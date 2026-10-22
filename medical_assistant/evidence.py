"""Retrieve only explicitly approved, hash-verified files in a local collection."""
import json
import re
from pathlib import Path

from langchain_core.runnables import RunnableLambda
from pydantic import Field

from medical_assistant.models import StrictModel
from medical_assistant.report import digest


class EvidenceItem(StrictModel):
    id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    path: str = Field(min_length=1)
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    approved: bool = Field(strict=True)


class EvidenceManifest(StrictModel):
    documents: list[EvidenceItem]


class LocalEvidenceCollection:
    def __init__(self, directory: Path):
        self.directory = directory.resolve()

    def retrieve(self, query: str) -> list[dict]:
        def local_search(query):
            manifest = EvidenceManifest.model_validate_json((self.directory / "manifest.json").read_text())
            if len({item.id for item in manifest.documents}) != len(manifest.documents):
                raise ValueError("Duplicate local evidence IDs")
            words = set(re.findall(r"\w+", query.casefold()))
            results = []
            for item in manifest.documents:
                if not item.approved:
                    continue
                path = (self.directory / item.path).resolve()
                if not path.is_relative_to(self.directory) or path.suffix not in (".txt", ".md"):
                    raise ValueError("Evidence path is outside the approved local collection")
                if path.stat().st_size > 20_000:
                    raise ValueError("Approved evidence excerpt exceeds 20 KB")
                text = path.read_text()
                if digest(text) != item.sha256:
                    raise ValueError("Approved local evidence changed; approval must be renewed")
                score = len(words & set(re.findall(r"\w+", (item.title + " " + text).casefold())))
                if score:
                    results.append({"id": item.id, "title": item.title, "path": item.path,
                                    "sha256": item.sha256, "text": text, "score": score})
            return sorted(results, key=lambda item: (-item["score"], item["id"]))[:3]
        return RunnableLambda(local_search).invoke(query)
