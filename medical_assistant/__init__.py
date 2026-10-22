"""Local-only educational prototype. No tracing or remote inference."""

import os

# Override inherited tracing switches before importing LangGraph/LangChain.
os.environ["LANGCHAIN_TRACING_V2"] = "false"
os.environ["LANGCHAIN_TRACING"] = "false"
os.environ["LANGSMITH_TRACING"] = "false"
