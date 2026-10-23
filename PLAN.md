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

## Guided synthetic demonstration

16. **Demo/report foundation** — five explicitly fictional complex cases with
    source-bound test expectations, a narrowly scoped local demo-account setup,
    staged safety preparation before inference, persistent CT result summaries,
    and concise seven-section reporting. Test services before changing the UI.
    Status: passed — 71 existing service checks and 7 new staged/demo checks;
    exact-source presentation and compact wire-budget validation retained.
17. **Guided signed-in UI** — gate all patient examples behind login, keep CT
    findings visible in the CT panel, put clear safety controls and gated draft
    generation at the bottom, and retain explicit final approval. Status: passed —
    24 focused staged/UI/source-presentation checks, including persistent CT
    results, login expiry, patient switching and no model call on safety save.
18. **Verification and delivery** — full regression, actual local smokes/browser
    checks, updated concise guides/evaluation and revised local demo. Status: complete —
    187 local tests, actual local Ollama and fixture/pretrained browser runs,
    Python 3.10/3.12 hosted tests and all three CT receiver smokes passed.

## Focused patient workspace

19. **Navigation and isolation foundation** — patient-scoped cleanup, stale-result
    guards and fixed allowlisted action destinations. Test before UI integration.
    Status: passed — 11 navigation/isolation unit checks (0.24 seconds).
20. **Concise guided UI** — explicit single-patient selection, dedicated Safety
    check view, clickable steps/next action, readable sources and no raw technical
    panels. Keep generation gated and final approval intact. Status: passed —
    16 adapted UI checks and 16 new navigation/isolation checks; actual browser
    guide-to-safety jump shows the form and locked generation control.
21. **Verification and delivery** — regression, actual browser navigation and
    patient-isolation checks, concise guides/screenshots and revised local release.
    Status: complete — 206 local tests, actual local Ollama, fixture/pretrained
    CT and desktop/narrow browser navigation/isolation checks. Guides and four
    screenshots updated; final hosted Python 3.10/3.12 and all three CT compatibility
    flows passed. Published/local trees match; demo remains on loopback.

## Concise combined clinical and CT report

22. **Source-bound summary services** — one-section report, explicit accepted/no-CT
    status, structured evidence retained separately, authenticated previewable
    clinician note and content-bound approval/persistence. Test before UI changes.
    Status: passed — 76 summary, note-authentication, source, workflow and CT checks.
23. **Combined report interface and export** — concise summary with inspected CT
    images, readable optional evidence, note preview before approval and portable
    HTML export with local embedded images. Preserve safety and review gates.
    Status: passed — 13 portable-export, combined-report UI and existing review/CT UI checks.
24. **Validation and publication** — full regressions, actual local model/CT smokes,
    accurate concise guides/sample report and hosted compatibility checks; publish.
    Status: complete — 220 LOVISA / 81 CT tests, actual local Ollama/pretrained
    transfer, browser example/app checks and 31/25 document checks passed. Hosted
    Python 3.10/3.12 and fixture/pretrained/legacy compatibility checks passed.
    Implementation and aligned CT documentation are published; local trees match.

## Image-first endoscopy companion

25. **Endoscopy foundation** — standalone typed RGB candidate/source/review contracts,
    safe synthetic exchange, dataset validation and grouped frozen splits; test
    all contracts and data invariants before adding inference. Status: passed — 15 companion foundation tests.
26. **Endoscopy model and deployment** — compact U-Net, reproducible train/evaluate,
    ONNX CPU parity, optional explicit OpenVINO devices and local CLI/UI. Separate
    real training/evaluation from synthetic tests. Status: passed — 26 companion tests and actual artificial CPU training/export/parity.
27. **LOVISA endoscopy integration** — modality-specific validator, bounded local
    worker, candidate review UI, accepted evidence and report images. Preserve
    safety, frozen snapshots, authentication and CT compatibility. Status: passed — 227 full tests and actual fixture/installed-model exchange smokes.
28. **Joint verification and publication** — full regressions, local Ollama and
    producer-consumer smokes, automated UI checks, concise linked documentation and
    accurate evaluation records; publish both projects after passing. Status: complete — 231 LOVISA/35 endoscopy local tests; actual model/CT/endoscopy smokes, Linux/Windows and both Python hosted suites plus all joint imaging jobs passed. Both repositories published; local demo restarted.

## Real research images and clearer review controls

29. **Research evidence boundary** — explicitly permit de-identified public research
    imaging alongside fictional history, with dataset/license/source provenance,
    distinct research-subject identities, composite-case labels and bounded
    source mappings; preserve synthetic compatibility. Test before UI changes.
    Status: passed — seven adversarial/backwards-compatibility tests and 24 existing CT/endoscopy checks.
30. **Real-data experiments and upload examples** — obtain permitted CT and
    endoscopy sources, freeze subject-aware splits where identifiers exist, execute
    feasible local training/evaluation without inventing GPU results; implement
    upload preparation and a labelled composite case. The actual prepared-pair
    smoke belongs to phase 32. Status: passed — 82 CT / 36 endoscopy tests,
    real Kvasir 24-epoch CPU training/export and 168-image evaluation; real CT
    downloaded and offline inference running. Full CT GPU training unavailable.
31. **Concise review interface** — short imaging results, optional notes, checked
    confirmation defaults, larger yellow/green decision controls; explicit submit
    and unresolved-candidate/safety gates remain. Status: passed — 14 review/UI tests, optional-note/authentication checks and 27 combined-report/existing workflow checks.
32. **Combined report validation and delivery** — temporary scripted-review tests
    for the actual research-image pair, full regressions/smokes and honest outcomes,
    updated instructions/sample manifest and a refreshed local demo. Publish
    compatible changes after passing. Status: local validation passed — 243 LOVISA / 83 CT / 37 endoscopy tests; actual 11.98s CT ROI, 3.16s endoscopy and 34.32s combined local-LLM smoke. Publishing/hosted checks in progress; full CT training remains hardware-blocked.
