# Contributing to LOVISA

Read [AGENTS.md](AGENTS.md), [Architecture](docs/ARCHITECTURE.md) and
[Security](SECURITY.md). Work with synthetic records, local Ollama and explicit
human approvals. No paid/cloud inference, remote tracing, automatic medical
decisions or model database tools are supported.

## Make a change

1. Reuse `.venv` and installed `gemma4:e2b`; inspect versions before dependency edits.
2. Keep schemas, UI, storage, extraction, retrieval, safety and coordination separate.
3. Preserve immutable sources, exact excerpts and parameterized transactions.
4. Add meaningful regression coverage for changed behavior, including rejected paths.
5. Complete the current [phase](PLAN.md) before starting another.

Safety-policy changes require versioning and fresh review. A model must never
change escalation. A new CT contract must pass producer, consumer and joint checks
before updating the pinned integration commit. [Stable identifiers](docs/NAMING.md).

## Validate

```bash
.venv/bin/python -m pip check
.venv/bin/python -m compileall -q medical_assistant app.py scripts tests
.venv/bin/python -m pytest -q
.venv/bin/python scripts/check_docs.py
```

Use temporary databases and scripted models/reviewers. Run real local inference
separately when affected: `.venv/bin/python scripts/smoke_local.py --model gemma4:e2b`.
CT changes also need [joint validation](docs/VALIDATION.md). Record actual outcomes
in [Evaluation](EVALUATION.md); software checks are not clinical validation.

## Submit/publish

Explain the problem, resulting behavior, validation and remaining limits. Inspect
`git status --short`, `git diff --check` and the complete staged diff. Keep real
records, account data, tokens, logs, reports, images and weights out of commits/issues.
New fictional fixtures need deliberate review and an explicit `.gitignore` exception.

Hosted CI runs Python 3.11/3.12 regression and pinned CT smokes. It downloads setup
packages/weights explicitly and executes models on runner CPU; the app uses no
cloud inference service. It uploads no clinical reports or patient records.
LOVISA has no selected project-wide redistribution license; preserve notices for
[vendored CT code](third_party/README.md).

## Documentation and expert review

Keep the root README as a short installation/workflow map. Put operational and
schema detail in linked subject guides; preserve historical results as dated
measurements, not current capability claims. Regenerate source API references
with `scripts/generate_api_docs.py --write`, then run `--check` and the Markdown
file/anchor checker. Update every affected guide in both producer and receiver.

Three independent expert coding reviewers audited LOVISA, CT and endoscopy in the
current pass. Their regressions are software evidence and are separate from
clinician review and actual model inference. [Findings](docs/REVIEW.md).

Source contributions use [MIT](LICENSE); see [data/model terms](DATA_TERMS.md).
Review [branch decisions](docs/BRANCH_REVIEW.md) and reproduce lint/type/coverage
and dependency audits before changing shared contracts.
