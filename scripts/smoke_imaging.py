"""Real local CT worker and receiver; no human or final approval is simulated."""

import argparse
import json
import sys
import time
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from medical_assistant.ct_worker import LocalCTJob, configured_ct_root
from medical_assistant.database import seed
from medical_assistant.imaging import ImagingStore


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ct-root", type=Path, default=configured_ct_root())
    parser.add_argument(
        "--mode",
        choices=["legacy", "lung-fixture", "lung-pretrained"],
        default="lung-fixture",
    )
    parser.add_argument("--model-dir", type=Path)
    parser.add_argument("--device", choices=["cpu", "cuda"], default="cpu")
    args = parser.parse_args()
    with TemporaryDirectory(prefix="mhcra-imaging-smoke-") as tmp:
        root = Path(tmp)
        path = root / "synthetic.sqlite3"
        seed(path)
        job = LocalCTJob(
            "synthetic-checklist",
            root=args.ct_root,
            jobs=root / "jobs",
            mode=args.mode,
            model_dir=args.model_dir,
            device=args.device,
        )
        print("Running real generated-synthetic CT worker locally…", flush=True)
        try:
            while job.status() == "running":
                time.sleep(0.2)
            if job.status() != "complete":
                raise RuntimeError(job.error + "\n" + job.log_path.read_text()[-4000:])
            store = ImagingStore(path)
            key, proposal = store.prepare(
                job.bundle_path.read_bytes(), job.patient_id, study_id=job.study_id
            )
            assert not store.snapshots(job.patient_id)
            manifest = proposal["manifest"]
            summary = {
                "status": "PASS",
                "mode": args.mode,
                "schema": manifest["schema_version"],
                "artifacts": len(manifest["artifacts"]),
                "imaging_approved": False,
                "final_report_approved": False,
            }
            if args.mode == "legacy":
                summary.update(
                    source_shape_zyx=manifest["geometry"]["shape_zyx"],
                    voxel_counts=manifest["voxel_counts"],
                    producer_reports_onnx_parity=manifest["onnx_parity_passed"],
                )
            else:
                assert (
                    manifest["status"] == "pending_review"
                    and manifest["producer_review"] is None
                )
                summary.update(
                    source_shape_zyx=manifest["study"]["geometry"]["shape_zyx"],
                    candidates=len(manifest["study"]["candidates"]),
                    synthetic_fixture=manifest["study"]["model"]["synthetic_fixture"],
                )
            print(json.dumps(summary), flush=True)
            store.discard(key)
        finally:
            job.cancel()


if __name__ == "__main__":
    main()
