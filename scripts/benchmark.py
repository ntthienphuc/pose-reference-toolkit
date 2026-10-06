"""Synthetic comparison timings; includes integrity check, excludes extraction."""
import argparse
from dataclasses import asdict
import importlib.metadata as metadata
import json
from pathlib import Path
import platform
import statistics
import tempfile
import time
import numpy as np
from signova_reference.bank import ReferenceBank
from signova_reference.compare import ComparePolicy, compare
from signova_reference.demo import create_demo, sequence

parser = argparse.ArgumentParser()
parser.add_argument("--out", required=True)
parser.add_argument("--repeats", type=int, default=30)
args = parser.parse_args()
if not 5 <= args.repeats <= 1000:
    parser.error("Use 5..1000 repeats")
with tempfile.TemporaryDirectory() as folder:
    root = Path(folder) / "fixture"
    create_demo(root)
    bank = ReferenceBank(root / "bank")
    query = sequence(seed=400)
    measurements = []
    for mode in ("linear", "dtw"):
        policy = ComparePolicy(alignment=mode)
        for _ in range(3):
            compare(query, bank, "SYNTHETIC_HORIZONTAL", policy)
        timings = []
        for _ in range(args.repeats):
            started = time.perf_counter()
            result = compare(query, bank, "SYNTHETIC_HORIZONTAL", policy)
            timings.append((time.perf_counter() - started) * 1000)
        measurements.append({"policy":asdict(policy), "repeats":args.repeats, "warmups":3,
                             "p50_ms":statistics.median(timings), "p95_ms":float(np.percentile(timings,95)),
                             "min_ms":min(timings), "status":result["status"], "raw_ms":timings})
    receipt = {"scope":"synthetic engineering microbenchmark; no video, network, learner accuracy or Jetson claim",
               "python":platform.python_version(), "platform":platform.platform(), "processor":platform.processor(),
               "numpy":metadata.version("numpy"), "bank_sha256":bank.digest, "glosses":2, "references":8,
               "frames":32, "joints":6, "bank_bytes":sum(p.stat().st_size for p in (root/'bank').iterdir()),
               "measurements":measurements}
Path(args.out).parent.mkdir(parents=True, exist_ok=True)
Path(args.out).write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
print(json.dumps({r["policy"]["alignment"]:{"p50_ms":r["p50_ms"],"p95_ms":r["p95_ms"]} for r in measurements},indent=2))
