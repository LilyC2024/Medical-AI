# Human-factors protocol: do reviewers catch wrong candidates?

[Overview](../README.md) · [Checklists](REPORTING_CHECKLISTS.md) · [Security](../SECURITY.md)

**Status: written, not executed.** No participant has used this protocol. Any run
needs appropriate ethics/institutional approval for the reviewers taking part. Only
fictional histories and permitted public research images are used; the software
is not a diagnostic device.

## Question

The review gate is the main safeguard against wrong model output and forged
archives. The key measure is whether reviewers **reject a seeded wrong candidate**
instead of accepting it.

## Design

- **Participants:** at least one clinician familiar with CT or colonoscopy, and
  one human security reviewer for the trust-boundary items. Record role and
  experience; local accounts do not verify either.
- **Cases:** about 20 fictional composite cases. In a random, concealed subset
  (about 30%) seed one error per case: a CT or endoscopy candidate box on normal
  tissue, a hypothesis whose cited excerpt does not support it, an unsigned or
  unpinned archive, or a note that adds an unsupported fact.
- **Conditions:** the review gates proposed in the open review-gate and
  producer-signature changes (unselected confirmations, active per-candidate
  choice, required preview, false-positive display, signature warnings). If time
  allows, compare with the previous preselected defaults on a separate build in
  counterbalanced order.
- **Procedure:** reviewers work as they normally would, without being told the
  seeding rate. Capture decisions from the audit trail, plus time per case and a
  short questionnaire on trust and workload.

## Measures

| Measure | Definition |
| --- | --- |
| Seeded-error catch rate | Seeded errors rejected or flagged ÷ seeded errors shown (primary) |
| False rejection rate | Correct candidates rejected ÷ correct candidates shown |
| Signature-warning response | Share of unsigned/unpinned archives questioned before acceptance |
| Time per case | From opening the study to submitting the decision |
| Automation-bias indicators | Acceptances with no candidate inspected (viewer events) |

Report counts with 95% confidence intervals; with ~6 seeded errors per reviewer,
results are descriptive, not a powered comparison.

## Security review checklist (human reviewer)

Pinned-key handling and rotation, `require_signature`, receipt-key storage, the
unencrypted SQLite/checkpoint files, the non-tamper-evident audit log, the Compose
network namespace, and the prompt-injection surface of free-text record fields.
