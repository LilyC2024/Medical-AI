"""Producer signatures at the LOVISA boundary: pinned keys, warnings and FP claims."""

import io
import json
import zipfile

import pytest
from test_endoscopy import endo_bytes
from test_nodule_imaging import nodule_bytes, nodule_store  # noqa: F401
from test_ui import login, ui  # noqa: F401

from medical_assistant.producer_signature import (
    SIGNATURE_ENTRY,
    Performance,
    generate_key,
    load_private_key,
    sign_archive,
)
from medical_assistant.producer_trust import TrustConfig, load_trust, main, pin
from medical_assistant.producer_ui import UNSIGNED, false_positive_text

MEASURED = Performance(
    measured=True,
    metric="1 - box-region precision proxy",
    false_positive_fraction=0.785,
    test_images=168,
    negative_images=0,
    evaluation_sha256="c" * 64,
    limitations="Exploratory: no negative images.",
)


@pytest.fixture
def keys(tmp_path):
    made = {}
    for producer in ("lovisa-ct", "lovisa-endo"):
        path = tmp_path / f"{producer}.key"
        made[producer] = (path, generate_key(path))
    return made


def trust(keys, *producers, require=False):
    return TrustConfig(
        require_signature=require,
        keys=[
            {"producer": p, "public_key_b64": keys[p][1]["public_key_b64"], "label": p}
            for p in producers
        ],
    )


def signed(payload, keys, producer, performance=None):
    path = keys[producer][0]
    args = (performance,) if performance else ()
    return sign_archive(payload, load_private_key(path), producer, *args)


def test_verified_unsigned_and_unpinned_archives_are_recorded(nodule_store, keys):  # noqa: F811
    imaging, _ = nodule_store
    imaging.trust = trust(keys, "lovisa-ct")
    _, proposal = imaging.prepare(
        signed(nodule_bytes(study_id="s1"), keys, "lovisa-ct"), "synthetic-checklist"
    )
    assert proposal["producer_signature"]["status"] == "verified"
    assert "not measured" in false_positive_text(proposal)
    _, unsigned = imaging.prepare(nodule_bytes(study_id="s2"), "synthetic-checklist")
    assert unsigned["producer_signature"]["status"] == "unsigned"
    assert "not available" in false_positive_text(unsigned)
    imaging.trust = trust(keys)
    with pytest.raises(ValueError, match="not pinned"):
        imaging.prepare(signed(nodule_bytes(study_id="s3"), keys, "lovisa-ct"), "synthetic-checklist")


def test_tampered_wrong_modality_and_required_signatures_fail_closed(nodule_store, keys):  # noqa: F811
    imaging, _ = nodule_store
    imaging.trust = trust(keys, "lovisa-ct", "lovisa-endo")
    payload = signed(nodule_bytes(study_id="t1"), keys, "lovisa-ct")
    with zipfile.ZipFile(io.BytesIO(payload)) as z:
        files = {n: z.read(n) for n in z.namelist()}
    envelope = json.loads(files[SIGNATURE_ENTRY])
    envelope["claims"]["performance"] = MEASURED.model_dump()
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w") as z:
        for name, data in dict(files, **{SIGNATURE_ENTRY: json.dumps(envelope)}).items():
            z.writestr(name, data)
    with pytest.raises(ValueError, match="verification failed"):
        imaging.prepare(out.getvalue(), "synthetic-checklist")
    with pytest.raises(ValueError, match="wrong (modality|producer)"):
        imaging.prepare(
            signed(nodule_bytes(study_id="t2"), keys, "lovisa-endo"),
            "synthetic-checklist",
        )
    imaging.trust = trust(keys, "lovisa-ct", require=True)
    with pytest.raises(ValueError, match="required"):
        imaging.prepare(nodule_bytes(study_id="t3"), "synthetic-checklist")


def test_measured_rate_is_shown_only_from_a_verified_claim(nodule_store, keys):  # noqa: F811
    imaging, _ = nodule_store
    imaging.trust = trust(keys, "lovisa-endo")
    _, proposal = imaging.prepare(
        signed(endo_bytes(), keys, "lovisa-endo", MEASURED), "synthetic-checklist"
    )
    text = false_positive_text(proposal)
    assert "about 78%" in text and "168 test images" in text and "0 negative" in text
    forged = dict(proposal, producer_signature=dict(proposal["producer_signature"], status="unsigned"))
    assert "not available" in false_positive_text(forged)


def test_pin_cli_writes_local_trust_and_rejects_duplicates(tmp_path, keys, capsys):
    path = tmp_path / "trust/keys.json"
    public = keys["lovisa-ct"][1]["public_key_b64"]
    main(["--producer", "lovisa-ct", "--public-key", public, "--label", "CT", "--trust-file", str(path)])
    assert "1 pinned key" in capsys.readouterr().out
    assert keys["lovisa-ct"][1]["key_id"] in load_trust(path).trusted()
    with pytest.raises(ValueError, match="already pinned"):
        pin(path, "lovisa-ct", public, "again")
    assert load_trust(tmp_path / "missing.json") == TrustConfig()


def test_review_screen_warns_and_shows_rate_beside_every_candidate(ui):  # noqa: F811
    app, _, _, _ = ui
    login(app)
    app.button(key="guide_ct-review").click().run()
    store = app.session_state.imaging_store
    app.session_state.imaging_proposal = store.prepare(
        nodule_bytes("fictional-001"), "fictional-001"
    )
    app.run()
    assert not app.exception
    assert any(UNSIGNED == w.value for w in app.warning)
    candidates = [r for r in app.radio if "_decision_" in str(r.key)]
    captions = [c.value for c in app.caption if "unmatched-candidate" in c.value]
    assert candidates and len(captions) == len(candidates)
