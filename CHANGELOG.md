# Changelog

All notable changes to LOVISA are recorded here. Dated test outcomes live in
[EVALUATION.md](EVALUATION.md). LOVISA is educational/research software, not a
diagnostic device.

## Unreleased

### Added
- CI gates: ruff (syntax/undefined names), mypy on schemas, safety and
  orchestration, 85% coverage floor (measured 89.10%), pip-audit of the lockfile,
  gitleaks full-history secret scan, CodeQL and a CycloneDX SBOM artifact;
  Dependabot for pip and GitHub Actions.

### Changed
- Two behaviour-preserving typing fixes for mypy (`models.py` walrus filter,
  documented ignore in `grounding.py`).

### Security
- Lockfile: Pillow 12.3.0 → 13.0.0 (pip-audit reported 37 known vulnerabilities
  in 12.3.0, all fixed in 13.0.0). Streamlit 1.65.0 → 1.66.1, the first release
  that permits Pillow 13. Pillow decodes uploaded endoscopy images.

## 0.7.0 — 24 October 2026

Baseline before this changelog was introduced; see [EVALUATION.md](EVALUATION.md)
for the history of earlier releases.
