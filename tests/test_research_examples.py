"""Manufactured upload-kit data; no dataset download or live inference."""

import hashlib
import json
import pytest
from medical_assistant.research_examples import (
    PATIENT,
    example_bundle,
    matching_endoscopy,
)


def test_example_kit_guards_case_bytes_and_paths(tmp_path):
    raw = b"manufactured research input"
    archive = b"manufactured archive"
    h = lambda b: hashlib.sha256(b).hexdigest()
    (tmp_path / "ct.zip").write_bytes(archive)
    m = dict(
        schema_version="lovisa-research-demo-v1",
        patient_id=PATIENT,
        ct=dict(file="ct.zip", sha256=h(archive)),
        endoscopy=[
            dict(
                file="ct.zip",
                sha256=h(archive),
                raw_sha256=h(raw),
                provenance={"dataset": "manufactured"},
            )
        ],
    )
    path = tmp_path / "examples.json"
    path.write_text(json.dumps(m))
    assert example_bundle("ct", PATIENT, root=tmp_path) == archive
    assert matching_endoscopy(raw, PATIENT, root=tmp_path)["dataset"] == "manufactured"
    with pytest.raises(ValueError):
        example_bundle("ct", "other-patient", root=tmp_path)
    with pytest.raises(ValueError):
        matching_endoscopy(b"unknown bytes", PATIENT, root=tmp_path)
    (tmp_path / "ct.zip").write_bytes(b"modified")
    with pytest.raises(ValueError):
        example_bundle("ct", PATIENT, root=tmp_path)
    m["ct"]["file"] = "../ct.zip"
    path.write_text(json.dumps(m))
    with pytest.raises(ValueError):
        example_bundle("ct", PATIENT, root=tmp_path)
    for bad in (
        [],
        {},
        dict(schema_version="lovisa-research-demo-v1", patient_id=PATIENT),
    ):
        path.write_text(json.dumps(bad))
        with pytest.raises(ValueError):
            example_bundle("ct", PATIENT, root=tmp_path)
