"""Actual local image-pair/report smoke with SCRIPTED reviews in a TEMPORARY DB.

The approvals below test plumbing only. They are never clinical review and never
modify the demo application's database. No image pixels are sent to the LLM.
"""

import argparse
import json
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from medical_assistant.auth import LocalAuth
from medical_assistant.database import seed
from medical_assistant.endo_contracts import Review as EndoReview
from medical_assistant.endo_contracts import digest as endo_digest
from medical_assistant.imaging import ImagingStore
from medical_assistant.models import Review
from medical_assistant.nodule_models import Review as CTReview
from medical_assistant.nodule_models import digest as ct_digest
from medical_assistant.nodule_support import imaging_acceptance_digest
from medical_assistant.ollama_client import OllamaClient
from medical_assistant.report import digest
from medical_assistant.report_assets import portable_html
from medical_assistant.research_examples import PATIENT, example_bundle
from medical_assistant.workflow import MedicalHistoryOrchestrator


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--kit",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "data/research-demo",
    )
    p.add_argument("--model", default="gemma4:e2b")
    p.add_argument("--output", type=Path)
    a = p.parse_args()
    started = time.monotonic()
    client = OllamaClient(a.model)
    client._deadline = time.monotonic() + 100
    try:
        with tempfile.TemporaryDirectory(
            prefix="lovisa-scripted-research-test-"
        ) as temp:
            path = Path(temp) / "test.sqlite3"
            seed(path)
            auth = LocalAuth(path)
            auth.create_clinician(
                "scripted.reviewer", "isolated-integration-test-password"
            )
            token = auth.login(
                "scripted.reviewer", "isolated-integration-test-password"
            )
            store = ImagingStore(path, auth)
            for modality in ("ct", "endoscopy"):
                key, proposal = store.prepare(
                    example_bundle(modality, PATIENT, root=a.kit), PATIENT
                )
                study = proposal["manifest"]["study"]
                decisions = [
                    dict(candidate_id=c["candidate_id"], decision="accept")
                    for c in study["candidates"]
                ]
                if modality == "ct":
                    image_review = CTReview(
                        study_digest=ct_digest(study),
                        reviewer="scripted.reviewer",
                        qualified_reviewer_attestation=True,
                        approved=True,
                        decisions=decisions,
                    )
                    kwargs = dict(nodule_review=image_review)
                else:
                    image_review = EndoReview(
                        study_digest=endo_digest(study),
                        reviewer="scripted.reviewer",
                        attested=True,
                        decisions=decisions,
                    )
                    kwargs = dict(endo_review=image_review)
                receipt = Review(
                    approved=True,
                    reviewer="scripted.reviewer",
                    clinician_attestation=True,
                    notes="Scripted integration test only; not a human image review.",
                    draft_sha256=imaging_acceptance_digest(proposal, **kwargs),
                )
                store.approve(key, receipt, token, **kwargs)
            flow = MedicalHistoryOrchestrator(client, auth=auth)
            case, events = flow.start_patient(PATIENT, path)
            list(events)
            state = flow.state(case)
            assert state["status"] == "awaiting_safety_review" and not state["reviewed"]
            review = Review(
                approved=True,
                reviewer="scripted.reviewer",
                clinician_attestation=True,
                notes="Scripted safety-gate test, not clinical assessment.",
                draft_sha256=state["safety_decision"]["decision_sha256"],
            )
            flow.acknowledge_safety(case, review, token)
            state = flow.state(case)
            assert (
                state["status"] == "awaiting_clinician_review" and not state["reviewed"]
            )
            assert (
                len(state["imaging"]) == 2
                and "CT inspection" in state["draft"]
                and "Endoscopy inspection" in state["draft"]
            )
            assert "image subjects are unrelated" in state["draft"]
            try:
                flow.export(case)
            except ValueError:
                pass
            else:
                raise AssertionError("Unapproved report exported")
            state = flow.prepare_report_note(
                case,
                "AUTOMATED INTEGRATION TEST ONLY — no clinician reviewed these images or conclusions.",
                token,
            )
            flow.review(
                case,
                Review(
                    approved=True,
                    reviewer="scripted.reviewer",
                    clinician_attestation=True,
                    notes="Scripted final-approval plumbing test only.",
                    draft_sha256=digest(state["draft"]),
                ),
                token,
            )
            result = flow.export(case)
            page = portable_html(result, auth=auth, safety=flow.safety)
            assert page.count('src="data:image/png;base64,') == 4
            if a.output:
                a.output.mkdir(parents=True, exist_ok=False)
                (a.output / "scripted-integration-report.html").write_text(page)
                (a.output / "scripted-integration-report.md").write_text(
                    result["final_report"]
                )
            print(
                json.dumps(
                    dict(
                        outcome="PASS",
                        actual_local_model=a.model,
                        actual_research_images=2,
                        embedded_images=4,
                        elapsed_seconds=round(time.monotonic() - started, 2),
                        report_words=len(result["final_report"].split()),
                        approvals="SCRIPTED TEST ONLY in disposable database; not clinician approval",
                    ),
                    indent=2,
                )
            )
    finally:
        client.close()


if __name__ == "__main__":
    main()
