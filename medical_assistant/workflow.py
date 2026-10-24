"""Clinical-review graph with deterministic safety holds and authenticated review."""

from datetime import datetime, timezone
from pathlib import Path
from typing import TypedDict
from uuid import uuid4

from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

from medical_assistant.agents import Inference, SpecialistAgent
from medical_assistant.auth import LocalAuth
from medical_assistant.database import get_history
from medical_assistant.evidence import LocalEvidenceCollection
from medical_assistant.grounding import validate_record_grounding
from medical_assistant.history import MedicalHistoryAgent, MedicationAgent
from medical_assistant.imaging import ImagingStore
from medical_assistant.models import PatientRecord, ReportNote, Review
from medical_assistant.persistence import resumable_cases, workflow_checkpointer
from medical_assistant.report import compose, digest, evidence_index
from medical_assistant.report_binding import content_digest, verify_content_binding
from medical_assistant.report_notes import verify_note
from medical_assistant.safety import SafetyAgent
from medical_assistant.storage import ROOT


class CaseState(TypedDict, total=False):
    case_id: str
    record: dict
    source_file: str
    model: str
    assessments: dict
    evidence: list[dict]
    safety_decision: dict
    final_safety_decision: dict
    safety_ack: dict
    safety_receipt: dict
    draft: str
    generated_draft: str
    status: str
    reviewed: bool
    review: dict
    approval_receipt: dict
    review_history: list[dict]
    reviewed_at: str
    final_report: str
    imaging: list[dict]
    report_evidence: dict
    clinician_note: dict
    note_receipt: dict
    report_content_receipt: dict


