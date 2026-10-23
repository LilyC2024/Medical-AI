"""Manufactured pixels test research boundaries; these are not real-image ML tests."""

import copy
import io
import json
import zipfile

import pytest
from test_endoscopy import endo_bytes
from test_nodule_imaging import nodule_bytes

from medical_assistant.imaging_contract import validate_bundle

PATIENT = "research-composite-demo"
PROVENANCE = dict(
    dataset="scripted test data",
    source_url="https://example.org/research",
    license="test-only",
    research_subject_id="independent-research-subject",
    original_sha256="a" * 64,
    composite_case=True,
)


def rewrite(payload, change):
    out = io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(payload)) as old, zipfile.ZipFile(out, "w") as new:
        manifest = json.loads(old.read("bundle.json"))
        change(manifest)
        new.writestr("bundle.json", json.dumps(manifest))
        for name in old.namelist():
            if name != "bundle.json":
                new.writestr(name, old.read(name))
    return out.getvalue()


def public_endo(m):
    m.update(
        schema_version="lovisa-endo-research-v2", synthetic=False, research=PROVENANCE
    )
    s = m["study"]
    s["input_kind"] = "approved-public-research"
    s["model"].update(
        name="UNetSmall", backend="onnx-cpu", evaluation_scope="positive-images-only"
    )


def public_ct(m):
    m.update(
        schema_version="lovisa-ct-research-v3",
        synthetic=False,
        research=PROVENANCE,
        crop_origin_zyx=[0, 0, 0],
    )
    s = m["study"]
    s.update(
        input_kind="approved-public-research",
        protocol_attestation="adult-noncontrast-chest-complete",
    )
    s["model"]["synthetic_fixture"] = False
    m["original_study"] = copy.deepcopy(s)
    m["inference_region_zyx"] = [0, 0, 0, *s["geometry"]["shape_zyx"]]


@pytest.mark.parametrize(
    "producer,change", [(endo_bytes, public_endo), (nodule_bytes, public_ct)]
)
def test_public_research_is_separate_and_pixels_verified(producer, change):
    payload = rewrite(producer(PATIENT), change)
    bundle, _, artifacts = validate_bundle(payload, PATIENT)
    assert bundle.synthetic is False and bundle.research.composite_case is True
    assert artifacts
    for mutate in (
        lambda m: m.update(synthetic=True),
        lambda m: m.pop("research"),
        lambda m: m["research"].update(composite_case=False),
        lambda m: m.update(patient_id="synthetic-checklist"),
    ):
        with pytest.raises(ValueError):
            validate_bundle(rewrite(payload, mutate), PATIENT)


def test_research_ct_geometry_and_predictions_cannot_be_relocated():
    payload = rewrite(nodule_bytes(PATIENT), public_ct)
    for mutate in (
        lambda m: m.update(crop_origin_zyx=[0, 1, 0]),
        lambda m: m["study"]["candidates"][0].update(score=0.9),
        lambda m: m["original_study"]["model"].update(name="different detector"),
    ):
        with pytest.raises(ValueError):
            validate_bundle(rewrite(payload, mutate), PATIENT)


@pytest.mark.parametrize("producer", [endo_bytes, nodule_bytes])
def test_old_synthetic_schema_cannot_relabel_public_images(producer):
    def mutate(m):
        m["study"]["input_kind"] = "approved-public-research"

    with pytest.raises(ValueError):
        validate_bundle(rewrite(producer(PATIENT), mutate), PATIENT)


@pytest.mark.parametrize("producer", [endo_bytes, nodule_bytes])
def test_previous_stored_synthetic_manifests_remain_verifiable(tmp_path, producer):
    """New optional provenance must not invalidate earlier accepted fixture manifests."""
    from medical_assistant.database import seed
    from medical_assistant.imaging import ImagingStore

    seed(tmp_path / "old.sqlite3")
    store = ImagingStore(tmp_path / "old.sqlite3")
    key, item = store.prepare(producer(), "synthetic-checklist")
    old = copy.deepcopy(item)
    for field in (
        "research",
        "original_study",
        "crop_origin_zyx",
        "inference_region_zyx",
    ):
        old["manifest"].pop(field, None)
    store._verify_directory(store.root / "pending" / key, old)


def test_public_ct_must_declare_and_respect_actual_inference_coverage():
    payload = rewrite(nodule_bytes(PATIENT), public_ct)
    for mutate in (
        lambda m: m.pop("inference_region_zyx"),
        lambda m: m.update(inference_region_zyx=[0, 0, 0, 2, 5, 5]),
    ):
        with pytest.raises(ValueError):
            validate_bundle(rewrite(payload, mutate), PATIENT)
