"""Verify Python modules and browser asset in a built wheel match source bytes."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

parser = argparse.ArgumentParser()
parser.add_argument("--wheel", required=True)
parser.add_argument("--out", required=True)
args = parser.parse_args()
root = Path(__file__).resolve().parents[1] / "src" / "signova_reference"
items = sorted(root.glob("*.py")) + [root / "web.html"]
with zipfile.ZipFile(args.wheel) as wheel:
    for file in items:
        if wheel.read("signova_reference/" + file.name) != file.read_bytes():
            raise SystemExit("Wheel/source mismatch: " + file.name)
receipt = {"status":"passed", "files":len(items), "wheel_sha256":hashlib.sha256(Path(args.wheel).read_bytes()).hexdigest(),
           "assets":[p.name for p in items]}
Path(args.out).parent.mkdir(parents=True, exist_ok=True)
Path(args.out).write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
print(json.dumps(receipt))
