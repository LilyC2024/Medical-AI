# LOVISA UI only. Research/education use; not a diagnostic device.
FROM python:3.12.14-slim-bookworm@sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e

ENV PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    LANGCHAIN_TRACING_V2=false \
    LANGCHAIN_TRACING=false \
    LANGSMITH_TRACING=false \
    OLLAMA_NO_CLOUD=1

RUN useradd --create-home --uid 10001 lovisa
WORKDIR /app
COPY requirements.lock.txt .
RUN python -m pip install --no-compile -r requirements.lock.txt
COPY --chown=lovisa:lovisa . .
USER lovisa

EXPOSE 8501
# 0.0.0.0 is inside the shared container namespace only; compose publishes the
# port on the host's 127.0.0.1. Ollama is reached on that namespace's loopback.
CMD ["python", "-m", "streamlit", "run", "app.py", "--server.address", "0.0.0.0", "--server.port", "8501"]
