"""Role-specific diagnostics and calibration; linguistic quality is not inferred."""
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
from .bank import audit_manifest, read_sample, sha256
from .compare import ComparePolicy, compare
from .pose import strict_json, write_json


def diagnostics(manifest, bank, role, policy=ComparePolicy(), calibration_receipt=None):
    if role not in {"calibration", "evaluation"}:
        raise ValueError("Diagnostics require calibration or evaluation role")
    rows, audit = audit_manifest(manifest)
    cases = []
    for row in rows:
        if row["role"] != role:
            continue
        if row["sha256"] in {digest for entry in bank.entries.values() for digest in entry["reference_source_sha256"]} or row["id"] in {rid for entry in bank.entries.values() for rid in entry["reference_ids"]} or row["source_group"] in bank.reference_groups or (row.get("speaker_verified") and row.get("speaker_id") in bank.reference_speakers) or (row.get("pose_sha256") and row["pose_sha256"] in {digest for entry in bank.entries.values() for digest in entry["reference_pose_sha256"]}):
            raise ValueError("Diagnostic sample overlaps the deployed reference bank")
        if calibration_receipt is not None and role == "evaluation":
            if calibration_receipt.get("bank_sha256") != bank.digest:
                raise ValueError("Calibration receipt bank mismatch")
            if row["id"] in calibration_receipt["source_sample_ids"] or row["sha256"] in calibration_receipt["source_sha256"] or row["source_group"] in calibration_receipt["source_groups"] or (row.get("pose_sha256") and row["pose_sha256"] in calibration_receipt["source_pose_sha256"]) or (row.get("speaker_verified") and row.get("speaker_id") in calibration_receipt["source_verified_speakers"]):
                raise ValueError("Evaluation overlaps calibration samples")
        try:
            seq = read_sample(row)
            for target in bank.entries:
                result = compare(seq, bank, target, policy, include_feedback=False)
                cases.append({"sample_id": row["id"], "source_sha256": row["sha256"], "actual_gloss": row["gloss"],
                              "target": target, "expected_target_match": row["gloss"] == target,
                              "status": result["status"], "score": result["score"], "margin": result.get("margin"),
                              "top_gloss": result.get("ranking", [{}])[0].get("gloss"), "reasons": result["reasons"]})
        except (ValueError, OSError, ImportError, RuntimeError) as error:
            cases.append({"sample_id": row["id"], "status": "reject", "score": None, "error": str(error)})
    if not cases:
        raise ValueError("No samples in requested diagnostic role")
    predicted = [c for c in cases if c.get("expected_target_match") is not None]
    positives = [c for c in predicted if c["expected_target_match"]]
    negatives = [c for c in predicted if not c["expected_target_match"]]
    return {"schema_version": 1, "role": role, "bank_sha256": bank.digest, "policy": asdict(policy), "audit": audit,
            "scope": "source-gloss target-match diagnostics; not expert-rated proficiency or educational benefit",
            "samples": len({c["sample_id"] for c in cases}), "comparisons": len(predicted),
            "true_match_rate": sum(c["status"] == "match" for c in positives) / len(positives) if positives else None,
            "false_match_rate": sum(c["status"] == "match" for c in negatives) / len(negatives) if negatives else None,
            "needs_recapture": sum(c["status"] == "needs_recapture" for c in cases),
            "inconclusive": sum(c["status"] == "inconclusive" for c in cases),
            "rejected": sum(c["status"] == "reject" for c in cases), "cases": cases}


def calibrate(manifest, bank, alignment="linear"):
    report = diagnostics(manifest, bank, "calibration", ComparePolicy(alignment=alignment))
    usable = [c for c in report["cases"] if c.get("score") is not None]
    positives = [c for c in usable if c["expected_target_match"]]
    negatives = [c for c in usable if not c["expected_target_match"]]
    if not positives or not negatives:
        raise ValueError("Calibration needs observable positive and negative target pairs")
    candidates = []
    for threshold in (70, 75, 80, 85, 90, 95):
        for margin in (0, 5, 10, 15):
            def accept(c):
                return c["top_gloss"] == c["target"] and c["score"] >= threshold and (c["margin"] is None or c["margin"] >= margin)
            tpr = sum(accept(c) for c in positives) / len(positives)
            fpr = sum(accept(c) for c in negatives) / len(negatives)
            candidates.append((0.5 * (tpr + 1 - fpr), threshold, margin, tpr, fpr))
    best = max(candidates)
    calibration_rows = [r for r in audit_manifest(manifest)[0] if r["role"] == "calibration"]
    return {"schema_version": 1, "bank_sha256": bank.digest, "role": "calibration",
            "policy": asdict(ComparePolicy(best[1], best[2], alignment)), "source_manifest_sha256": sha256(manifest),
            "source_sample_ids": sorted({c["sample_id"] for c in report["cases"]}),
            "source_sha256": [r["sha256"] for r in calibration_rows],
            "source_pose_sha256": [r["pose_sha256"] for r in calibration_rows if r["pose_sha256"]],
            "source_groups": sorted({r["source_group"] for r in calibration_rows}),
            "source_verified_speakers": sorted({r["speaker_id"] for r in calibration_rows if r.get("speaker_verified")}),
            "selection": "maximum empirical balanced target-match rate; stricter thresholds break ties",
            "positive_pairs": len(positives), "negative_pairs": len(negatives),
            "calibration_true_match_rate": best[3], "calibration_false_match_rate": best[4],
            "scope": report["scope"]}


def load_policy(path, bank):
    document = strict_json(Path(path).read_text(encoding="utf-8"))
    if document.get("schema_version") != 1 or document.get("bank_sha256") != bank.digest or document.get("role") != "calibration":
        raise ValueError("Calibration policy does not match this bank")
    return ComparePolicy(**document["policy"])
