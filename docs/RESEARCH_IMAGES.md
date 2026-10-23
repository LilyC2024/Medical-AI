# Real research images and the composite demo

[Overview](../README.md) · [CT review](IMAGING.md) · [Endoscopy review](ENDOSCOPY.md)

LOVISA keeps patient histories fictional. This extension permits **deidentified
public research images** in the separate **Jordan — real-image research composite**
case. Its CT and endoscopy images come from unrelated research subjects. They are
never represented as one real patient, a shared disease or evidence explaining
the fictional symptoms. Image dates and absent clinical measurements stay unknown.

## Upload examples

After local preparation, `data/research-demo/README.txt` and `examples.json` list
all upload files, source identities, hashes and terms. Sign in, select Jordan and
use **Upload → Analyze** in the matching imaging view:

| File | Use |
| --- | --- |
| `ct-real.mhcra.zip` | CT review: source HU excerpt, model candidates and annotations |
| `ct-source_preview.png` | View a real CT slice; PNG is **not** a CT detector input |
| `endoscopy-01.jpg` through `endoscopy-03.jpg` | Re-run the local polyp model on these actual research images |
| `endoscopy-01.endo.zip` through `endoscopy-03.endo.zip` | Inspect prepared source/prediction evidence immediately |
| `endoscopy-01-reference-mask.jpg` etc. | Dataset annotation for comparison; never a model result or histology |

A review ZIP opens its included predictions; it is not new inference. An uploaded
permitted JPG/PNG runs the installed polyp model. To open the prepared example
without a file, choose **Local research example** under **Model / example** and
Analyze. Adding images after a report starts opens a fresh unreviewed context and
requires safety review again.

The three endoscopy images are the **first three frozen test-manifest rows**,
selected without ranking their model results. Include a CT and endoscopy study
before generating a new report. Every candidate needs an include/exclude decision;
image acceptance, the safety assessment and final report approval are separate.
Notes are optional. A checked confirmation alone submits nothing.

The CT bundle covers a **32 × 96 × 96 voxel excerpt**, with original source-slice
hashes and a physical-coordinate mapping. The fixed ROI was selected from the first source-matched public reader contour
before inference; this is a localization demonstration, not a detection benchmark.
Only the declared ROI was analysed. Predictions wholly
inside the crop are retained; overlapping/outside candidates are not depicted.
No resampling, guessed geometry or full-scan coverage is claimed. Original DICOM
files remain in the external dataset directory. The source PNG is for viewing;
CT inference requires the DICOM/HU volume and geometry, not a screenshot.

## Sources and permission

