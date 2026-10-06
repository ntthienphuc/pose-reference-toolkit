"""Explicit pose contracts, quality gates and observation-preserving resampling."""
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import numpy as np


def strict_json(text):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("Duplicate JSON key: " + key)
            result[key] = value
        return result
    def forbidden(value):
        raise ValueError("Non-finite JSON constant: " + value)
    return json.loads(text, object_pairs_hook=pairs, parse_constant=forbidden)


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")


@dataclass(frozen=True)
class QualityConfig:
    min_confidence: float = 0.5
    min_frames: int = 8
    min_anchor_coverage: float = 0.8
    min_group_coverage: float = 0.8
    max_missing_run_fraction: float = 0.25
    max_frame_gap_ms: float = 250

    def __post_init__(self):
        for key in ("min_confidence", "min_anchor_coverage", "min_group_coverage", "max_missing_run_fraction"):
            value = getattr(self, key)
            if isinstance(value, bool) or not np.isfinite(value) or not 0 < value <= 1:
                raise ValueError(key + " must be finite in (0,1]")
        if type(self.min_frames) is not int or not 2 <= self.min_frames <= 2000:
            raise ValueError("min_frames must be an integer in [2,2000]")
        if not np.isfinite(self.max_frame_gap_ms) or not 0 < self.max_frame_gap_ms <= 60000:
            raise ValueError("Invalid maximum frame gap")


@dataclass(frozen=True)
class PoseSequence:
    xy: np.ndarray
    confidence: np.ndarray
    timestamps_ms: np.ndarray
    names: tuple
    groups: dict
    coordinate_space: str = "pixel_xy"
    mirror: str = "unmirrored"

    def __post_init__(self):
        xy = np.array(self.xy, dtype=np.float64, copy=True)
        confidence = np.array(self.confidence, dtype=np.float64, copy=True)
        times = np.array(self.timestamps_ms, dtype=np.float64, copy=True)
        names = tuple(self.names)
        if xy.ndim != 3 or xy.shape[2] != 2 or not 1 <= xy.shape[0] <= 2000 or not 3 <= xy.shape[1] <= 128:
            raise ValueError("xy must have shape [1..2000,3..128,2]")
        if confidence.shape != xy.shape[:2] or times.shape != (len(xy),):
            raise ValueError("Confidence/timestamp shape mismatch")
        if not np.isfinite(confidence).all() or np.any((confidence < 0) | (confidence > 1)):
            raise ValueError("Confidence must be finite in [0,1]")
        if not np.isfinite(times).all() or np.any(times < 0) or np.any(np.diff(times) <= 0):
            raise ValueError("Timestamps must be finite, nonnegative and strictly increasing")
        if np.isinf(xy).any() or not np.isfinite(xy[confidence > 0]).all():
            raise ValueError("Observed coordinates must be finite; missing coordinates need zero confidence")
        if len(names) != xy.shape[1] or len(set(names)) != len(names) or any(not isinstance(n, str) or not n or len(n) > 120 for n in names):
            raise ValueError("Ordered joint names must be unique nonempty strings")
        if not {"pose_left_shoulder", "pose_right_shoulder"}.issubset(names):
            raise ValueError("Shoulder anchors are required")
        if not isinstance(self.groups, dict) or not self.groups or any(not isinstance(k, str) or not k for k in self.groups):
            raise ValueError("Explicit joint groups are required")
        indexes = []
        groups = {}
        for group, ids in self.groups.items():
            if not isinstance(ids, (list, tuple)) or not ids or any(type(i) is not int or not 0 <= i < len(names) for i in ids):
                raise ValueError("Invalid joint group indexes")
            groups[group] = list(ids)
            indexes.extend(ids)
        if sorted(indexes) != list(range(len(names))):
            raise ValueError("Groups must partition all joints exactly once")
        if self.coordinate_space not in {"pixel_xy", "cartesian_xy"} or self.mirror not in {"unmirrored", "mirrored"}:
            raise ValueError("Unsupported coordinate/mirror contract")
        for array in (xy, confidence, times):
            array.setflags(write=False)
        for key, value in (("xy", xy), ("confidence", confidence), ("timestamps_ms", times), ("names", names), ("groups", groups)):
            object.__setattr__(self, key, value)

    @property
    def contract(self):
        return {"names": list(self.names), "groups": self.groups, "coordinate_space": self.coordinate_space,
                "mirror": self.mirror, "normalization": "shoulder-center-median-scale-v1"}

    def to_dict(self):
        xy = self.xy.astype(object)
        xy[~np.isfinite(self.xy)] = None
        return {"schema_version": 1, "xy": xy.tolist(), "confidence": self.confidence.tolist(),
                "timestamps_ms": self.timestamps_ms.tolist(), "names": list(self.names), "groups": self.groups,
                "coordinate_space": self.coordinate_space, "mirror": self.mirror}

    @classmethod
    def from_dict(cls, document):
        fields = {"schema_version", "xy", "confidence", "timestamps_ms", "names", "groups", "coordinate_space", "mirror"}
        if not isinstance(document, dict) or set(document) != fields or type(document["schema_version"]) is not int or document["schema_version"] != 1:
            raise ValueError("Pose schema fields/version mismatch")
        return cls(**{k: v for k, v in document.items() if k != "schema_version"})


