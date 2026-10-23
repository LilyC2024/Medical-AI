"""Verified representative CT images and self-contained, approval-gated HTML reports."""

import base64
import html
import io
from dataclasses import dataclass

from PIL import Image

from medical_assistant.nodule_exchange import NoduleBundle, source_pixels, wire_pixels
from medical_assistant.nodule_support import is_nodule, verify_nodule_snapshot
from medical_assistant.report import NOTICE, summary_parts
from medical_assistant.storage import validate_reviewed_report


@dataclass(frozen=True)
class InspectionFigure:
    caption: str
    source_png: bytes
    overlay_png: bytes


def inspection_figures(state, store):
    """Render at most three representative study slices, never omit summary counts."""
    snapshots = state.get("imaging", [])
    patient = state["record"]["patient_id"]
    if any(s["manifest"]["patient_id"] != patient for s in snapshots):
        raise ValueError("Imaging snapshot patient mismatch")
    store.verify(snapshots)
    figures = []
    for number, snapshot in enumerate(snapshots[:3], 1):
        manifest = snapshot["manifest"]
        resolve = store.preview_resolver(snapshot)
        if is_nodule(manifest):
            bundle = NoduleBundle.model_validate(manifest)
            review = verify_nodule_snapshot(snapshot)
            accepted = {
                d.candidate_id for d in review.decisions if d.decision == "accept"
            }
            preferred = next((d.caliper for d in review.decisions if d.caliper), None)
            candidate = next(
                (c for c in bundle.study.candidates if c.candidate_id in accepted),
                next(iter(bundle.study.candidates), None),
            )
            index = (
                int(preferred.start_zyx[0])
                if preferred
                else int((candidate.box_zyx[0] + candidate.box_zyx[3]) / 2)
                if candidate
                else bundle.study.geometry.shape_zyx[0] // 2
            )
            item = next(a for a in bundle.artifacts if a.role == "source_volume")
            hu = source_pixels(
                bundle, {item.path: resolve("source_volume", None).read_bytes()}
            )
            _, overlay = wire_pixels(
                bundle.study,
                hu,
                index,
                calipers=[d.caliper for d in review.decisions if d.caliper],
            )
            buffer = io.BytesIO()
            Image.fromarray(overlay).save(buffer, format="PNG")
            overlay_png = buffer.getvalue()
            mode = (
                "non-ML demonstration"
                if bundle.study.model.synthetic_fixture
                else "installed detector"
            )
            caption = f"Study {number} · {mode} · source slice {index}. Amber: candidate boxes; cyan: reviewed calipers. Representative view only."
        else:
            index = manifest["geometry"]["shape_zyx"][0] // 2
            overlay_png = resolve("overlay_preview", index).read_bytes()
            caption = f"Study {number} · legacy tissue-mask demonstration · source slice {index}. Representative view, not nodule detection."
        figures.append(
            InspectionFigure(
                caption, resolve("source_preview", index).read_bytes(), overlay_png
            )
        )
    return figures


def portable_html(payload, *, auth, safety=None):
    """Final download with embedded verified CT pictures; no scripts, external assets or draft export."""
    record = validate_reviewed_report(payload, auth=auth, safety=safety)
    from medical_assistant.imaging import ImagingStore

    figures = inspection_figures(payload, ImagingStore(auth.path))
    parts = summary_parts(
        record,
        payload["assessments"],
        payload.get("imaging"),
        payload.get("clinician_note"),
    )
    paragraphs = "".join(
        f"<p><strong>{html.escape(label)}.</strong> {html.escape(text)}</p>"
        for label, text in parts
    )
    images = []
    for figure in figures:
        pair = "".join(
            '<div><img alt="'
            + label
            + '" src="data:image/png;base64,'
            + base64.b64encode(data).decode("ascii")
            + '"><small>'
            + label
            + "</small></div>"
            for label, data in [
                ("Source CT", figure.source_png),
                ("Reviewed annotation", figure.overlay_png),
            ]
        )
        images.append(
            '<figure><div class="pair">'
            + pair
            + "</div><figcaption>"
            + html.escape(figure.caption)
            + "</figcaption></figure>"
        )
    if len(payload.get("imaging", [])) > len(figures):
        images.append(
            "<p>Representative images from the first three studies are shown. All accepted studies remain in the evidence package and CT review.</p>"
        )
    return (
        """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; img-src data:; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'">
<title>LOVISA clinical summary</title><style>
body{font:15px/1.55 system-ui,sans-serif;color:#172d3b;background:#f5f7fa;margin:0;padding:28px}main{max-width:900px;margin:auto;background:white;padding:32px;border:1px solid #e0e8ed;border-radius:16px}h1{font-size:26px;margin:0 0 22px}strong{color:#147d73}p{overflow-wrap:anywhere}.notice,small,figcaption{font-size:12px;color:#526773}.pair{display:flex;gap:14px}.pair>div{width:50%}img{display:block;width:100%;max-height:270px;object-fit:contain;background:black;border-radius:8px}figure{margin:24px 0;break-inside:avoid}figcaption{margin-top:8px}@media print{body{background:white;padding:0;font-size:11pt}main{border:0;padding:0}img{max-height:220px}}
</style></head><body><main><h1>Clinical summary</h1>"""
        + paragraphs
        + "".join(images)
        + '<p class="notice">'
        + html.escape(NOTICE)
        + "</p></main></body></html>"
    )
