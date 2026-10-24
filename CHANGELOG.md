# Changelog

All notable changes to LOVISA are recorded here. Dated test outcomes live in
[EVALUATION.md](EVALUATION.md). LOVISA is educational/research software, not a
diagnostic device.

## Unreleased

### Added
- Durable receipt key from `LOVISA_RECEIPT_KEY` or the OS keyring (optional
  `keyring` extra); `python -m medical_assistant.persistence` creates one.
- With a durable key, pending review graphs use a LangGraph SQLite checkpointer
  and **Safety check** offers **Resume saved review** after a restart. Without one,
  behaviour is unchanged (in-memory). New dependency
  `langgraph-checkpoint-sqlite` (lockfile: 3.1.1, aiosqlite 0.22.1, sqlite-vec 0.1.9).

### Changed
- SECURITY and SETUP document key handling and require full-disk encryption for
  `data/`, since databases and checkpoints are not encrypted by the app.

## 0.7.0 — 24 October 2026

Baseline before this changelog was introduced; see [EVALUATION.md](EVALUATION.md)
for the history of earlier releases.