def load_pose(path):
    path = Path(path)
    if path.stat().st_size > 20_000_000:
        raise ValueError("Pose file exceeds 20 MB")
    if path.suffix.lower() == ".json":
        return PoseSequence.from_dict(strict_json(path.read_text(encoding="utf-8-sig")))
    if path.suffix.lower() == ".npz":
        import zipfile
        with zipfile.ZipFile(path) as archive:
            if sum(i.file_size for i in archive.infolist()) > 30_000_000:
                raise ValueError("Expanded pose archive exceeds limit")
        with np.load(path, allow_pickle=False) as arrays:
            if set(arrays.files) != {"xy", "confidence", "timestamps_ms", "metadata"}:
                raise ValueError("NPZ pose schema mismatch")
            metadata = strict_json(str(arrays["metadata"].item()))
            return PoseSequence.from_dict({**metadata, "xy": arrays["xy"], "confidence": arrays["confidence"], "timestamps_ms": arrays["timestamps_ms"]})
    raise ValueError("Pose input must be explicit JSON or NPZ, or extracted from video")


def required_indexes(contract, required_groups):
    if not required_groups or len(set(required_groups)) != len(required_groups) or any(g not in contract["groups"] for g in required_groups):
        raise ValueError("Required groups must be unique declared groups")
    return sorted(i for group in required_groups for i in contract["groups"][group])


def longest_run(values):
    longest = current = 0
    for value in values:
        current = current + 1 if value else 0
        longest = max(longest, current)
    return longest


def prepare_pose(seq, target_len, required_groups, quality=QualityConfig()):
    if type(target_len) is not int or not 8 <= target_len <= 256:
        raise ValueError("target_len must be in [8,256]")
    required = required_indexes(seq.contract, required_groups)
    observed = np.isfinite(seq.xy).all(axis=2) & (seq.confidence >= quality.min_confidence)
    left, right = [seq.names.index(n) for n in ("pose_left_shoulder", "pose_right_shoulder")]
    widths = np.linalg.norm(seq.xy[:, left] - seq.xy[:, right], axis=1)
    anchors = observed[:, left] & observed[:, right] & np.isfinite(widths) & (widths > 1e-6)
    observed &= anchors[:, None]
    reasons = []
    if len(seq.xy) < quality.min_frames:
        reasons.append("too_few_frames")
    if len(seq.timestamps_ms) > 1 and np.diff(seq.timestamps_ms).max() > quality.max_frame_gap_ms:
        reasons.append("timestamp_gap")
    if anchors.mean() < quality.min_anchor_coverage:
        reasons.append("insufficient_shoulders")
    coverage = {g: float(observed[:, seq.groups[g]].mean()) for g in required_groups}
    for group, value in coverage.items():
        if value < quality.min_group_coverage:
            reasons.append("insufficient_group:" + group)
    if any(longest_run(~observed[:, j]) / len(seq.xy) > quality.max_missing_run_fraction for j in required):
        reasons.append("long_tracking_gap")
    report = {"passed": not reasons, "reasons": reasons, "frames": len(seq.xy), "anchor_coverage": float(anchors.mean()),
              "required_group_coverage": coverage, "config": asdict(quality)}
    if reasons:
        return None, report
    scale = np.median(widths[anchors])
    center = (seq.xy[:, left] + seq.xy[:, right]) / 2
    normalized = (seq.xy - center[:, None]) / scale
    normalized[~observed] = np.nan
    dst = np.linspace(seq.timestamps_ms[0], seq.timestamps_ms[-1], target_len)
    hi = np.searchsorted(seq.timestamps_ms, dst, side="left").clip(0, len(seq.xy) - 1)
    lo = np.maximum(hi - 1, 0)
    exact = np.isclose(seq.timestamps_ms[hi], dst, rtol=0, atol=1e-9)
    lo[exact] = hi[exact]
    width = seq.timestamps_ms[hi] - seq.timestamps_ms[lo]
    alpha = np.divide(dst - seq.timestamps_ms[lo], width, out=np.zeros(target_len), where=width > 0)
    valid = observed[lo] & observed[hi]
    out = normalized[lo] * (1 - alpha[:, None, None]) + normalized[hi] * alpha[:, None, None]
    out[~valid] = np.nan
    return out.astype(np.float32), report
