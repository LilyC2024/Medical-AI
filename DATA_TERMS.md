# Dataset and model terms

The [MIT license](LICENSE) covers this repository's source code only. It grants no
rights to datasets, research images, reference masks, model weights or patient
data, and does not certify fitness or regulatory approval for clinical use. LOVISA is educational/research software,
not a diagnostic device.

No dataset pixels, masks or weights are committed. Anyone who downloads them must
accept and follow the publisher's current terms themselves:

| Source | Used for | Terms as documented here (check the publisher before use) |
| --- | --- | --- |
| [TCIA LIDC-IDRI](https://www.cancerimagingarchive.net/collection/lidc-idri/) | Real-image composite demo (subject LIDC-IDRI-0002) via the CT companion | CC BY 3.0 and the TCIA data usage policy; credit the collection and its dataset DOI |
| [Simula Kvasir-SEG](https://datasets.simula.no/kvasir-seg/) | Real-image composite demo via the endoscopy companion | Research/education use; commercial use requires the publisher's permission |
| [MONAI lung_nodule_ct_detection bundle](https://github.com/Project-MONAI/model-zoo/tree/dev/models/lung_nodule_ct_detection) | Pretrained RetinaNet weights used by the CT companion | Upstream license files are kept beside downloaded weights by `fetch-model`; weights are trained on LUNA16 (derived from LIDC-IDRI) |

Fictional histories in this repository are authored for testing and carry the
repository's MIT license. A fictional flag does not prove absence of personal data;
see [Security](SECURITY.md). Third-party code notices: [third_party](third_party/README.md).