- CT: [TCIA LIDC-IDRI](https://www.cancerimagingarchive.net/collection/lidc-idri/),
  research subject **LIDC-IDRI-0002**, CC BY 3.0. Credit the collection and its
  published dataset DOI. The fixed public download uses the [official NBIA API](https://wiki.cancerimagingarchive.net/display/Public/NBIA%2BSearch%2BREST%2BAPI%2BGuide).
  Deidentified DICOM dates do not establish actual acquisition dates. Contrast
  status is not supplied; this is a **protocol-unverified research smoke**.
- Endoscopy: [Simula Kvasir-SEG](https://datasets.simula.no/kvasir-seg/).
  Current dataset terms permit research/education and require permission for
  commercial use. These are publicly available research images, not a blanket
  commercial-use asset library. Subject identifiers/independence are unknown.

Dataset pixels, reference masks, model weights, local accounts and reports are
excluded from Git. Setup scripts generate the local kit; no inference-time
network access or remote model inference is introduced. Original JPEG/DICOM
sources remain separate from canonical source pixels and predictions.

## Reproduce the CT experiment

In the CT checkout, with its existing `.venv` and registered MONAI weights:

```bash
.venv/bin/python scripts/fetch_lidc_demo.py --output /absolute/path/LIDC-IDRI-0002 --accept-public-data-terms
.venv/bin/python -m lung_nodule.cli detect --series /absolute/path/LIDC-IDRI-0002/series --approval /absolute/path/LIDC-IDRI-0002/approval.json --model-dir models/luna16-full --device cpu --threads 4 --patient-alias LIDC-IDRI-0002 --study-id lidc0002-real --output artifacts/lidc0002-excerpt32-real --inference-region 168 313 300 32 96 96
.venv/bin/python scripts/evaluate_public_lidc.py --workspace artifacts/lidc0002-excerpt32-real --xml /absolute/path/LIDC-IDRI-0002/annotations.xml --output reports/lidc0002-localization.json
```

An attempted full-scan CPU run was stopped after roughly 28 minutes. The actual
32×96×96 excerpt run took **11.98 seconds**; it does not cover the rest of the scan.
Full-scan CPU inference is **offline preparation** and can take many minutes;
it is not a two-minute interactive operation. The UI opens the bounded prepared
bundle quickly. Existing interactive workers still stop at 110 seconds.

The XML evaluation compares predicted centers to individual readers' contour
boxes with a declared 2-mm margin. It does not merge readers into consensus,
use malignancy ratings as pathology or claim official LUNA scoring. Pretrained
LUNA/LIDC overlap is possible; this scan is not an independent accuracy benchmark.

Full RetinaNet training remains the CT companion's CUDA workflow, requiring the
upstream 16-GB GPU gate and a larger subject-separated dataset. This host has no
CUDA device, so **no full CT training was performed here**. See the companion's
[training guide](https://github.com/LilyC2024/ai-medimg-2.5D-CT/blob/main/docs/lung/training.md).

## Reproduce endoscopy training and build the kit

In the endoscopy checkout, after obtaining permitted Kvasir-SEG data and using
the committed frozen split:

```bash
.venv/bin/python -m endo.cli train --data /absolute/path/Kvasir-SEG --manifest reports/kvasir-split-v1.json --output artifacts/kvasir-research-v2 --epochs 24 --size 128 --base 8 --threads 4
.venv/bin/python -m endo.cli export-model --model-dir artifacts/kvasir-research-v2
.venv/bin/python -m endo.cli evaluate --model-dir artifacts/kvasir-research-v2 --data /absolute/path/Kvasir-SEG --manifest reports/kvasir-split-v1.json --output reports/kvasir-research-v2-evaluation.json
```

The checkpoint is selected by validation loss. This is a repeat experiment on a
previously examined test split: mean positive-image Dice 0.544 and IoU 0.413 over
168 images, without negative examinations or established patient independence.
These limitations prevent a clinical detection/specificity claim. The model is
not trained to diagnose cancer. The local runtime prefers the registered v2
model when available; `LOVISA_ENDO_MODEL_DIR` can select another explicit model.

Then, in LOVISA (use a new output directory if rebuilding):

```bash
.venv/bin/python scripts/prepare_research_demo.py --ct-workspace ../ai-medimg-2.5D-CT/artifacts/lidc0002-excerpt32-real --endo-data /absolute/path/Kvasir-SEG --endo-model ../AI-MedImg-Endo/artifacts/kvasir-research-v2
```

This script creates upload evidence only. It does not approve images, override
safety, publish patient records or approve a report.

## Evidence contracts

Synthetic CT-v2 and endoscopy-v1 retain their previous restrictions. Separate
`lovisa-ct-research-v3` and `lovisa-endo-research-v2` schemas require
`synthetic: false`, public provenance and a `research-composite-` case ID.
The CT schema additionally validates exact crop geometry, source-slice mapping,
model identity and enclosed predicted boxes against the original study metadata.
Both consumers reconstruct annotations from their actual source arrays/maps.
Hashes establish internal consistency, not independent proof of dataset origin,
producer execution or model accuracy. The exporter verifies original byte hashes;
the consumer cannot inspect original full-scan/JPEG files absent from a bundle.

Research CT additionally binds `inference_region_zyx` (origin Z/Y/X then depth/height/width). The consumer rejects crops/predictions outside the declared analysed region. No claim of full-scan inference is inferred from full-source metadata.
