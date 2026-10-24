# Changelog

All notable changes to LOVISA are recorded here. Dated test outcomes live in
[EVALUATION.md](EVALUATION.md). LOVISA is educational/research software, not a
diagnostic device.

## Unreleased

### Added
- `model_provenance` on every draft: model name and Ollama digest, reasoning
  prompt version and SHA-256, safety policy version and SHA-256. It is bound into
  approval and exported in JSON and as an HTML footer.
- Optional model pin: `LOVISA_OLLAMA_MODEL_DIGEST` makes the adapter refuse any
  other installed build before reasoning.
- `Dockerfile` and `docker-compose.yml`: Ollama (pinned image digest) plus LOVISA
  in one loopback-only network namespace; UI on host `127.0.0.1:8501`.

## 0.7.0 — 24 October 2026

Baseline before this changelog was introduced; see [EVALUATION.md](EVALUATION.md)
for the history of earlier releases.
