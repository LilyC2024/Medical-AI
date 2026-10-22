"""Short real local inference connection test without patient data."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from medical_assistant.ollama_client import OllamaClient

client = OllamaClient(sys.argv[1] if len(sys.argv) > 1 else "gemma4:e2b")
try:
    result = client.assess(
        'Connection self-test. Return exactly {"missing_information":["LOCAL_CONNECTION_OK"]}. No clinical analysis.',
        'No patient data. Respond with the requested JSON only.',
        schema={"type": "object", "properties": {"missing_information": {"type": "array", "items": {"type": "string", "const": "LOCAL_CONNECTION_OK"}, "minItems": 1, "maxItems": 1}}, "required": ["missing_information"], "additionalProperties": False},
    )
    assert result.missing_information == ["LOCAL_CONNECTION_OK"]
    print("PASS: local Ollama structured inference connection", flush=True)
finally:
    client.close()
