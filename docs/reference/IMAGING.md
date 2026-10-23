# Imaging service contracts

[Reference index](../CODE_REFERENCE.md) · [All signatures](CALLABLES.md) · [Integration](../IMAGING.md)

| API / helper | Input → result and invariant |
| --- | --- |
| configured_ct_root / configured_ct_model | Existing MHCRA_CT_* settings or sibling defaults → resolved local paths |
| LocalCTJob.__init__ | Synthetic patient, mode, device and paths → separate no-shell CT subprocess with unique study/output |
| LocalCTJob._watch / cancel / status | Process/watchdog → bounded state and process-group termination; no auto approval |
| validate_bundle | Bounded ZIP and patient → separately validated nodule-v2 or legacy tissue-v1; old incomplete nodule-v1 rejected |
| ExchangeArtifact.safe_path | Artifact name → safe relative nonreserved path |
| NoduleBundle.consistent | Typed manifest → exact identity, synthetic status, producer-review consistency and artifact roles |
| unique_object / byte_digest | JSON pairs or bytes → duplicate-key rejection / SHA-256 identity |
| source_pixels | NPY bytes + geometry → finite bounded float32 HU after header/length checks |
| wire_pixels | HU, candidates and optional calipers → exact source/overlay RGB arrays without font dependencies |
| read_exchange | Nodule ZIP → validated bundle, original manifest and artifacts; verify all pixels/report text |
| ImagingStore.prepare | Valid bundle → pending original ZIP/artifacts and hash-bound proposal; no accepted study |
| ImagingStore.approve | Proposal, authenticated Review and typed nodule choices → immutable transactionally accepted snapshot |
| ImagingStore._verify_directory / verify | Original ZIP, extracted bytes and persisted snapshot → exact integrity/acceptance check |
| ImagingStore.snapshots / preview_path | Patient or accepted snapshot → verified studies/artifact path |
| ImagingStore.discard | Pending key → remove proposal; accepted studies untouched |
| checked_nodule_review | Manifest and Review → resolved per-candidate decisions, valid calipers and matching authenticated reviewer |
| imaging_acceptance_digest | Proposal plus exact nodule Review → choices-bound digest; legacy uses its original proposal digest |
| verify_nodule_snapshot | Persisted study/review → study/actor/acceptance-digest validation |
| imaging_results.summarize / imaging_ui.result_summary | Validated manifest/review → concise counts, candidate/source ranges, scores and calipers; no diagnosis or automatic approval |
| pixels_for / nodule_viewer | Verified artifacts → source/candidate navigation; accepted caliper overlay recomputed from HU |
| candidate_controls / build_nodule_review | UI decisions and attestation → typed candidate Review; uncertainty stays blocked |
| preview_calipers | Source HU + unapproved endpoints → cyan line and physical distance; no persistence |
| research_report | Verified Study + completed Review → deterministic evidence-linked research summary, no diagnosis |
| report composition | Accepted snapshot → concise inspection results and verified report pictures; preserve producer attestation separately from LOVISA acceptance |
| sync_ct_contracts.sync | Companion source → equality check or intentional import-path-rewritten vendor update |

The shared models/renderer remain unchanged by the LOVISA branding update. Existing
`mhcra-*` names identify their versioned wire contract, not the current app name.
Original producer review is never rewritten into LOVISA acceptance. Calipers are
source-plane distances inside a candidate box, not confirmed lesion diameters.
