# Local setup

[Overview](../README.md) · [First case](WORKFLOWS.md) · [CT setup](IMAGING.md)

The package requires Python 3.10 or newer; CI exercises Python 3.10 and 3.12.
Use an installed Ollama server and enough local memory for the model and its
requested 16,384-token context. Performance depends on your hardware. The commands
below use a Linux/macOS shell; this release's hosted tests run on Linux. In an
existing checkout, reuse `.venv`. For a fresh checkout:

```bash
git clone https://github.com/LilyC2024/Medical-AI.git
cd Medical-AI
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.lock.txt
.venv/bin/python -m pip check
```

Start Ollama in another terminal if it is not already running:

```bash
OLLAMA_NO_CLOUD=1 OLLAMA_HOST=127.0.0.1:11434 ollama serve
```

For service-managed Ollama, configure these variables on the service instead.
Check that the development model is installed:

```bash
ollama list
```

The default model is `gemma4:e2b`. If its weights are absent, install them explicitly:

```bash
ollama pull gemma4:e2b
```

Dependency installation and the initial model download need internet access.
Inference and application operation use local resources after installation.

Optionally initialize the built-in synthetic records explicitly, then create a
local reviewer account. The UI also seeds these fixtures idempotently at startup:

```bash
.venv/bin/python -m medical_assistant.database
.venv/bin/python -m medical_assistant.auth
```

Seeding is idempotent: exact repeats do not duplicate encounters; conflicts roll
back. The account command prompts for a 3–80 character username using letters,
digits, `_`, `.` or `-`, and a password of at least 12
characters. Passwords are stored as salted PBKDF2 hashes. This authenticates a local
account; it does not verify professional clinical credentials.

Start the interface:

```bash
.venv/bin/python -m streamlit run app.py
```

Open [the local interface](http://127.0.0.1:8501). The checked-in Streamlit
configuration binds to loopback and disables usage telemetry. Keep the app local.

Windows uses `.venv\Scripts\python.exe` in place of `.venv/bin/python`. MHCRA hosted tests run on Linux; standalone CT also has Windows checks.
