"""Explicit local Endoscopy Agent adapter; bounded CV worker, no LLM or downloads."""

import os
from pathlib import Path
from uuid import uuid4

from pydantic import TypeAdapter

from medical_assistant.endo_contracts import Id
from medical_assistant.endo_contracts.worker import LocalJob
from medical_assistant.storage import ROOT


def configured_endo_root():
    return (
        Path(os.environ.get("LOVISA_ENDO_ROOT", str(ROOT.parent / "AI-MedImg-Endo")))
        .expanduser()
        .resolve()
    )


def configured_endo_model(root=None):
    root = Path(root or configured_endo_root())
    preferred = root / "artifacts/kvasir-research-v2"
    default = (
        preferred
        if (preferred / "registration.json").is_file()
        else root / "artifacts/kvasir-model"
    )
    return (
        Path(os.environ.get("LOVISA_ENDO_MODEL_DIR", str(default)))
        .expanduser()
        .resolve()
    )


class LocalEndoscopyJob(LocalJob):
    def __init__(
        self,
        patient_id,
        *,
        root=None,
        jobs=None,
        mode="fixture",
        model_dir=None,
        backend="onnx-cpu",
        timeout=110,
        image_bytes=None,
        research=None,
    ):
        TypeAdapter(Id).validate_python(patient_id)
        if image_bytes is not None:
            import hashlib

            from medical_assistant.endo_contracts import PublicResearchSource

            provenance = PublicResearchSource.model_validate(research)
            if (
                mode != "installed"
                or not patient_id.startswith("research-composite-")
                or not image_bytes
                or len(image_bytes) > 16 * 1024**2
                or hashlib.sha256(image_bytes).hexdigest() != provenance.original_sha256
            ):
                raise ValueError(
                    "Public image requires installed model, exact provenance and composite case"
                )
        elif research is not None:
            raise ValueError("Research provenance has no source image")
        if (
            mode not in ("fixture", "installed")
            or backend not in ("onnx-cpu", "openvino-cpu", "openvino-npu")
            or (mode == "fixture" and backend != "onnx-cpu")
        ):
            raise ValueError("Unsupported endoscopy mode/backend")
        root = Path(root or configured_endo_root()).resolve()
        python = (
            root / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        )
        if not python.is_file() or not (root / "src/endo/cli.py").is_file():
            raise ValueError(
                "Install the endoscopy companion and its .venv; see docs/ENDOSCOPY.md"
            )
        self.patient_id = patient_id
        self.study_id = "endo-" + uuid4().hex[:16]
        directory = Path(jobs or ROOT / "data/imaging/endo-jobs") / uuid4().hex
        output = directory / "result"
        command = [
            str(python),
            "-m",
            "endo.cli",
            "infer" if image_bytes is not None else "bridge",
            "--patient-id",
            patient_id,
            "--study-id",
            self.study_id,
            "--output",
            str(output),
            "--backend",
            backend,
        ]
        inputs = None
        if image_bytes is not None:
            inputs = {
                "input.image": image_bytes,
                "research.json": provenance.model_dump_json().encode(),
            }
            command += [
                "--image",
                str(directory / "input.image"),
                "--research-provenance",
                str(directory / "research.json"),
                "--research-use-attested",
            ]
        if mode == "installed":
            command += [
                "--model-dir",
                str(
                    Path(model_dir or configured_endo_model(root))
                    .expanduser()
                    .resolve()
                ),
            ]
        super().__init__(
            command,
            cwd=root,
            directory=directory,
            output=output / "bundle.endo.zip",
            timeout=timeout,
            input_files=inputs,
        )
