# LOVISA implementation phases

Complete and test each phase before starting the next. Historical counts refer to
the suite at that gate, not the current total. [Actual evidence](EVALUATION.md).

| Phase | Deliverable | Completed evidence |
| --- | --- | --- |
| 1 | Foundation, synthetic schemas/SQLite and local model | 20 tests; actual local structured response |
| 2 | Grounded history/orders and approved source import | 24 cumulative tests |
| 3 | Sequential specialist graph and bounded hypotheses | 48 full tests |
| 4 | Deterministic safety, authenticated pauses and final approval | 76 non-UI tests |
| 5 | Streamlit and eight acceptance requirements | 87 full tests; actual local smoke |
| 6 | Synthetic legacy CT exchange producer | 32 CT tests; unchanged 87-test LOVISA baseline |
| 7 | Legacy viewer, acceptance and report appendix | 116 LOVISA tests; source/geometry validation |
| 8 | Joint demonstration and publication | 120 LOVISA / 32 CT tests; actual CT/Ollama smokes |
| 9 | Shared typed nodule-v2 producer/HU/previews | 26 producer/review tests and adversarial archive checks |
| 10 | Nodule consumer, candidates/calipers, authenticated acceptance | 144 LOVISA / 81 CT tests |
| 11 | Joint nodule verification/docs/publication | 146 LOVISA / 81 CT tests; all actual smokes and hosted checks |
| 12 | LOVISA name, two-project documentation and reused figures | Complete: 146 LOVISA / 81 CT tests, 25 Markdown files per repo, local Ollama and contract checks; both published updates passed all hosted jobs |

Phases 1–12 are complete. Phase 12 preserves the safety policy, model/weights,
source schemas and exchange identifiers. The visible name and explanatory guides
change together. Unexecuted clinical/GPU work is not marked completed by these
software gates.

## Workspace redesign and response budget

13. **Performance foundation** — bounded background jobs with real progress,
    cancellation and no late-result publication; two-minute maximum response
    budget, local Ollama request limits, CT watchdog and verified-view image access.
    Test timeouts/cancellation/late results and preserve all integrity gates before
    starting the UI phase. Status: passed (163 full LOVISA tests; 86 focused
    performance/integrity checks and 15 CT producer checks).
14. **Reusable workspace UI** — local design tokens/components, readable history
    and medication cards, focused CT/report actions, right-side operating guide,
    advanced source details and responsive layout. Preserve source escaping,
    authentication and explicit safety/import/imaging/final review. Status: passed
    (166 full tests; readable views, guide, cancellation and async responsiveness).
15. **Demo and publication** — full regression, actual local CT/Ollama timings,
    live browser checks/screenshots, updated guides/evaluation and publication.
    Remain on localhost as requested. Status: complete — 176 LOVISA / 81 CT tests,
    actual local model/three CT smokes, browser desktop/narrow checks and all
    hosted Python/CT/Windows/Linux/container checks passed.
