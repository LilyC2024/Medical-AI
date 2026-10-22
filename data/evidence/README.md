# Approved local evidence collection

No medical references have been approved yet. The default manifest is deliberately
empty; the app must disclose this gap and must not invent citations.

A human may add `.txt` or `.md` excerpts inside this folder, then explicitly list
their IDs, titles, relative paths, exact UTF-8 SHA-256 digests and `approved: true`
in `manifest.json`. Only those unchanged, approved files can be retrieved.
No web search, recursive file discovery or remote reference retrieval occurs.
