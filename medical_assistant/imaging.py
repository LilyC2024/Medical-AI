"""Human-reviewed synthetic imaging storage, separate from clinical source facts."""

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from medical_assistant.database import connect, get_history
from medical_assistant.imaging_contract import file_digest, validate_bundle
from medical_assistant.models import Review
from medical_assistant.report import digest
from medical_assistant.nodule_support import (
    is_nodule,
    checked_nodule_review,
    imaging_acceptance_digest,
    verify_nodule_snapshot,
)


class ImagingStore:
    def __init__(self, path, auth=None):
        self.path, self.auth = Path(path), auth
        self.root = self.path.parent / "imaging"
        self.pending = {}
        with connect(self.path) as db:
            db.execute("""CREATE TABLE IF NOT EXISTS imaging_studies (
                patient_id TEXT NOT NULL REFERENCES patients(id), study_id TEXT NOT NULL,
                snapshot TEXT NOT NULL, PRIMARY KEY(patient_id,study_id))""")

    def prepare(self, payload, patient_id, *, study_id=None):
        get_history(patient_id, self.path)
        bundle, raw, artifacts = validate_bundle(payload, patient_id)
        if study_id is not None and bundle.study_id != study_id:
            raise ValueError("Completed CT bundle does not match its requested study")
        key = uuid4().hex
        proposal = {
            "manifest": bundle.model_dump(mode="json"),
            "manifest_sha256": file_digest(raw),
            "archive_sha256": file_digest(payload),
        }
        proposal["sha256"] = digest(json.dumps(proposal, sort_keys=True))
        directory = self.root / "pending" / key
        directory.mkdir(parents=True)
        try:
            (directory / "bundle.json").write_bytes(raw)
            (directory / "source.mhcra.zip").write_bytes(payload)
            for name, data in artifacts.items():
                target = directory / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
        except Exception:
            shutil.rmtree(directory)
            raise
        self.pending[key] = json.dumps(proposal)
        return key, proposal

    def discard(self, key):
        self.pending.pop(key, None)
        shutil.rmtree(self.root / "pending" / key, ignore_errors=True)

    def _directory(self, patient_id, study_id):
        return self.root / "accepted" / patient_id / study_id

    @staticmethod
    def _verify_directory(directory, snapshot):
        archive = directory / "source.mhcra.zip"
        if archive.is_symlink() or directory.is_symlink():
            raise ValueError("Imaging artifacts cannot be symlinks")
        payload = archive.read_bytes()
        if file_digest(payload) != snapshot["archive_sha256"]:
            raise ValueError("Original imaging archive changed")
        bundle, raw, artifacts = validate_bundle(
            payload, snapshot["manifest"]["patient_id"]
        )
        if (
            bundle.model_dump(mode="json") != snapshot["manifest"]
            or file_digest(raw) != snapshot["manifest_sha256"]
        ):
            raise ValueError("Imaging manifest changed")
        for name, data in {"bundle.json": raw, **artifacts}.items():
            path = directory / name
            if path.is_symlink() or path.read_bytes() != data:
                raise ValueError("Extracted imaging artifact changed")

    def approve(self, key, review, token=None, *, nodule_review=None):
        review = Review.model_validate(review.model_dump())
        if self.auth is None or self.auth.require(token) != review.reviewer:
            raise PermissionError("Authenticated imaging reviewer required")
        proposal = json.loads(self.pending[key])
        candidate_review = (
            checked_nodule_review(
                proposal["manifest"], nodule_review, reviewer=review.reviewer
            )
            if is_nodule(proposal["manifest"])
            else None
        )
        expected_digest = imaging_acceptance_digest(
            proposal,
            candidate_review if candidate_review is not None else nodule_review,
        )
        if not review.approved or review.draft_sha256 != expected_digest:
            raise ValueError("Matching explicit imaging acceptance required")
        directory = self.root / "pending" / key
        self._verify_directory(directory, proposal)
        patient, study = (
            proposal["manifest"]["patient_id"],
            proposal["manifest"]["study_id"],
        )
        receipt = self.auth.receipt(token, "imaging-import:" + key, expected_digest)
        snapshot = {
            **proposal,
            "review": review.model_dump(mode="json"),
            "accepted_at": datetime.now(timezone.utc).isoformat(),
        }
        if candidate_review is not None:
            snapshot["nodule_review"] = candidate_review.model_dump(mode="json")
        target = self._directory(patient, study)
        target.parent.mkdir(parents=True, exist_ok=True)
        moved = False
        try:
            with connect(self.path) as db:
                if db.execute(
                    "SELECT 1 FROM imaging_studies WHERE patient_id=? AND study_id=?",
                    (patient, study),
                ).fetchone():
                    raise ValueError(
                        "Study ID already exists; accepted imaging is immutable"
                    )
                if target.exists():
                    # Recover the same bundle after a process crash between file
                    # promotion and DB commit; conflicting bytes still fail closed.
                    self._verify_directory(target, proposal)
                else:
                    directory.rename(target)
                    moved = True
                db.execute(
                    "INSERT INTO imaging_studies VALUES (?,?,?)",
                    (patient, study, json.dumps(snapshot)),
                )
                db.execute(
                    "INSERT INTO audit(action,patient_id,actor,payload) VALUES (?,?,?,?)",
                    (
                        "imaging-import:" + key,
                        patient,
                        review.reviewer,
                        json.dumps(
                            {
                                "receipt": receipt,
                                "decision": review.model_dump(mode="json"),
                                "manifest_sha256": proposal["manifest_sha256"],
                            }
                        ),
                    ),
                )
        except Exception:
            if moved:
                target.rename(directory)
            raise
        self.pending.pop(key)
        if directory.exists():
            shutil.rmtree(directory)
        return snapshot

    def snapshots(self, patient_id):
        with connect(self.path) as db:
            rows = db.execute(
                "SELECT snapshot FROM imaging_studies WHERE patient_id=? ORDER BY study_id",
                (patient_id,),
            ).fetchall()
        items = [json.loads(row[0]) for row in rows]
        self.verify(items)
        return items

    def verify(self, snapshots):
        for item in snapshots:
            patient, study = (
                item["manifest"]["patient_id"],
                item["manifest"]["study_id"],
            )
            with connect(self.path) as db:
                row = db.execute(
                    "SELECT snapshot FROM imaging_studies WHERE patient_id=? AND study_id=?",
                    (patient, study),
                ).fetchone()
            if not row or json.loads(row[0]) != item:
                raise ValueError("Imaging snapshot is not the accepted immutable study")
            verify_nodule_snapshot(item)
            self._verify_directory(self._directory(patient, study), item)

    def preview_path(self, snapshot, role, index):
        self.verify([snapshot])
        manifest = snapshot["manifest"]
        artifact = next(
            a
            for a in manifest["artifacts"]
            if a["role"] == role and a["slice_index"] == index
        )
        return (
            self._directory(manifest["patient_id"], manifest["study_id"])
            / artifact["path"]
        )

    def preview_resolver(self, snapshot):
        """Verify the archive once per view, then hash only requested artifacts.

        Acceptance, composition, completion, export and saving still perform full
        independent validation. Nothing is globally cached or shared across patients.
        """
        self.verify([snapshot])
        directory = self._directory(
            snapshot["manifest"]["patient_id"], snapshot["manifest"]["study_id"]
        )
        lookup = {
            (a["role"], a["slice_index"]): a for a in snapshot["manifest"]["artifacts"]
        }

        def resolve(role, index):
            item = lookup[(role, index)]
            path = directory / item["path"]
            if path.is_symlink() or file_digest(path.read_bytes()) != item["sha256"]:
                raise ValueError("Displayed imaging artifact changed")
            return path

        return resolve
