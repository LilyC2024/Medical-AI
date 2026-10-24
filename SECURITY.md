# LOVISA security and data handling

LOVISA accepts fictional histories, generated-synthetic imaging and explicitly
permitted public research imaging in labelled fictional composite cases. A
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
consistency. Hashes do not independently prove origin or model execution: anyone
can craft a ZIP with fabricated candidates and valid hashes. Producers can add an
Ed25519 signature, verified against public keys pinned locally in
`data/trust/producer_keys.json` (or `LOVISA_TRUSTED_PRODUCER_KEYS`). A bad
signature is rejected; unsigned or unpinned archives are accepted with a visible
warning unless `require_signature` is set. A signature identifies the key holder,
not model correctness, data permission or clinical truth. The
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

Brief report notes are authenticated reviewer commentary, not imported record
facts. A case-bound signed note changes the draft hash and requires fresh final
approval. Final HTML/Markdown/JSON exports verify exact report text, evidence
links, note authorship and CT integrity. HTML embeds verified images and permits
no external assets or scripts. Existing source and safety checks remain mandatory.

Approval also signs a content manifest covering the source records, model evidence,
CT snapshots and clinician note. Even when two studies produce identical short
text, substituting different images or source metadata invalidates the approval.

## Public research exception

Synthetic histories remain mandatory. Explicitly permitted deidentified public
imaging may enter separate research schemas only in fictional composite cases,
with dataset/license/subject provenance and no asserted real-patient linkage.
Original data/weights/accounts remain outside Git. Hashes are consistency checks,
not proof of permission or model execution. Review confirmations start selected,
but no approval exists until an authenticated user explicitly submits the exact
decision. Notes can be blank; the attestation and content binding remain mandatory.

## Error and task lifecycle hardening

Dynamic import, imaging and clinical errors render as bounded literal Markdown;
structured validation omits original input values and automatic help URLs. An
uploaded image/link expression cannot become a browser resource through an error
message. Actual source content remains in its source view. Worker saturation is
recoverable without clearing or fabricating an assessment. Cancelled work cannot
publish a late draft after patient/input changes. [Audit](docs/REVIEW.md).
