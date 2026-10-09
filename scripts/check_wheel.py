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
project = Path(__file__).resolve().parents[1]
root = project / "src" / "pose_reference"
license_bytes = (project / "LICENSE").read_bytes()
if (project / "Licence.txt").read_bytes() != license_bytes:
    raise SystemExit("Licence.txt must be byte-identical to LICENSE")
items = sorted(root.glob("*.py")) + [root / "web.html"]
with zipfile.ZipFile(args.wheel) as wheel:
    for name in ("LICENSE", "Licence.txt"):
        matches = [p for p in wheel.namelist() if p.endswith(".dist-info/licenses/" + name)]
        if len(matches) != 1 or wheel.read(matches[0]) != license_bytes:
            raise SystemExit("Wheel license missing or mismatched: " + name)
    for file in items:
        if wheel.read("pose_reference/" + file.name) != file.read_bytes():
            raise SystemExit("Wheel/source mismatch: " + file.name)
receipt = {"status":"passed", "files":len(items), "wheel_sha256":hashlib.sha256(Path(args.wheel).read_bytes()).hexdigest(),
           "assets":[p.name for p in items], "license_copies_identical": True}
Path(args.out).parent.mkdir(parents=True, exist_ok=True)
Path(args.out).write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
print(json.dumps(receipt))
