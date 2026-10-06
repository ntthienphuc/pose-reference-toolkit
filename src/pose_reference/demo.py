"""Deterministic synthetic motion fixture, with no participant data."""
from pathlib import Path
import numpy as np
from .pose import PoseSequence, write_json
from .bank import ReferenceBank, build_bank
from .compare import compare
from .evaluation import calibrate, diagnostics, load_policy

NAMES = ("pose_left_shoulder", "pose_right_shoulder", "pose_nose", "left_hand_wrist", "left_hand_tip", "right_hand_wrist")
GROUPS = {"body": [0, 1, 2], "left_hand": [3, 4], "right_hand": [5]}


def sequence(kind=0, seed=0, length=32, speed=1):
    rng = np.random.default_rng(seed)
    t = np.linspace(0, 1, length) ** speed
    xy = np.zeros((length, 6, 2))
    xy[:, 0] = [-0.5, 0]
    xy[:, 1] = [0.5, 0]
    xy[:, 2] = [0, -0.5]
    if kind == 0:
        xy[:, 3, 0] = -0.6 + t
        xy[:, 3, 1] = 0.5
        xy[:, 5, 0] = 0.6 - t
        xy[:, 5, 1] = 0.8
    else:
        xy[:, 3, 0] = -0.8
        xy[:, 3, 1] = -0.3 + 1.7 * t
        xy[:, 5, 0] = 0.8
        xy[:, 5, 1] = 1.3 - 1.7 * t
    xy[:, 4] = xy[:, 3] + [0.05, -0.1]
    xy += rng.normal(0, 0.003, xy.shape)
    return PoseSequence(xy, np.ones((length, 6)), np.linspace(0, 1200, length), NAMES, GROUPS, "cartesian_xy")


def create_demo(output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    rows = []
    for role, count, offset in (("reference", 4, 100), ("calibration", 2, 200), ("evaluation", 2, 300)):
        for kind, gloss in enumerate(("SYNTHETIC_HORIZONTAL", "SYNTHETIC_VERTICAL")):
            for i in range(count):
                name = "%s_%d_%d" % (role, kind, i)
                write_json(output / (name + ".json"), sequence(kind, offset + kind * 10 + i).to_dict())
                rows.append({"id": name, "gloss": gloss, "path": name + ".json", "kind": "pose", "role": role,
                             "source_group": name, "license": "MIT synthetic fixture", "authorized": True})
    write_json(output / "sources.json", {"schema_version": 1, "samples": rows})
    bank_result = build_bank(output / "sources.json", output / "bank")
    bank = ReferenceBank(output / "bank")
    policy = calibrate(output / "sources.json", bank)
    write_json(output / "policy.json", policy)
    evaluation = diagnostics(output / "sources.json", bank, "evaluation", load_policy(output / "policy.json", bank), policy)
    write_json(output / "evaluation.json", evaluation)
    same = sequence(0, 400)
    wrong = sequence(1, 400)
    missing_confidence = same.confidence.copy()
    missing_confidence[:, GROUPS["left_hand"]] = 0
    missing = PoseSequence(same.xy, missing_confidence, same.timestamps_ms, NAMES, GROUPS, "cartesian_xy")
    bad_xy = same.xy.copy()
    bad_xy[:, 1] = bad_xy[:, 0]
    degenerate = PoseSequence(bad_xy, same.confidence, same.timestamps_ms, NAMES, GROUPS, "cartesian_xy")
    outcomes = {}
    expected = {"same": "match", "wrong": "low_similarity", "missing": "needs_recapture", "degenerate": "needs_recapture"}
    for name, seq in (("same", same), ("wrong", wrong), ("missing", missing), ("degenerate", degenerate)):
        write_json(output / ("example_" + name + ".json"), seq.to_dict())
        result = compare(seq, bank, "SYNTHETIC_HORIZONTAL", load_policy(output / "policy.json", bank))
        if result["status"] != expected[name]:
            raise RuntimeError("Demo outcome mismatch for " + name + ": " + result["status"])
        outcomes[name] = result["status"]
    receipt = {"status": "passed", "scope": "synthetic engineering fixture only; not sign-language accuracy",
               "seed_recipe": "role-offset plus class/index; NumPy default_rng", "bank": bank_result,
               "expected_outcomes": outcomes, "evaluation_role": evaluation["role"],
               "evaluation_true_match_rate": evaluation["true_match_rate"], "evaluation_false_match_rate": evaluation["false_match_rate"]}
    write_json(output / "receipt.json", receipt)
    return receipt