class MedicalHistoryOrchestrator:
    def __init__(
        self,
        inference: Inference,
        evidence_collection=None,
        *,
        auth=None,
        safety=None,
        checkpointer=None,
    ):
        self.inference = inference
        self.auth = auth or LocalAuth()
        self.imaging_store = ImagingStore(self.auth.path, self.auth)
        self.safety = safety or SafetyAgent()
        self.evidence_collection = evidence_collection or LocalEvidenceCollection(
            ROOT / "data" / "evidence"
        )
        builder = StateGraph(CaseState)
        builder.add_node("safety", self._initial_safety)
        builder.add_node("safety_human_review", self._safety_review)
        for role, extractor in (
            ("history", MedicalHistoryAgent()),
            ("medications", MedicationAgent()),
        ):

            def extract(state, role=role, extractor=extractor):
                result = extractor.run(PatientRecord.model_validate(state["record"]))
                return {
                    "assessments": {
                        **state["assessments"],
                        role: result.model_dump(mode="json"),
                    }
                }

            builder.add_node(role, extract)
        builder.add_node("evidence_retrieval", self._retrieve_evidence)
        builder.add_node("reasoning", self._reasoning)
        builder.add_node("safety_review", self._final_safety)
        builder.add_node("orchestrator", self._compose)
        builder.add_node("clinician_review", self._review)
        builder.add_node("complete_report", self._complete)
        builder.add_edge(START, "safety")
        builder.add_conditional_edges(
            "safety",
            lambda state: (
                "ordinary"
                if state["safety_decision"]["state"] == "ordinary_eligible"
                else "hold"
            ),
            {"ordinary": "history", "hold": "safety_human_review"},
        )
        builder.add_conditional_edges(
            "safety_human_review",
            lambda state: "continue" if state["status"] == "running" else "stop",
            {"continue": "history", "stop": END},
        )
        sequence = [
            "history",
            "medications",
            "evidence_retrieval",
            "reasoning",
            "safety_review",
            "orchestrator",
            "clinician_review",
        ]
        for left, right in zip(sequence, sequence[1:]):
            builder.add_edge(left, right)
        builder.add_conditional_edges(
            "clinician_review",
            lambda state: "complete" if state["status"] == "approved" else "review",
            {"complete": "complete_report", "review": "clinician_review"},
        )
        builder.add_edge("complete_report", END)
        self.graph = builder.compile(
            checkpointer=checkpointer
            or workflow_checkpointer(self.auth.path, self.auth.durable_receipts)
        )

    def resumable_cases(self, patient_id):
        """Pending saved reviews for this patient (durable receipt key only)."""
        return resumable_cases(self.graph.checkpointer, patient_id)

    def _initial_safety(self, state):
        decision = self.safety.evaluate(PatientRecord.model_validate(state["record"]))
        return {
            "safety_decision": decision,
            "assessments": {"safety": decision["assessment"]},
            "status": "running"
            if decision["state"] == "ordinary_eligible"
            else "awaiting_safety_review",
        }

    def _checked_review(self, state, response, action):
        review = Review.model_validate(response["review"])
        actor = self.auth.verify_receipt(
            response["receipt"],
            action + ":" + state["case_id"],
            digest(review.model_dump_json()),
        )
        if actor != review.reviewer:
            raise PermissionError("Authenticated account does not match the reviewer")
        return review

    def _safety_review(self, state):
        decision = state["safety_decision"]
        response = interrupt(
            {
                "type": "safety_human_review_required",
                "decision": decision,
                "message": "Uncertain cases require clinician assessment before reasoning. Urgent workflow holds cannot continue in this case.",
            }
        )
        review = self._checked_review(state, response, "safety-review")
        if review.draft_sha256 != decision["decision_sha256"]:
            raise ValueError("Stale safety assessment")
        if review.approved and decision["state"] == "urgent":
            raise ValueError(
                "An urgent workflow hold cannot be bypassed; stop and seek human assessment"
            )
        self.auth.record_receipt(
            response["receipt"], state["record"]["patient_id"], review.model_dump()
        )
        return {
            "safety_ack": review.model_dump(),
            "safety_receipt": response["receipt"],
            "status": "running" if review.approved else "stopped_for_human_review",
        }

    def _retrieve_evidence(self, state):
        record = PatientRecord.model_validate(state["record"])
        query = " ".join(
            entry.text
            for entry in record.entries
            if entry.kind in ("symptom", "diagnosis")
        )
        return {"evidence": self.evidence_collection.retrieve(query)}

    def _reasoning(self, state):
        self._verify_safety_ack(state)
        result = SpecialistAgent("reasoning", self.inference).run(
            PatientRecord.model_validate(state["record"]),
            state["assessments"],
            state["evidence"],
        )
        return {"assessments": {**state["assessments"], "reasoning": result}}

    def _verify_safety_ack(self, state):
        current = self.safety.evaluate(PatientRecord.model_validate(state["record"]))
        if current["decision_sha256"] != state["safety_decision"]["decision_sha256"]:
            raise ValueError(
                "Safety policy, date or records changed: restart clinical review"
            )
        if current["state"] == "urgent":
            raise ValueError(
                "Urgent safety hold blocks clinical reasoning and completion"
            )
        if current["state"] == "uncertain":
            review = Review.model_validate(state.get("safety_ack", {}))
            self.auth.verify_receipt(
                state.get("safety_receipt"),
                "safety-review:" + state["case_id"],
                digest(review.model_dump_json()),
            )
            if not review.approved or review.draft_sha256 != current["decision_sha256"]:
                raise ValueError(
                    "Uncertain safety state requires a matching clinician decision"
                )
        return current

    def _final_safety(self, state):
        return {"final_safety_decision": self._verify_safety_ack(state)}

    def _verify_imaging(self, state):
        snapshots = state.get("imaging", [])
        if any(
            s["manifest"]["patient_id"] != state["record"]["patient_id"]
            for s in snapshots
        ):
            raise ValueError("Imaging snapshot patient mismatch")
        self.imaging_store.verify(snapshots)

    def _compose(self, state):
        self._verify_imaging(state)
        draft = compose(
            PatientRecord.model_validate(state["record"]),
            state["source_file"],
            state["assessments"],
            state["evidence"],
            state.get("imaging", []),
        )
        return {
            "draft": draft,
            "generated_draft": draft,
            "report_evidence": evidence_index(
                PatientRecord.model_validate(state["record"]),
                state["assessments"],
                state.get("imaging", []),
            ),
            "status": "awaiting_clinician_review",
        }

    def _verify_report(self, state):
        verify_note(state, self.auth)
        record = validate_record_grounding(
            PatientRecord.model_validate(state["record"])
        )
        expected = compose(
            record,
            state["source_file"],
            state["assessments"],
            state["evidence"],
            state.get("imaging", []),
            state.get("clinician_note"),
        )
        if state["draft"] != expected or state["generated_draft"] != expected:
            raise ValueError(
                "Clinical report no longer matches its grounded source snapshot"
            )
        if state.get("report_evidence") != evidence_index(
            record, state["assessments"], state.get("imaging", [])
        ):
            raise ValueError("Clinical report evidence links changed")

    def _review(self, state):
        self._verify_report(state)
        response = interrupt(
            {
                "type": "clinician_review_required",
                "draft": state["draft"],
                "draft_sha256": digest(state["draft"]),
                "message": "Authenticated clinician approval is required.",
            }
        )
        review = self._checked_review(state, response, "clinical-review")
        verify_content_binding(
            state, response.get("content_receipt"), self.auth, review.reviewer
        )
        if review.draft_sha256 != digest(state["draft"]):
            raise ValueError("Review does not match the current report")
        self.auth.record_receipt(
            response["receipt"], state["record"]["patient_id"], review.model_dump()
        )
        return {
            "review": review.model_dump(),
            "approval_receipt": response["receipt"],
            "report_content_receipt": response["content_receipt"],
            "review_history": [
                *state.get("review_history", []),
                {
                    **review.model_dump(),
                    "reviewed_draft": state["draft"],
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            ],
            "status": "approved" if review.approved else "awaiting_clinician_review",
        }

    def _complete(self, state):
        self._verify_safety_ack(state)
        self._verify_imaging(state)
        self._verify_report(state)
        review = Review.model_validate(state["review"])
        verify_content_binding(
            state, state.get("report_content_receipt"), self.auth, review.reviewer
        )
        self.auth.verify_receipt(
            state["approval_receipt"],
            "clinical-review:" + state["case_id"],
            digest(review.model_dump_json()),
        )
        if not review.approved or review.draft_sha256 != digest(state["draft"]):
            raise ValueError("A matching authenticated clinician approval is required")
        return {
            "status": "complete",
            "reviewed": True,
            "final_report": state["draft"],
            "reviewed_at": datetime.now(timezone.utc).isoformat(),
        }

    @staticmethod
    def config(case_id):
        return {"configurable": {"thread_id": case_id}}

    def start(
        self,
        record: PatientRecord,
        source_file: str,
        *,
        imaging=None,
        safety_only=False,
    ):
        validate_record_grounding(record)
        case_id = uuid4().hex
        return case_id, self.graph.stream(
            {
                "case_id": case_id,
                "record": record.model_dump(mode="json"),
                "source_file": source_file,
                "model": self.inference.model,
                "assessments": {},
                "review_history": [],
                "status": "running",
                "reviewed": False,
                "imaging": imaging or [],
            },
            self.config(case_id),
            stream_mode="updates",
            interrupt_before=["history"] if safety_only else None,
        )

    def start_patient(self, patient_id, path, *, safety_only=False):
        if Path(path).resolve() != self.auth.path.resolve():
            raise ValueError("Case database must match the authenticated local service")
        record = get_history(patient_id, path)
        # Never delay an urgent safety hold for optional image artifact inspection.
        imaging = (
            []
            if self.safety.evaluate(record)["state"] == "urgent"
            else self.imaging_store.snapshots(patient_id)
        )
        return self.start(
            record,
            "SQLite original-source snapshot",
            imaging=imaging,
            safety_only=safety_only,
        )

    def state(self, case_id):
        return self.graph.get_state(self.config(case_id)).values

    def _response(self, case_id, review, token, action):
        review = Review.model_validate(review.model_dump())
        actor = self.auth.require(token)
        if review.reviewer != actor:
            raise PermissionError(
                "Reviewer identity must match authenticated clinician account"
            )
        response = {
            "review": review.model_dump(),
            "receipt": self.auth.receipt(
                token, action + ":" + case_id, digest(review.model_dump_json())
            ),
        }

        if action == "clinical-review":
            response["content_receipt"] = self.auth.receipt(
                token,
                "clinical-content:" + case_id,
                content_digest(self.state(case_id)),
            )
        return response

    def acknowledge_safety(
        self, case_id, review: Review, token=None, *, safety_only=False
    ):
        state = self.state(case_id)
        if state.get("status") != "awaiting_safety_review":
            raise ValueError("No safety review is pending")
        response = self._response(case_id, review, token, "safety-review")
        if review.draft_sha256 != state["safety_decision"]["decision_sha256"]:
            raise ValueError("Stale safety decision")
        if review.approved and state["safety_decision"]["state"] == "urgent":
            raise ValueError("Urgent cases cannot continue through automated reasoning")
        return self.graph.invoke(
            Command(resume=response),
            self.config(case_id),
            interrupt_before=["history"] if safety_only else None,
        )

    def ready_for_analysis(self, case_id, token=None):
        """Authenticate and recheck the exact prepared snapshot before generation."""
        self.auth.require(token)
        snapshot = self.graph.get_state(self.config(case_id))
        state = snapshot.values
        if state.get("status") != "running" or tuple(snapshot.next) != ("history",):
            raise ValueError(
                "Complete required safety checks before generating a draft"
            )
        self._verify_safety_ack(state)
        self._verify_imaging(state)
        return True

    def continue_analysis(self, case_id, token=None):
        self.ready_for_analysis(case_id, token)
        return self.graph.invoke(None, self.config(case_id))

    def revise(self, case_id, draft: str, token=None):
        self.auth.require(token)
        state = self.state(case_id)
        if state.get("status") != "awaiting_clinician_review" or not draft.strip():
            raise ValueError("Only a non-empty pending draft can be revised")
        if draft != state["generated_draft"]:
            raise ValueError(
                "Clinical report text is source-bound. Record corrections require an approved source import and a new case; use review notes for feedback."
            )
        self.auth.audit(
            "clinician-correction:" + case_id,
            state["record"]["patient_id"],
            token,
            {
                "before": state["draft"],
                "after": draft,
                "previous_sha256": digest(state["draft"]),
                "new_sha256": digest(draft),
            },
        )
        self.graph.update_state(
            self.config(case_id),
            {
                "draft": draft,
                "review": {},
                "approval_receipt": {},
                "report_content_receipt": {},
            },
            as_node="orchestrator",
        )

    def prepare_report_note(self, case_id, text, token=None):
        """Preview a signed reviewer comment; any changed report requires fresh approval."""
        actor = self.auth.require(token)
        state = self.state(case_id)
        if state.get("status") != "awaiting_clinician_review":
            raise ValueError("A report note can only be changed on a pending draft")
        self._verify_safety_ack(state)
        self._verify_imaging(state)
        self._verify_report(state)
        note = ReportNote(reviewer=actor, text=text)
        receipt = self.auth.receipt(
            token, "report-note:" + case_id, digest(note.model_dump_json())
        )
        draft = compose(
            PatientRecord.model_validate(state["record"]),
            state["source_file"],
            state["assessments"],
            state["evidence"],
            state.get("imaging", []),
            note.model_dump(),
        )
        self.auth.record_receipt(
            receipt, state["record"]["patient_id"], note.model_dump()
        )
        self.graph.update_state(
            self.config(case_id),
            {
                "draft": draft,
                "generated_draft": draft,
                "clinician_note": note.model_dump(),
                "note_receipt": receipt,
                "review": {},
                "approval_receipt": {},
                "report_content_receipt": {},
                "reviewed": False,
            },
            as_node="orchestrator",
        )
        return self.state(case_id)

    def review(self, case_id, review: Review, token=None):
        state = self.state(case_id)
        if state.get("status") != "awaiting_clinician_review":
            raise ValueError("No report is awaiting clinician review")
        self._verify_report(state)
        response = self._response(case_id, review, token, "clinical-review")
        if review.draft_sha256 != digest(state["draft"]):
            raise ValueError("Stale review: inspect the current draft before approving")
        return self.graph.invoke(Command(resume=response), self.config(case_id))

    def export(self, case_id):
        snapshot = self.graph.get_state(self.config(case_id))
        state = snapshot.values
        if (
            state.get("status") != "complete"
            or not state.get("reviewed")
            or snapshot.next
        ):
            raise ValueError("Report is not complete: clinician approval is required")
        self._verify_safety_ack(state)
        self._verify_imaging(state)
        self._verify_report(state)
        review = Review.model_validate(state["review"])
        verify_content_binding(
            state, state.get("report_content_receipt"), self.auth, review.reviewer
        )
        self.auth.verify_receipt(
            state["approval_receipt"],
            "clinical-review:" + case_id,
            digest(review.model_dump_json()),
        )
        if not review.approved or review.draft_sha256 != digest(state["final_report"]):
            raise ValueError("Report approval failed verification")
        return {**state, "educational_only": True}
