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
| 12 | LOVISA name, two-project documentation and reused figures | Local checks passed: 146 LOVISA / 81 CT tests, 25 Markdown files per repo, contract equality and actual local Ollama smoke; hosted publication pending |

Phases 1–11 are complete. Phase 12 preserves the safety policy, model/weights,
source schemas and exchange identifiers. The visible name and explanatory guides
change together. Unexecuted clinical/GPU work is not marked completed by these
software gates.
