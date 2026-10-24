# Local response budgets

[Overview](../README.md) · [Workspace](INTERFACE.md) · [Validation](VALIDATION.md)

## What changed

| Path | Implementation |
| --- | --- |
| Patient reasoning | Session-owned daemon task; immediate progress/cancel; 110-second publication deadline |
| Ollama | Local metadata check up to 5s; 90-second call budget; weights kept warm for 15 minutes |
| Reasoning output | Model selects catalog/evidence IDs; Python copies exact source text and validates the expanded assessment |
| CT | Separate process, real-stage log markers, one-second polling and a 110-second watchdog; cancellation kills its process group |
| Viewer | Only the selected workspace renders; snapshot list verified, selected-view resolver verified once, requested previews hash-checked individually |

Accepted-study loading and resolver creation are two fixed validation passes;
preview access no longer repeats full archive validation for each image.

A local operation should display progress immediately and either a result or an
explicit stop before two minutes under normal browser/server scheduling. This is
a response budget, not a promise of successful inference on every PC. A sleeping
browser, saturated machine or slow filesystem can delay display. Human review
time is separate. The budget does not shorten records or bypass integrity checks.

`WorkTask` limits concurrent clinical workers to two. Cancellation/deadline stops
publication; an in-flight HTTP/native call may unwind afterward and holds its slot
until it exits. No late result can become a draft or enable approval. CT runs are
terminated as processes. Failed/incomplete/invalid model output fails closed;
there is no fabricated, cloud or deterministic reasoning fallback.

## Smaller model output, same evidence boundary

`SpecialistAgent` supplies the constrained reasoning schema. The Ollama adapter
recognizes its explicit compact-protocol marker and sends bounded IDs from the
same eligible hypothesis, consideration and question catalogs. It retains the
supplied record in the prompt. The model selects supporting/conflicting entry IDs
and approved reference IDs. Python expands those IDs into exact original excerpts
and attribution, then runs normal source/catalog validation. Unknown, duplicate,
unsupported or invented IDs/prose are rejected. These hypotheses still require
clinician review; IDs do not establish relevance or diagnostic validity.

The compact call allows 1,200 output tokens instead of generating repeated source
quotes. Other structured adapter calls use 2,000. Both retain the 16,384 context
and conservative 11,000-byte input budget, applied to the actual transmitted
prompt/schema after compact conversion. Entire records remain present; unused
full-output schema size cannot reject a valid compact request. No dependency/model change was needed.

## Actual checks on this local CPU environment

| Executed synthetic operation | Observed wall time |
| --- | --- |
| Fixture CT producer + receiver validation | 1.65s |
| Installed pretrained CT producer + receiver validation | 12.43s |
| Actual gemma4:e2b clinical smoke before compact output | 44.58s |
| Actual gemma4:e2b clinical smoke with compact output | 23.40s |

These are individual smoke runs, not a controlled benchmark or latency guarantee.
Model cache/warm-up and competing load affect results. CT used generated
32×64×64 pixels; the fixture finder is non-ML. The pretrained run used installed
weights on CPU. No new GPU/NPU execution, full-size CT timing, clinical accuracy or
clinician time-saving result is claimed. Neither smoke approved a clinical report.
[Detailed evaluation](../EVALUATION.md).

Use fixture mode for the fastest walkthrough. For pretrained CT choose CPU or an
actually available CUDA device; unavailable acceleration fails explicitly. Fetch
weights during setup, never inference. Existing companion training/evaluation
workflows remain available separately; they are not two-minute UI operations.

## Real research data

Full CT inference and model training are offline setup and may exceed two minutes.
The interface opens prepared, bounded real CT evidence instead of running a whole
scan synchronously. Research endoscopy uploads run in the bounded local worker;
progress/cancellation/110-second termination remain. Real-image inference timing
is distinct from setup/training and is recorded in [evaluation](../EVALUATION.md).

## Failure and measurement interpretation

Worker-slot exhaustion is now caught at safety preparation, assessment submission
and draft generation. It preserves the existing safety context and shows a
retryable explanation. Stopped jobs expose a bounded literal reason; invalid
source input is never echoed as active Markdown. New input/settings/patient
transitions cannot publish an old task's late result.

Do not compare a warmed model's predict-only timing with Upload-to-visible-result
or full-volume latency. Current smoke outcomes identify what was timed, input
shape/scope, backend and whether reviews were simulated. Training and full-scan
preparation remain offline; the interactive deadline is not a clinical turnaround
guarantee. [Expert review](REVIEW.md) · [Current evidence](../EVALUATION.md).
