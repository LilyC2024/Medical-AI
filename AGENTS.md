# Architectural constraints

- Synthetic records only. Local Ollama inference only; no paid APIs, remote
  inference, remote tracing, or automatic medical decisions.
- Reuse `.venv` and the installed `gemma4:e2b` model. Inspect versions before
  changing dependencies. Use stdlib SQLite and installed LangChain/LangGraph.
- Keep immutable original sources separate from extracted facts. Never invent
  encounter dates, source quotations, measurements or medication orders.
- SQLite writes are parameterized and transactional. Models get no database tools.
- Safety routing is defined in a versioned local policy and executed in Python.
  Missing information is uncertainty, never evidence of safety. Urgent/uncertain
  cases pause for human review before reasoning. Models cannot lower escalation.
- Clinical possibilities are hypotheses. Record-derived statements require real
  source IDs and exact source excerpts; unsupported statements fail closed.
- Record imports and final clinical reports require explicit human approval.
  Real-world record modification is unsupported; synthetic mode is mandatory.
- Complete and test each PLAN.md phase before beginning the next.

# Development and validation

- Keep UI, schemas, persistence, specialist extraction, evidence retrieval, policy
  and workflow coordination in separate modules.
- Run `.venv/bin/python -m pytest -q`; use temporary databases and scripted models
  in automated tests. Never mark a mocked inference test as a live model test.
- Live smoke: `.venv/bin/python scripts/smoke_local.py --model gemma4:e2b`.
- Document actual test outcomes and limitations in `EVALUATION.md`.
