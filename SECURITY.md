# LOVISA security and data handling

LOVISA accepts fictional histories and bounded generated-synthetic CT only. A
fictional flag/hash marker does not prove that input is free of personal data;
inspect sources manually. Clinical deployment and real-world record modification
are unsupported. [CT boundary](docs/IMAGING.md).

## Local operation

Keep Streamlit and Ollama on loopback. The adapter calls only `127.0.0.1:11434`,
disables proxies/redirects and rejects remote-backed models. Tracing switches are
disabled; set `OLLAMA_NO_CLOUD=1` on the daemon too. These checks are not a network
sandbox. The operating system and local process administrator remain trusted.

Accounts use salted PBKDF2 hashes and one-hour process-local sessions. Signed
receipts bind approvals to content. They do not verify clinical qualifications,
provide a production identity system or resist a database/process administrator.

All case/example controls are gated by a valid session. Logout/expiry hides them
and cancels session work. The explicit CLI `--local-demo` exception permits a
nonempty password only for username `demo`; no account or password is bundled.
Normal accounts require at least 12 characters. Keep demo credentials local and
loopback-only. This is a synthetic walkthrough, not production authentication.

## Sources and approvals

SQLite separates immutable originals from extracted facts; writes are parameterized
and transactional. Models have no database, filesystem, shell or approval tools.
Record imports, safety continuation, imaging acceptance and final report approval
have explicit review gates. Models cannot lower deterministic escalation.

CT ZIP/NPY/PNG/report validation checks bounds, paths, hashes and source/annotation
consistency. Hashes do not independently prove origin or model execution. The
structured safety policy is not comprehensive free-text emergency recognition.

## Persistence and publication

Pending graphs, proposals, sessions and receipt keys live in memory. Restarting
loses pending work. Local databases, accepted images and exports are not encrypted
by the app. Audit records are not a tamper-proof legal audit system.

Publish deliberately fictional fixtures only. Exclude databases, account hashes,
credentials, exports, local approvals, logs, weights and real images. Inspect the
staged diff and Git history; `.gitignore` does not remove previously tracked data.
Reference excerpts require redistribution rights. The evidence manifest starts empty.

Report suspected vulnerabilities privately when a maintainer channel is available.
Use a minimal synthetic reproduction; never post real records or credentials in
public issues. No certification or response-time commitment is claimed.
