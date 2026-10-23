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

## Shared CT workbench extension

6. **CT exchange contract** — add a synthetic-only, hash-bound review bundle,
   explicit identity/unknown dates, source-grid previews and measurements; test
   CT export and invalid-artifact behavior before MHCRA implementation.
   Status: passed (32 CT tests including 2 new bridge tests; CT lint passed;
   unchanged MHCRA baseline: 87 tests passed).
7. **MHCRA imaging workbench** — isolated local CT jobs, verified bundle inspection,
   source/overlay viewer, authenticated imaging acceptance and source-linked report
   appendix. Preserve existing safety and final approval gates. Test before phase 8.
   Status: passed (116 full MHCRA tests, including 29 imaging/worker/UI checks;
   CT suite rerun: 32 tests; real exported synthetic bundle validated by MHCRA).
8. **Cross-project demonstration and publication** — run both suites, real synthetic
   CT processing and local Ollama smoke; document actual results, illustrate the
   integration, review publication contents and push both repositories.
   Implementation/local validation passed: 120 MHCRA tests, 32 CT tests, real CT
   worker/receiver smoke and separate real local Ollama smoke. The coordinated
   release pins its CT producer in hosted integration CI; see EVALUATION.md.

## Current lung CT compatibility

9. **Versioned nodule exchange** — shared lightweight contracts/rendering, bounded
   source HU and every-slice previews, explicit pending/reviewed status, synthetic
   patient/study binding and no automatic approval. Test CT producer before receiver.
   Status: passed (26 CT producer/review tests; pending and reviewed exports,
   source-grid/caliper checks and 11 adversarial archive mutations).
10. **MHCRA nodule consumer and worker** — independent bounded validation, typed
    candidate/caliper review, authenticated imaging acceptance, immutable storage,
    source-linked appendix and offline fixture/pretrained jobs. Preserve safety,
    final clinician gate and old tissue-mask compatibility. Status: passed (144 full
    MHCRA regression tests; CT full suite 81 tests; legacy and new UI paths).
11. **Joint verification and documentation** — both suites, actual cross-project
    fixture/pretrained smoke and Ollama smoke; current producer CI pin; concise
    MHCRA overview with detailed linked guides and function/folder reference;
    update CT compatibility docs and publish both tested trees. Local verification
    passed: 146 MHCRA tests, 81 CT tests; real fixture/pretrained/legacy CT smoke
    and live gemma4:e2b smoke passed. Both matching updates published; hosted MHCRA Python 3.10/3.12 and all three
    producer-consumer smokes passed. CT Windows/Linux, Docker and pretrained
    checks passed. Phase complete; exact commits/runs in EVALUATION.md.
