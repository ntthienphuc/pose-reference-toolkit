"""Inventory installed distribution license metadata; not a legal clearance."""
import argparse
import importlib.metadata as metadata
import json
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--out", required=True)
args = parser.parse_args()
rows = []
for dist in sorted(metadata.distributions(), key=lambda d: d.metadata.get("Name", "").lower()):
    files = [str(f) for f in (dist.files or []) if any(part in str(f).lower() for part in ("license", "notice", "copying"))]
    rows.append({"name": dist.metadata.get("Name"), "version": dist.version,
                 "license_expression": dist.metadata.get("License-Expression"), "license": dist.metadata.get("License"),
                 "license_files": files})
Path(args.out).parent.mkdir(parents=True, exist_ok=True)
Path(args.out).write_text(json.dumps({"scope":"installed metadata only; inspect upstream and binary notices", "distributions":rows}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
