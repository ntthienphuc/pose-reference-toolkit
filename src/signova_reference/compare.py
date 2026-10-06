"""Quality-gated, whole-template matching with traceable joint-level feedback."""
from dataclasses import asdict, dataclass
import hashlib
import json
import numpy as np
from .alignment import align
from .pose import prepare_pose


@dataclass(frozen=True)
class ComparePolicy:
    min_score: float = 85
    min_margin: float = 5
    alignment: str = "linear"
    band_fraction: float = 0.2

    def __post_init__(self):
        if any(isinstance(v, bool) for v in (self.min_score, self.min_margin, self.band_fraction)) or not np.isfinite([self.min_score, self.min_margin, self.band_fraction]).all() or not 0 <= self.min_score <= 100 or not 0 <= self.min_margin <= 100 or not 0 <= self.band_fraction <= 1 or self.alignment not in {"linear", "dtw"}:
            raise ValueError("Invalid comparison policy")


def match_template(user, reference, tolerance, required, policy):
    ui, ri = align(user, reference, tolerance, required, policy.alignment, policy.band_fraction)
    distances = np.linalg.norm(user[ui] - reference[ri], axis=-1)
    ratios = distances / tolerance[ri]
    valid = np.isfinite(ratios)
    good = valid & (ratios <= 1)
    score = 100 * float(good[:, required].mean())
    cost = float(np.where(valid[:, required], np.minimum(ratios[:, required], 5), 5).mean())
    return {"score": score, "cost": cost, "ui": ui, "ri": ri, "ratios": ratios, "valid": valid, "good": good}


def nullable(array):
    out = np.asarray(array).astype(object)
    out[~np.isfinite(array)] = None
    return out.tolist()


def compare(seq, bank, target, policy=ComparePolicy(), include_feedback=True):
    query_digest = hashlib.sha256(json.dumps(seq.to_dict(), sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()
    result = {"schema_version": 1, "bank_sha256": bank.digest, "query_pose_sha256": query_digest, "target": target, "policy": asdict(policy),
              "scope": "geometric target-match feedback; not calibrated linguistic proficiency", "status": "reject", "score": None}
    try:
        bank.assert_integrity()
    except (ValueError, OSError) as error:
        return {**result, "reasons": ["bank_integrity_error"], "error": str(error)}
    if target not in bank.entries:
        return {**result, "reasons": ["unknown_target"]}
    if seq.contract != bank.profile["contract"]:
        return {**result, "reasons": ["pose_contract_mismatch"]}
    user, quality = prepare_pose(seq, bank.profile["target_len"], bank.profile["required_groups"], bank.quality)
    result["quality"] = quality
    if not quality["passed"]:
        return {**result, "status": "needs_recapture", "reasons": quality["reasons"]}
    matches = {}
    for gloss, entry in bank.entries.items():
        candidates = [match_template(user, reference, entry["tolerance"], bank.required, policy) for reference in entry["templates"]]
        index = min(range(len(candidates)), key=lambda i: (candidates[i]["cost"], -candidates[i]["score"], i))
        matches[gloss] = {**candidates[index], "reference_index": index}
    order = sorted(matches, key=lambda g: (-matches[g]["score"], matches[g]["cost"], g))
    selected = matches[target]
    alternatives = [matches[g]["score"] for g in order if g != target]
    margin = selected["score"] - max(alternatives) if alternatives else None
    if selected["score"] < policy.min_score or (margin is not None and margin < -policy.min_margin):
        status, reasons = "low_similarity", ["target_below_threshold_or_not_top_match"]
    elif (margin is not None and margin < policy.min_margin) or order[0] != target:
        status, reasons = "inconclusive", ["insufficient_inter_gloss_margin"]
    else:
        status, reasons = "match", []
    result.update(status=status, reasons=reasons, score=round(selected["score"], 6), margin=margin,
                  matched_reference_id=bank.entries[target]["reference_ids"][selected["reference_index"]],
                  ranking=[{"gloss": g, "score": round(matches[g]["score"], 6), "cost": matches[g]["cost"]} for g in order],
                  alignment_pairs=np.stack([selected["ui"], selected["ri"]], axis=-1).tolist(),
                  component_feedback={group: {"good_fraction": float(selected["good"][:, ids].mean()),
                                             "valid_fraction": float(selected["valid"][:, ids].mean()), "required": group in bank.profile["required_groups"]}
                                      for group, ids in bank.profile["contract"]["groups"].items()})
    if include_feedback:
        entry = bank.entries[target]
        result["feedback"] = {"names": bank.profile["contract"]["names"], "groups": bank.profile["contract"]["groups"],
                              "user_xy": nullable(user[selected["ui"]]),
                              "reference_xy": nullable(entry["templates"][selected["reference_index"]][selected["ri"]]),
                              "ratio": nullable(selected["ratios"]),
                              "state": [["unknown" if not v else ("within_tolerance" if g else "outside_tolerance") for v, g in zip(vrow, grow)]
                                        for vrow, grow in zip(selected["valid"], selected["good"])],
                              "required_indexes": bank.required}
    return result
