# Contributing to MHCRA AI

This is a synthetic-record educational prototype. Read [AGENTS.md](AGENTS.md),
[the architecture](docs/ARCHITECTURE.md) and [SECURITY.md](SECURITY.md) before changes.
No real patient data, remote inference, paid APIs, remote tracing, automatic
medical decisions or model database tools are accepted.

## Local development

Follow [README.md](README.md) to install dependencies, initialize synthetic SQLite
and create a local reviewer account. Reuse `.venv` and the installed
`gemma4:e2b` model. Inspect versions before changing dependencies and explain any
lock-file update in the pull request.

Keep schema, UI, storage, extraction, evidence retrieval, safety and workflow
coordination separate. Preserve immutable sources, parameterized transactional
writes, exact source excerpts and explicit authenticated human approvals. Treat
all diagnostic possibilities as hypotheses. Policy changes need a version update
and fresh review; the model must never lower escalation.

## Validation

Run:

```bash
.venv/bin/python -m pip check
.venv/bin/python -m compileall -q medical_assistant app.py scripts tests
.venv/bin/python -m pytest -q
```

Use temporary SQLite databases and scripted models in automated tests. Add
meaningful regression coverage for changed behavior, especially rejected and
unauthenticated actions, source mismatches, immutable IDs, missing data and safety
holds. For inference changes, separately run:

```bash
.venv/bin/python scripts/smoke_local.py --model gemma4:e2b
```

Record actual outcomes and limitations in [EVALUATION.md](EVALUATION.md). Distinguish
mocked tests from live local-model tests. Neither constitutes clinical validation.
GitHub CI runs the locked-dependency regression suite on Python 3.10 and 3.12.
It downloads dependencies but does not install models, call a hosted LLM, upload
patient records/reports or deploy the app. A newly added CI configuration is not
proof of a successful hosted run; inspect the actual Actions result.

## Pull requests and data hygiene

Describe the problem, resulting behavior, validation and remaining limitations.
Use minimal, deliberately fictional reproductions. Do not include databases,
accounts, passwords, tokens, exports, logs, `.env` files or real medical records in
issues, commits or pull requests. New synthetic fixtures require deliberate review
and an explicit `.gitignore` exception: arbitrary files under `data/patients/` are
ignored by default. The two bundled fixtures are approved demonstration data.

Check `git diff --check`, `git status --short` and the complete staged diff before
committing. Existing tracked secrets are not protected by `.gitignore`.
Report security concerns privately when a private maintainer channel is available.
No redistribution license has been selected; do not assume open-source licensing.
