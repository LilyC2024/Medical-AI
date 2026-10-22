# Implementation plan

The user authorized all eight checklist items after Phase 1 passes. Each phase
must pass its tests before work begins on the next.

1. **Foundation, model connection and synthetic records** — inspect environment;
   typed source/fact schemas, SQLite creation/retrieval, idempotent synthetic seed,
   data-validation tests and exact local commands. Status: passed (20 foundation
   tests; live local structured Ollama connection passed).
2. **Medical history management** — source-grounded history/dose extraction,
   known/missing dates, consistency checks and human-approved transactional imports.
   Status: passed (24 cumulative foundation/history tests).
3. **Agent orchestration and clinical reasoning** — shared validated records,
   local approved evidence only, hypotheses, source grounding and missing data.
   Status: passed (48 full regression tests).
4. **Safety and human approval** — external deterministic policy, initial/final
   screening, mandatory escalation interrupts, clinician approval and audit records.
   Status: passed (76 non-UI regression and adversarial tests).
5. **Streamlit interface and automated evaluation** — SQLite selection/import,
   symptoms, timeline, medications, evidence, safety controls and checklist tests.
   Status: passed (87 full regression/UI/adversarial tests; real local smoke passed; see EVALUATION.md).
