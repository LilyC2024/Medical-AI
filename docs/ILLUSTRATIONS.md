# Clinical and technical illustrations

[Overview](../README.md) · [Precise architecture](ARCHITECTURE.md)

### Clinical workflow

![MHCRA AI workflow: synthetic records, safety routing, four specialists and clinician approval](images/mhcra-ai-workflow-v1.png)

Read this illustration from left to right. SQLite supplies the synthetic source
history, and the orchestrator applies the Safety Agent before reasoning. An
explicit warning stops the case for human assessment. Missing information pauses
it for authenticated review; an approved uncertainty assessment allows the
workflow to continue. History and medication extraction then precede constrained
reasoning, a safety recheck and an unverified draft. A clinician must approve the
exact draft before it becomes a reviewed report. Requested corrections keep it
pending. The separate strip shows human approval before source imports are saved.

### Technical flow

![MHCRA AI technical architecture: Streamlit, SQLite, sequential LangGraph nodes, local Ollama and authenticated review](images/mhcra-ai-technical-flow-v1.png)

The interface is Streamlit (`app.py`). Python validates a SQLite source snapshot,
then LangGraph passes it through the numbered specialist and validation nodes.
Only the Clinical Reasoning Agent sends a prompt and JSON Schema to Ollama at
`127.0.0.1:11434`; the default installed model is `gemma4:e2b`. Python validates
the returned JSON, source IDs, excerpts and attribution before composing a draft.
An authenticated review interrupt blocks completion until a matching approval
receipt exists. Completion and export recheck safety and approval integrity.

The bottom cards distinguish in-memory graph state from persistent SQLite data
and describe the supporting authentication, audit and source-traceability
components. Both urgent and uncertain cases reach the safety-review interrupt;
an urgent case can only stop. The illustrations summarize the flow; the precise
graph and module contracts are in [ARCHITECTURE.md](ARCHITECTURE.md).

The PNG illustrations were generated with the built-in image tool and checked
against the implementation. Their [workflow prompt](images/mhcra-ai-workflow-v1.prompt.txt),
[technical prompt](images/mhcra-ai-technical-flow-v1.prompt.txt) and
[editable technical Mermaid source](images/mhcra-ai-technical-flow-v1.mmd)
are included. Image generation was a documentation step; it is not an application
runtime dependency.


## Historical tissue-mask workbench

![Legacy synthetic tissue-mask workbench](images/mhcra-synthetic-workbench.png)

This older illustration shows the retained legacy four-class tissue-mask demo. Its voxel counts and teacher agreement are not lung-nodule results. The current nodule figure is in the [overview](../README.md).
