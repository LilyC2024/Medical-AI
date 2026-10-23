"""Build local upload examples from separately obtained, permitted research datasets.

No downloads, training, clinical approval or linking of real patient histories.
The real CT workspace must already have been produced by the CT companion.
"""

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATIENT = "research-composite-demo"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--ct-root", type=Path, default=ROOT.parent / "ai-medimg-2.5D-CT")
    p.add_argument("--ct-workspace", type=Path, required=True)
    p.add_argument("--endo-root", type=Path, default=ROOT.parent / "AI-MedImg-Endo")
    p.add_argument("--endo-data", type=Path, required=True)
    p.add_argument("--endo-model", type=Path, required=True)
    p.add_argument("--output", type=Path, default=ROOT / "data/research-demo")
    a = p.parse_args()
    a.output = a.output.resolve()
    a.output.mkdir(parents=True, exist_ok=False)
    for name in ("ct_root", "ct_workspace", "endo_root", "endo_data", "endo_model"):
        setattr(a, name, getattr(a, name).resolve())

    def run(root, *args):
        python = (
            root
            / ".venv"
            / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
        )
        subprocess.run([str(python), "-m", *map(str, args)], cwd=root, check=True)

    study = json.loads((a.ct_workspace / "study.json").read_text())
    if (
        study["input_kind"] != "approved-public-research"
        or study["patient_alias"] != "LIDC-IDRI-0002"
    ):
        raise ValueError("This fixed demo requires the LIDC-IDRI-0002 public workspace")
    ct_source = dict(
        dataset="TCIA LIDC-IDRI",
        source_url="https://www.cancerimagingarchive.net/collection/lidc-idri/",
        license="CC BY 3.0",
        research_subject_id="LIDC-IDRI-0002",
        original_sha256=sha(a.ct_workspace / "source.npy"),
        composite_case=True,
    )
    ct_meta = a.output / "ct-provenance.json"
    ct_meta.write_text(json.dumps(ct_source, indent=2))
    original_shape = study["geometry"]["shape_zyx"]
    shape = [min(x, y) for x, y in zip(original_shape, (32, 192, 192))]
    c = study["candidates"][0] if study["candidates"] else None
    center = (
        [(x + y) / 2 for x, y in zip(c["box_zyx"][:3], c["box_zyx"][3:])]
        if c
        else [s / 2 for s in original_shape]
    )
    origin = [
        max(0, min(int(round(c - n / 2)), s - n))
        for c, n, s in zip(center, shape, original_shape)
    ]
    integrity = json.loads((a.ct_workspace / "integrity.json").read_text())
    if "inference_region_zyx" in integrity:
        region = integrity["inference_region_zyx"]
        origin, shape = region[:3], region[3:]
    ct_zip = a.output / "ct-real.mhcra.zip"
    run(
        a.ct_root,
        "lung_nodule.cli",
        "export-research",
        "--workspace",
        a.ct_workspace,
        "--output",
        ct_zip,
        "--patient-id",
        PATIENT,
        "--research-provenance",
        ct_meta,
        "--crop-origin",
        *origin,
        "--shape",
        *shape,
    )
    with zipfile.ZipFile(ct_zip) as archive:
        m = json.loads(archive.read("bundle.json"))
        first = m["study"]["candidates"][0] if m["study"]["candidates"] else None
        z = (
            int((first["box_zyx"][0] + first["box_zyx"][3]) / 2)
            if first
            else shape[0] // 2
        )
        for role in ("source_preview", "overlay_preview"):
            item = next(
                x for x in m["artifacts"] if x["role"] == role and x["slice_index"] == z
            )
            (a.output / f"ct-{role}.png").write_bytes(archive.read(item["path"]))
    frozen = json.loads((a.endo_root / "reports/kvasir-split-v1.json").read_text())
    # Fixed first three manifest test rows; no best-image/Dice selection.
    examples = [r for r in frozen["records"] if r["split"] == "test"][:3]
    endo = []
    for i, row in enumerate(examples, 1):
        source = a.endo_data / row["image"]
        if sha(source) != row["image_sha256"]:
            raise ValueError("Kvasir image differs from frozen manifest")
        raw = a.output / f"endoscopy-{i:02d}.jpg"
        shutil.copyfile(source, raw)
        shutil.copyfile(
            a.endo_data / row["mask"],
            a.output / f"endoscopy-{i:02d}-reference-mask.jpg",
        )
        provenance = dict(
            dataset="Kvasir-SEG",
            source_url="https://datasets.simula.no/kvasir-seg/",
            license="Research/education use; commercial use requires permission",
            research_subject_id="unknown; Kvasir image " + source.stem,
            original_sha256=sha(source),
            composite_case=True,
        )
        meta = a.output / f"endoscopy-{i:02d}-provenance.json"
        meta.write_text(json.dumps(provenance, indent=2))
        workspace = a.output / f"endoscopy-{i:02d}-workspace"
        run(
            a.endo_root,
            "endo.cli",
            "infer",
            "--image",
            raw,
            "--model-dir",
            a.endo_model,
            "--research-use-attested",
            "--research-provenance",
            meta,
            "--patient-id",
            PATIENT,
            "--study-id",
            f"kvasir-real-{i:02d}",
            "--output",
            workspace,
        )
        bundle = a.output / f"endoscopy-{i:02d}.endo.zip"
        shutil.copyfile(workspace / "bundle.endo.zip", bundle)
        endo.append(
            dict(
                file=bundle.name,
                sha256=sha(bundle),
                raw=raw.name,
                raw_sha256=sha(raw),
                provenance=provenance,
                reference=row["image"],
                manifest_partition="test",
            )
        )
    manifest = dict(
        schema_version="lovisa-research-demo-v1",
        patient_id=PATIENT,
        composite_notice="Fictional history; unrelated CT and endoscopy research subjects. No common disease is inferred.",
        ct=dict(
            file=ct_zip.name,
            sha256=sha(ct_zip),
            provenance=ct_source,
            crop_origin_zyx=origin,
            shape_zyx=shape,
            coverage="CT excerpt only, not the whole scan",
            inference_region_zyx=integrity.get(
                "inference_region_zyx", [0, 0, 0, *original_shape]
            ),
            selection="Annotation-selected ROI; rest not analysed"
            if "inference_region_zyx" in integrity
            else "Model-ranked crop after full-source inference",
        ),
        endoscopy=endo,
    )
    (a.output / "examples.json").write_text(json.dumps(manifest, indent=2))
    (a.output / "README.txt").write_text(
        "LOVISA real-image research examples\n\nSign in and select Jordan — real-image research composite.\n"
        "CT review: Upload ct-real.mhcra.zip, then Analyze. Endoscopy review: Upload endoscopy-01.endo.zip or endoscopy-01.jpg, then Analyze.\n"
        "Inspect each proposed region and explicitly include the study. Then complete Safety check and generate the report.\n"
        "These images are from unrelated research subjects. The CT ZIP contains a limited source-mapped excerpt, not a full scan.\n"
        "ct-source_preview.png is for viewing only: PNG screenshots cannot replace DICOM HU/geometry for CT inference.\n"
        "Reference masks are dataset annotations, never model predictions or histology. Kvasir subject independence is unknown.\n"
        "Sources/licenses and hashes: examples.json. Original acquisition dates are not inferred from deidentified DICOM dates.\n"
    )
    print("Upload kit ready:", a.output)


if __name__ == "__main__":
    main()
