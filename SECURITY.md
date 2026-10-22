# Security and data handling

Synthetic records only. A `fictional: true` field is an input constraint, not
proof that a file contains no personal information. Review every fixture and
import manually. Real clinical records, real-world record modification and
clinical deployment are outside the supported scope.

## Local boundary

Run Streamlit and Ollama on loopback. Inference requests are fixed to
`127.0.0.1:11434`. The adapter disables proxies and redirects, rejects remote-backed
model metadata, and inherited remote tracing switches are disabled. Configure
Ollama with `OLLAMA_NO_CLOUD=1` too. The daemon and operating system remain trusted;
these checks are not a network sandbox.

Accounts use salted PBKDF2 password hashes and expiring process-local sessions.
Signed approval receipts bind decisions to case and content. This protects the
normal application workflow. It does not verify professional qualifications or
protect against someone controlling the Python process, SQLite database or source.
This is not a production identity system or a multi-tenant service.

## Persistence and approvals

SQLite holds synthetic originals, facts, local account hashes and audit events.
Originals are immutable through normal app operations. Writes are parameterized
and transactional. Models have no database tools.

Imports and final reports require explicit human approval. Urgent holds cannot
continue reasoning within that case. Missing current information requires human
assessment. Models cannot lower escalation. The structured-field policy is a
synthetic workflow rule, not validated medical triage; it does not detect every
hazard from free text.

Checkpoints, sessions, approval signing keys and proposals are in process-local
memory. Restarting loses pending work. Disk storage is not encrypted by the app.
Audit events are not a tamper-proof legal audit service. Use operating-system
access controls on the local project directory.

## Publishing safely

Commit deliberately fictional fixtures only. Exclude local databases, passwords
or hashes, exported reports, logs, `.env` files, credentials, tokens and model
weights. Inspect staged content and existing history; `.gitignore` does not remove
already committed material. Reference excerpts require redistribution rights;
the default evidence manifest is empty.

For a suspected vulnerability, contact the maintainer privately using an
available private channel. Do not put patient records, credentials or full local
databases in public issues. Prefer a minimal synthetic reproduction. No formal
response-time commitment or security certification is provided.
