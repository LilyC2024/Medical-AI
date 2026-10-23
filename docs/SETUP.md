# Install and start LOVISA

[Overview](../README.md) · [First case](WORKFLOWS.md) · [CT installation](IMAGING.md)

## 1. Install the history application

Use Python 3.10 or newer; regression CI targets 3.10 and 3.12. Reuse `.venv` in an
existing checkout. For a new Linux/macOS checkout:

```bash
git clone https://github.com/LilyC2024/Medical-AI.git
cd Medical-AI
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.lock.txt
.venv/bin/python -m pip check
```

On Windows, use `.venv\Scripts\python.exe` for Python commands and `python -m
venv .venv` to create the environment. LOVISA's hosted tests run on Linux; the
standalone CT companion also has Windows checks. [Stable names](NAMING.md).

## 2. Start local Ollama

The default model is `gemma4:e2b`. Check the installed models:

```bash
ollama list
# Explicit setup download only, if the model is absent:
ollama pull gemma4:e2b
```

Start the server when it is not already running:

```bash
OLLAMA_NO_CLOUD=1 OLLAMA_HOST=127.0.0.1:11434 ollama serve
```

For a managed service, set these variables on that service. On PowerShell set
`$env:OLLAMA_NO_CLOUD="1"` and `$env:OLLAMA_HOST="127.0.0.1:11434"` before starting
Ollama. Inference stays local. Setup packages/weights require internet access.
The requested 16,384-token context needs sufficient local memory; performance is
hardware-dependent. No other model is claimed evaluated here.

## 3. Create a reviewer and launch

```bash
.venv/bin/python -m medical_assistant.auth
.venv/bin/python -m streamlit run app.py
```

The account command prompts for a username (3–80 characters; letters, digits,
underscore, dot or hyphen) and a password of at least 12 characters. It stores a
salted hash. This authenticates a local account, not clinical qualifications.

Open [localhost:8501](http://127.0.0.1:8501). Streamlit binds to loopback and disables
usage telemetry. Fictional fixtures are seeded idempotently at startup; optional
explicit seeding is `.venv/bin/python -m medical_assistant.database`.

Choose **Taylor Synthetic — checklist case**. Its missing screening and blood
pressure intentionally pause reasoning. Follow the [review walkthrough](WORKFLOWS.md).
Keep Ollama and Streamlit local. [Troubleshooting](VALIDATION.md).

## 4. Add CT when needed

LOVISA itself does not need PyTorch/MONAI. Install the CT project in a separate
Python 3.12 environment, then follow [Imaging](IMAGING.md). The existing GitHub
repository path is `Medical-AI`; the app is named LOVISA.
