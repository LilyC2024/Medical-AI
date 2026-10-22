"""Real local CT worker and receiver; no human or final approval is simulated."""
import argparse
import json
import sys
import time
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from medical_assistant.ct_worker import LocalCTJob, configured_ct_root
from medical_assistant.database import seed
from medical_assistant.imaging import ImagingStore


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ct-root", type=Path, default=configured_ct_root())
    args = parser.parse_args()
    with TemporaryDirectory(prefix="mhcra-imaging-smoke-") as tmp:
        root = Path(tmp)
        path = root / "synthetic.sqlite3"
        seed(path)
        job = LocalCTJob("synthetic-checklist", root=args.ct_root, jobs=root / "jobs")
        print("Running real generated-synthetic CT worker locally…", flush=True)
        try:
            while job.status() == "running":
                time.sleep(0.2)
            if job.status() != "complete":
                raise RuntimeError(job.error + "\n" + job.log_path.read_text()[-4000:])
            store = ImagingStore(path)
            key, proposal = store.prepare(job.bundle_path.read_bytes(), job.patient_id, study_id=job.study_id)
            assert not store.snapshots(job.patient_id)
            manifest = proposal["manifest"]
            print(json.dumps({"status": "PASS", "source_shape_zyx": manifest["geometry"]["shape_zyx"],
                              "voxel_counts": manifest["voxel_counts"], "artifacts": len(manifest["artifacts"]),
                              "producer_reports_onnx_parity": manifest["onnx_parity_passed"],
                              "imaging_approved": False, "final_report_approved": False}), flush=True)
            store.discard(key)
        finally:
            job.cancel()


if __name__ == "__main__":
    main()
