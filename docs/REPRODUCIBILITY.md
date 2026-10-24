# Reproducibility, trust and restart recovery

[Overview](../README.md) · [Setup](SETUP.md) · [Imaging](IMAGING.md) · [Branch review](BRANCH_REVIEW.md)

## Supported environment

LOVISA now requires Python 3.11+; CI targets 3.11/3.12. Pillow 13 fixes the known
issues found in the previous 12.3 installation and does not support Python 3.10.
The existing local Python 3.10 environment was preserved; validation and deployment
use the separate `.venv-release` Python 3.12 environment. For a fresh installation,
create `.venv` with Python 3.12 and install `requirements.lock.txt`. Do not copy
account databases, research images or private keys to Git.

## Model, prompt and safety identity

The local `/api/tags` response supplies the observed installed model digest.
`LOVISA_OLLAMA_MODEL_DIGEST=<64-character digest>` optionally pins that digest;
a mismatch/missing installed model fails before chat. Remote-backed models remain
prohibited. Reports record the model name/digest, prompt version/hash and policy
version/hash. This metadata is included in exact-content approval and a small
HTML footer; it is not evidence of diagnostic accuracy. The application still
uses one local LLM reasoning role and deterministic Python extraction/safety roles.

## Optional durable pending reviews

Without a configured durable key, workflows/receipts are process-local as before.
Generate a secret with `python -m medical_assistant.persistence`, then set
`LOVISA_RECEIPT_KEY` in the local environment; never commit or share its output.
Alternatively install the `keyring` extra and run
`python -m medical_assistant.persistence --store-keyring` with a working OS keyring.
The key is not automatically created, rotated or stored in the repository.

Durable checkpoints use `<database-name>.workflow_checkpoints.sqlite3` beside the
case database. Keys and case identity are scoped to the resolved database path.
After restart, sign in again, select the same patient and open Safety check to
resume the newest saved safety/final-report review. Only human-review interrupts
are offered; interrupted generation must be started again. Pending image proposals,
worker handles and sessions are not restored. Saved cases are immutable snapshots;
new imported records/images require a fresh case. Policy/date/image integrity and
approval receipts are rechecked before generation/completion/export.

Keep the master key and database path stable. Moving the database or changing the
key invalidates earlier receipts; restarting with a new key cannot approve old
work. Checkpoints contain fictional record/report text and are unencrypted; keep
all local runtime storage private. This is not a clinical record recovery system.

## Pinned imaging exporters

Create a producer key with the CT/endoscopy companion's `keygen --output` command.
The private PEM stays with that exporter (owner-only permissions on POSIX). Pin
only the public key after verifying its identity through a trusted local channel:

```bash
python -m medical_assistant.producer_trust --producer lovisa-ct \
  --public-key '<public_key_b64>' --label 'Local CT exporter'
```

Use `lovisa-endo` for the other producer. The default trust configuration is
`data/trust/producer_keys.json`; override with `LOVISA_TRUSTED_PRODUCER_KEYS`.
Setting `require_signature: true` rejects unsigned imports too. Unknown signed
keys are rejected even when unsigned older evidence is allowed. Tampered signed
claims/evidence and wrong modalities fail closed. A verified signature identifies
an exporting key and exact bytes, not truthful training, data permission or a
clinical diagnosis. Revocation changes future imports; existing approved evidence
retains its recorded trust snapshot and is not automatically reclassified.

Endoscopy performance is attached only when an evaluation is explicitly supplied
and matches the ONNX graph, configuration, backend and test partition. It remains
a producer declaration. An unmatched-candidate fraction (1 − precision proxy) is
not a screening false-positive rate. No negative exams means specificity is unknown.

## Redacted local traces and audit replay

Set `LOVISA_TRACE_FILE` to a private local JSONL path before starting the app to
record workflow step names, hashed case references, status/timing and exception
class only. No network exporter is configured. Exception recording/status text and
automatic host/process resource collection are disabled, including at graph
interrupts. Do not point the file into a published directory or enable external
instrumentation; unset the variable to disable tracing.

Clinical report → Audit trail shows the selected patient's local action history.
Displayed review decisions are compared with their signed receipts. Old ephemeral
keys are labelled unverifiable, and modified decisions are flagged. The database
and log are not tamper-evident and local accounts do not verify qualifications.

## Deferred work

The proposed Compose stack is not shipped: container execution, persistent volume
permissions and companion discovery need dedicated validation. Clinical human-
factors testing and external validation remain proposed, not executed. See the
[reporting checklist mapping](REPORTING_CHECKLISTS.md) and
[human-factors protocol](HUMAN_FACTORS.md).
