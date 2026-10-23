# LOVISA local reference collection

The default [manifest](manifest.json) is empty. LOVISA reports that no approved
reference support was retrieved; it never invents a citation to fill that gap.

To add an excerpt, verify permission, save UTF-8 `.txt`/`.md` inside this folder,
and explicitly record its unique ID, title, relative path, SHA-256 and
`approved: true` in the manifest. Each excerpt is limited to 20 KB. Changed bytes
require renewed approval. Retrieval checks approved entries only, scores word
overlap and returns at most three results. No web search or automatic downloads.

[Reference rules](../../docs/RECORDS.md) · [Implementation](../../medical_assistant/evidence.py).
