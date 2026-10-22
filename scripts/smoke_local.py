"""Real local model smoke: verify an uncertainty hold and a separate fully synthetic
ordinary-eligible fixture. Never approve a safety hold or final clinical report.
"""
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from medical_assistant.auth import LocalAuth
from medical_assistant.database import attach_original, get_history, seed
from medical_assistant.models import PatientRecord
from medical_assistant.ollama_client import OllamaClient
from medical_assistant.workflow import MedicalHistoryOrchestrator


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="gemma4:e2b")
    args = parser.parse_args()
    client = OllamaClient(args.model)
    try:
        with TemporaryDirectory(prefix="mhcra-smoke-") as directory:
            path = Path(directory) / "synthetic.sqlite3"
            seed(path)
            auth = LocalAuth(path)
            workflow = MedicalHistoryOrchestrator(client, auth=auth)
            case_id, events = workflow.start_patient("synthetic-checklist", path)
            list(events)
            assert workflow.state(case_id)["status"] == "awaiting_safety_review"
            assert not workflow.state(case_id)["reviewed"]
            print("PASS: missing-data fixture pauses before model reasoning; no safety approval issued.", flush=True)

            # Explicit synthetic test observations, not invented real-world findings.
            day = datetime.now(ZoneInfo("Europe/Amsterdam")).date().isoformat()
            data = {"fictional": True, "patient_id": "synthetic-live-smoke", "display_name": "Synthetic local model test only", "entries": [
                {"id": "screen", "date": day, "source_type": "documented", "kind": "encounter",
                 "text": "Synthetic test observation only; structured fields are explicitly supplied for workflow evaluation.",
                 "warning_screen": "absent", "blood_pressure": {"systolic": 125, "diastolic": 80}},
                {"id": "symptom", "date": None, "source_type": "patient_reported", "kind": "symptom",
                 "text": "Synthetic subject reports intermittent tiredness and irregular sleep during shift work. Symptom onset is not supplied."},
            ]}
            raw = json.dumps(data)
            record = attach_original(PatientRecord.model_validate(data), "synthetic-live-smoke.json", raw)
            case_id, events = workflow.start(record, "synthetic-live-smoke.json")
            for event in events:
                print("Completed:", ", ".join(event), flush=True)
            state = workflow.state(case_id)
            assert state["status"] == "awaiting_clinician_review" and state["reviewed"] is False
            assert "final_report" not in state
            assert set(state["assessments"]) == {"safety", "history", "medications", "reasoning"}
            print("PASS: deterministic history/medication/safety agents + real local LLM reasoning; final report approval still required.", flush=True)
    finally:
        client.close()


if __name__ == "__main__":
    main()
