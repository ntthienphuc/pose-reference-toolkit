"""Audited reference construction with explicit role separation and hashed assets."""
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import warnings
import numpy as np
from .pose import QualityConfig, load_pose, prepare_pose, required_indexes, strict_json, write_json


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def inside(root, relative):
    relative = Path(relative)
    if relative.is_absolute():
        raise ValueError("Artifact paths must be relative")
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError("Artifact path escapes its root")
    return path


def audit_manifest(path):
    path = Path(path)
    doc = strict_json(path.read_text(encoding="utf-8-sig"))
    if not isinstance(doc, dict) or set(doc) != {"schema_version", "samples"} or type(doc["schema_version"]) is not int or doc["schema_version"] != 1:
        raise ValueError("Source manifest schema mismatch")
    rows = doc["samples"]
    if not isinstance(rows, list) or not 1 <= len(rows) <= 10000:
        raise ValueError("Source sample count must be in [1,10000]")
    ids, groups, speakers, contents, pose_contents = {}, {}, {}, {}, {}
    prepared = []
    for row in rows:
        required = {"id", "gloss", "path", "kind", "role", "source_group", "license", "authorized"}
        optional = {"speaker_id", "speaker_verified"}
        if not isinstance(row, dict) or not required.issubset(row) or set(row) - required - optional:
            raise ValueError("Sample schema mismatch")
        for field in ("id", "gloss", "path", "source_group", "license"):
            if not isinstance(row[field], str) or not row[field] or len(row[field]) > 1024:
                raise ValueError("Sample field must be a nonempty string: " + field)
        if row["authorized"] is not True or row["role"] not in {"reference", "calibration", "evaluation"} or row["kind"] not in {"pose", "video"}:
            raise ValueError("Unsupported role/kind or missing user-declared permission")
        if row["id"] in ids:
            raise ValueError("Duplicate sample ID")
        ids[row["id"]] = row["role"]
        file = inside(path.parent, row["path"])
        if not file.is_file():
            raise ValueError("Missing source file for sample " + row["id"])
        digest = sha256(file)
        content = contents.get(digest)
        if content:
            if content["gloss"] != row["gloss"]:
                raise ValueError("Identical source bytes have conflicting labels")
            raise ValueError("Duplicate source content, including across roles")
        contents[digest] = row
        pose_fingerprint = None
        if row["kind"] == "pose":
            # Representation-invariant duplicate check; this does not detect
            # visually similar videos or prove capture/signer independence.
            try:
                seq = load_pose(file)
                canonical = seq.to_dict()
                canonical["timestamps_ms"] = (seq.timestamps_ms - seq.timestamps_ms[0]).tolist()
                fingerprint = hashlib.sha256(json.dumps(canonical, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()
                if fingerprint in pose_contents:
                    raise ValueError("Duplicate canonical pose content")
                pose_contents[fingerprint] = row["id"]
                pose_fingerprint = fingerprint
            except (ValueError, OSError) as error:
                if "Duplicate canonical" in str(error):
                    raise
                # Malformed source is logged by the role-specific build/check,
                # so one bad reference can be excluded rather than hiding it.
        prior = groups.setdefault(row["source_group"], row["role"])
        if prior != row["role"]:
            raise ValueError("Source group overlaps roles")
        if "speaker_verified" in row and type(row["speaker_verified"]) is not bool:
            raise ValueError("speaker_verified must be boolean")
        if row.get("speaker_verified"):
            speaker = row.get("speaker_id")
            if not isinstance(speaker, str) or not speaker:
                raise ValueError("Verified speaker requires an ID")
            if speakers.setdefault(speaker, row["role"]) != row["role"]:
                raise ValueError("Declared verified speaker overlaps roles")
        prepared.append({**row, "sha256": digest, "pose_sha256": pose_fingerprint, "resolved_path": file})
    return prepared, {"status": "passed", "samples": len(rows), "manifest_sha256": sha256(path),
                      "partition_scope": "user-declared-verified-speakers" if all(r.get("speaker_verified") for r in rows) else "source-groups-only",
                      "roles": {role: sum(r["role"] == role for r in rows) for role in ("reference", "calibration", "evaluation")},
                      "rights_scope": "user declaration, not independent verification"}


def read_sample(row):
    if sha256(row["resolved_path"]) != row["sha256"]:
        raise ValueError("Source changed after manifest audit")
    if row["kind"] == "pose":
        return load_pose(row["resolved_path"])
    from .video import extract_video
    return extract_video(row["resolved_path"])


def build_bank(manifest_path, output, target_len=32, required_groups=("body", "left_hand", "right_hand"),
               quality=QualityConfig(), tolerance_quantile=0.85, tolerance_floor=0.08,
               tolerance_margin=0.03, tolerance_cap=0.25):
    if type(target_len) is not int or not 8 <= target_len <= 256:
        raise ValueError("target_len must be in [8,256]")
    if not 0 < tolerance_quantile <= 1 or not 0 < tolerance_floor <= tolerance_cap or tolerance_margin < 0 or not np.isfinite([tolerance_quantile, tolerance_floor, tolerance_margin, tolerance_cap]).all():
        raise ValueError("Invalid tolerance settings")
    output = Path(output)
    if output.exists():
        raise ValueError("Bank destination already exists; build a new version")
    rows, audit = audit_manifest(manifest_path)
    references = [row for row in rows if row["role"] == "reference"]
    if not references:
        raise ValueError("Manifest has no reference samples")
    accepted, excluded, contract = {}, [], None
    for row in references:
        try:
            seq = read_sample(row)
            tensor, report = prepare_pose(seq, target_len, required_groups, quality)
            if not report["passed"]:
                excluded.append({"id": row["id"], "gloss": row["gloss"], "quality": report})
                continue
            if contract is None:
                contract = seq.contract
            if seq.contract != contract:
                raise ValueError("Reference pose contract mismatch")
            accepted.setdefault(row["gloss"], []).append((row, tensor, report))
        except (OSError, ValueError, ImportError, RuntimeError) as error:
            excluded.append({"id": row["id"], "gloss": row["gloss"], "error": str(error)})
    expected = sorted({r["gloss"] for r in references})
    failures = [gloss for gloss in expected if not 2 <= len(accepted.get(gloss, [])) <= 64]
    if failures:
        raise ValueError("Each gloss needs 2..64 accepted references: " + ", ".join(failures) + "; exclusions=" + json.dumps(excluded))
    indexes = required_indexes(contract, required_groups)
    output.parent.mkdir(parents=True, exist_ok=True)
    temp = Path(tempfile.mkdtemp(prefix=".signova-build-", dir=output.parent))
    try:
        profile = {"schema_version": 1, "contract": contract, "target_len": target_len, "required_groups": list(required_groups),
                   "quality": asdict(quality), "tolerance": {"quantile": tolerance_quantile, "floor": tolerance_floor,
                   "margin": tolerance_margin, "cap": tolerance_cap}, "metric": "coherent-template-xy-v1"}
        write_json(temp / "profile.json", profile)
        entries = []
        for i, gloss in enumerate(expected):
            items = accepted[gloss]
            stack = np.stack([item[1] for item in items])
            support = np.isfinite(stack).all(axis=-1).mean(axis=0)
            if np.any(support[:, indexes] < 0.5):
                raise ValueError("Reference bank has unsupported required cells: " + gloss)
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", RuntimeWarning)
                median = np.nanmedian(stack, axis=0)
                deviations = np.linalg.norm(stack - median[None], axis=-1)
                raw_tolerance = np.nanquantile(deviations, tolerance_quantile, axis=0) + tolerance_margin
            tolerance = np.clip(np.where(np.isfinite(raw_tolerance), raw_tolerance, tolerance_floor), tolerance_floor, tolerance_cap)
            file = "gloss_%03d.npz" % i
            np.savez_compressed(temp / file, templates=stack, tolerance=tolerance.astype(np.float32))
            medoid_costs = []
            for ref in stack:
                distances = np.linalg.norm(stack[:, :, indexes] - ref[None, :, indexes], axis=-1)
                medoid_costs.append(float(np.where(np.isfinite(distances), distances, 5).mean()))
            entries.append({"gloss": gloss, "file": file, "sha256": sha256(temp / file),
                            "reference_ids": [item[0]["id"] for item in items], "medoid_reference_id": items[int(np.argmin(medoid_costs))][0]["id"],
                            "reference_source_sha256": [item[0]["sha256"] for item in items],
                            "reference_pose_sha256": [item[0]["pose_sha256"] for item in items],
                            "tolerance_clipped_fraction": float((raw_tolerance[:, indexes] > tolerance_cap).mean()),
                            "minimum_required_cell_support": float(support[:, indexes].min())})
        from importlib.metadata import version
        recipe = {"numpy": version("numpy"), "toolkit": "0.1.0", "pose_import": "explicit-json-or-nonpickled-npz-v1"}
        if any(r["kind"] == "video" for r in references):
            recipe["video_adapter"] = {"mediapipe": version("mediapipe"), "opencv": version("opencv-contrib-python"),
                                       "frame_stride": 2, "model_complexity": 1, "timestamp": "frame-index-divided-by-fps",
                                       "hand_confidence": "presence-only", "variable_frame_rate": "unsupported"}
        write_json(temp / "build_report.json", {"audit": audit, "reference_samples_only": True, "recipe": recipe,
                   "accepted": [{"id": row["id"], "gloss": row["gloss"], "source_sha256": row["sha256"], "source_group": row["source_group"],
                                 "license": row["license"], "quality": report, "speaker_id": row.get("speaker_id"),
                                 "speaker_verified": row.get("speaker_verified", False)} for items in accepted.values() for row, _, report in items],
                   "excluded": excluded})
        manifest = {"schema_version": 1, "profile_sha256": sha256(temp / "profile.json"),
                    "build_report_sha256": sha256(temp / "build_report.json"), "glosses": entries}
        write_json(temp / "manifest.json", manifest)
        ReferenceBank(temp)
        temp.rename(output)
    finally:
        if temp.exists():
            assert temp.resolve().parent == output.parent.resolve() and temp.name.startswith(".signova-build-")
            shutil.rmtree(temp)
    return {"status": "passed", "glosses": len(expected), "accepted_references": sum(len(v) for v in accepted.values()),
            "excluded_references": len(excluded), "bank_sha256": sha256(output / "manifest.json"), "audit": audit}


class ReferenceBank:
    def __init__(self, root):
        self.root = Path(root)
        self.digest = sha256(self.root / "manifest.json")
        self.manifest = strict_json((self.root / "manifest.json").read_text(encoding="utf-8"))
        if set(self.manifest) != {"schema_version", "profile_sha256", "build_report_sha256", "glosses"} or self.manifest["schema_version"] != 1:
            raise ValueError("Bank manifest schema mismatch")
        self.assert_integrity()
        self.profile = strict_json((self.root / "profile.json").read_text(encoding="utf-8"))
        profile_fields = {"schema_version", "contract", "target_len", "required_groups", "quality", "tolerance", "metric"}
        if set(self.profile) != profile_fields or self.profile["schema_version"] != 1 or self.profile["metric"] != "coherent-template-xy-v1":
            raise ValueError("Unsupported bank profile")
        self.quality = QualityConfig(**self.profile["quality"])
        contract = self.profile["contract"]
        dummy = {"schema_version": 1, "names": contract["names"], "groups": contract["groups"],
                 "coordinate_space": contract["coordinate_space"], "mirror": contract["mirror"],
                 "xy": np.zeros((1, len(contract["names"]), 2)), "confidence": np.zeros((1, len(contract["names"]))), "timestamps_ms": [0]}
        from .pose import PoseSequence
        if PoseSequence.from_dict(dummy).contract != contract:
            raise ValueError("Bank pose contract mismatch")
        self.report = strict_json((self.root / "build_report.json").read_text(encoding="utf-8"))
        self.reference_groups = {row["source_group"] for row in self.report["accepted"]}
        self.reference_speakers = {row["speaker_id"] for row in self.report["accepted"] if row["speaker_verified"]}
        self.required = required_indexes(self.profile["contract"], self.profile["required_groups"])
        self.entries = {}
        for item in self.manifest["glosses"]:
            if item["gloss"] in self.entries:
                raise ValueError("Duplicate bank gloss")
            file = inside(self.root, item["file"])
            import zipfile
            with zipfile.ZipFile(file) as archive:
                if sum(i.file_size for i in archive.infolist()) > 100_000_000:
                    raise ValueError("Expanded bank array limit exceeded")
            with np.load(file, allow_pickle=False) as arrays:
                if set(arrays.files) != {"templates", "tolerance"}:
                    raise ValueError("Bank array schema mismatch")
                templates, tolerance = arrays["templates"].copy(), arrays["tolerance"].copy()
            length = self.profile["target_len"]
            joints = len(self.profile["contract"]["names"])
            if not 8 <= length <= 256 or templates.shape != (len(item["reference_ids"]), length, joints, 2) or not 2 <= len(templates) <= 64:
                raise ValueError("Bank template shape mismatch")
            if len(set(item["reference_ids"])) != len(templates) or tolerance.shape != (length, joints) or not np.isfinite(tolerance).all() or np.any(tolerance <= 0) or np.isinf(templates).any():
                raise ValueError("Invalid bank metadata/tolerance")
            templates.setflags(write=False)
            tolerance.setflags(write=False)
            self.entries[item["gloss"]] = {**item, "templates": templates, "tolerance": tolerance}
        if not self.entries:
            raise ValueError("Empty bank")

    def assert_integrity(self):
        if sha256(self.root / "manifest.json") != self.digest:
            raise ValueError("Bank manifest changed; reload a deliberate new version")
        for file, digest in (("profile.json", self.manifest["profile_sha256"]), ("build_report.json", self.manifest["build_report_sha256"])):
            if sha256(self.root / file) != digest:
                raise ValueError("Bank asset checksum mismatch")
        for item in self.manifest["glosses"]:
            if sha256(inside(self.root, item["file"])) != item["sha256"]:
                raise ValueError("Bank template checksum mismatch")
