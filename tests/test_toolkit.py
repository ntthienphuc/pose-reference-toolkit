import contextlib
import copy
import io
import json
from pathlib import Path
import shutil
import tempfile
import unittest
import numpy as np
from signova_reference.pose import PoseSequence, QualityConfig, prepare_pose, strict_json, write_json, load_pose
from signova_reference.demo import sequence, create_demo, NAMES, GROUPS
from signova_reference.bank import ReferenceBank, audit_manifest, build_bank, sha256
from signova_reference.compare import ComparePolicy, compare, match_template
from signova_reference.alignment import align
from signova_reference.evaluation import diagnostics, calibrate, load_policy
from signova_reference.cli import main


def changed(seq=None, **kwargs):
    seq = seq or sequence()
    values = {k: getattr(seq, k) for k in ("xy", "confidence", "timestamps_ms", "names", "groups", "coordinate_space", "mirror")}
    return PoseSequence(**{**values, **kwargs})


class PoseTests(unittest.TestCase):
    def test_duplicate_joint_names_rejected(self):
        names = list(NAMES)
        names[-1] = names[-2]
        with self.assertRaisesRegex(ValueError, "unique"):
            changed(names=names)

    def test_overlapping_groups_rejected(self):
        with self.assertRaisesRegex(ValueError, "partition"):
            changed(groups={"body": [0, 1, 2], "left_hand": [2, 3, 4], "right_hand": [5]})

    def test_missing_group_member_rejected(self):
        with self.assertRaisesRegex(ValueError, "partition"):
            changed(groups={"body": [0, 1], "left_hand": [3, 4], "right_hand": [5]})

    def test_equal_timestamps_rejected(self):
        times = sequence().timestamps_ms.copy()
        times[5] = times[4]
        with self.assertRaisesRegex(ValueError, "increasing"):
            changed(timestamps_ms=times)

    def test_nonfinite_confidence_rejected(self):
        confidence = sequence().confidence.copy()
        confidence[0, 0] = np.nan
        with self.assertRaisesRegex(ValueError, "Confidence"):
            changed(confidence=confidence)

    def test_observed_nan_rejected(self):
        xy = sequence().xy.copy()
        xy[0, 3] = np.nan
        with self.assertRaisesRegex(ValueError, "Observed"):
            changed(xy=xy)

    def test_missing_nan_roundtrip(self):
        seq = sequence()
        xy, conf = seq.xy.copy(), seq.confidence.copy()
        xy[4, 3] = np.nan
        conf[4, 3] = 0
        restored = PoseSequence.from_dict(changed(xy=xy, confidence=conf).to_dict())
        self.assertTrue(np.isnan(restored.xy[4, 3]).all())
        self.assertEqual(restored.confidence[4, 3], 0)

    def test_json_duplicates_and_nan_rejected(self):
        for raw in ('{"a":1,"a":2}', '{"a":NaN}', '{"a":Infinity}'):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                strict_json(raw)

    def test_coordinate_contract_rejected(self):
        with self.assertRaisesRegex(ValueError, "Unsupported"):
            changed(coordinate_space="normalized_unknown")

    def test_normalization_translation_scale_invariant(self):
        seq = sequence()
        a, _ = prepare_pose(seq, 32, tuple(GROUPS))
        b, _ = prepare_pose(changed(seq, xy=seq.xy * 20 + [123, -17]), 32, tuple(GROUPS))
        np.testing.assert_allclose(a, b, atol=1e-6)

    def test_resampling_does_not_bridge_missing_frame(self):
        seq = sequence()
        conf = seq.confidence.copy()
        conf[10, 3] = 0
        pose, report = prepare_pose(changed(seq, confidence=conf), 63, tuple(GROUPS))
        self.assertTrue(report["passed"])
        self.assertTrue(np.isnan(pose[19:22, 3]).all())

    def test_timestamp_gap_requests_recapture(self):
        seq = sequence()
        times = seq.timestamps_ms.copy()
        times[16:] += 400
        pose, report = prepare_pose(changed(seq, timestamps_ms=times), 32, tuple(GROUPS))
        self.assertIsNone(pose)
        self.assertIn("timestamp_gap", report["reasons"])

    def test_degenerate_anchors_requests_recapture(self):
        seq = sequence()
        xy = seq.xy.copy()
        xy[:, 1] = xy[:, 0]
        pose, report = prepare_pose(changed(seq, xy=xy), 32, tuple(GROUPS))
        self.assertIsNone(pose)
        self.assertIn("insufficient_shoulders", report["reasons"])

    def test_missing_hand_quality_failure(self):
        seq = sequence()
        conf = seq.confidence.copy()
        conf[:, 3:5] = 0
        _, report = prepare_pose(changed(seq, confidence=conf), 32, tuple(GROUPS))
        self.assertFalse(report["passed"])
        self.assertIn("insufficient_group:left_hand", report["reasons"])

    def test_quality_settings_cannot_disable_by_nan(self):
        for kwargs in ({"min_confidence": np.nan}, {"min_frames": True}, {"min_anchor_coverage": 0}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                QualityConfig(**kwargs)

    def test_unsafe_npz_object_metadata_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "unsafe.npz"
            seq = sequence()
            np.savez(path, xy=seq.xy, confidence=seq.confidence, timestamps_ms=seq.timestamps_ms, metadata=np.array({"schema_version": 1}, dtype=object))
            with self.assertRaisesRegex(ValueError, "Object arrays"):
                load_pose(path)


class BankTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture_temp = tempfile.TemporaryDirectory()
        cls.fixture = Path(cls.fixture_temp.name) / "fixture"
        create_demo(cls.fixture)

    @classmethod
    def tearDownClass(cls):
        cls.fixture_temp.cleanup()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "case"
        shutil.copytree(self.fixture, self.root)
        self.manifest = self.root / "sources.json"
        self.doc = strict_json(self.manifest.read_text(encoding="utf-8"))
        self.bank = ReferenceBank(self.root / "bank")

    def tearDown(self):
        self.temp.cleanup()

    def save(self):
        write_json(self.manifest, self.doc)

    def test_synthetic_outcomes(self):
        expected = {"same": "match", "wrong": "low_similarity", "missing": "needs_recapture", "degenerate": "needs_recapture"}
        for name, status in expected.items():
            with self.subTest(name=name):
                result = compare(load_pose(self.root / ("example_" + name + ".json")), self.bank, "SYNTHETIC_HORIZONTAL")
                self.assertEqual(result["status"], status)
                if status == "needs_recapture":
                    self.assertIsNone(result["score"])

    def test_unknown_target_rejected(self):
        self.assertEqual(compare(sequence(), self.bank, "ABSENT")["reasons"], ["unknown_target"])

    def test_ambiguous_similar_glosses_inconclusive(self):
        for row in self.doc["samples"]:
            if row["role"] == "reference" and row["gloss"] == "SYNTHETIC_VERTICAL":
                write_json(self.root / row["path"], sequence(0, 999 + int(row["id"][-1])).to_dict())
        build_bank(self.manifest, self.root / "ambiguous_bank")
        bank = ReferenceBank(self.root / "ambiguous_bank")
        result = compare(sequence(), bank, "SYNTHETIC_HORIZONTAL")
        self.assertEqual(result["status"], "inconclusive")
        self.assertEqual(result["margin"], 0)

    def test_calibration_rows_cannot_change_reference_templates(self):
        for row in self.doc["samples"]:
            if row["role"] == "calibration":
                write_json(self.root / row["path"], sequence(1, 900 + int(row["id"][-1])).to_dict())
        # Give each class unique seeds, keeping the source audit meaningful.
        write_json(self.root / self.doc["samples"][10]["path"], sequence(1, 950).to_dict())
        write_json(self.root / self.doc["samples"][11]["path"], sequence(1, 951).to_dict())
        build_bank(self.manifest, self.root / "independent_bank")
        bank = ReferenceBank(self.root / "independent_bank")
        for gloss in self.bank.entries:
            np.testing.assert_equal(self.bank.entries[gloss]["templates"], bank.entries[gloss]["templates"])
            np.testing.assert_equal(self.bank.entries[gloss]["tolerance"], bank.entries[gloss]["tolerance"])

    def test_query_receipt_changes_with_pose(self):
        first = compare(sequence(seed=800), self.bank, "SYNTHETIC_HORIZONTAL")
        second = compare(sequence(seed=801), self.bank, "SYNTHETIC_HORIZONTAL")
        self.assertNotEqual(first["query_pose_sha256"], second["query_pose_sha256"])

    def test_mirror_contract_mismatch_rejected(self):
        self.assertEqual(compare(changed(mirror="mirrored"), self.bank, "SYNTHETIC_HORIZONTAL")["reasons"], ["pose_contract_mismatch"])

    def test_feedback_score_same_reference(self):
        result = compare(sequence(), self.bank, "SYNTHETIC_HORIZONTAL")
        feedback = result["feedback"]
        ri = [p[1] for p in result["alignment_pairs"]]
        entry = self.bank.entries["SYNTHETIC_HORIZONTAL"]
        index = entry["reference_ids"].index(result["matched_reference_id"])
        np.testing.assert_allclose(feedback["reference_xy"], entry["templates"][index][ri])
        states = np.array(feedback["state"])
        expected = 100 * (states[:, feedback["required_indexes"]] == "within_tolerance").mean()
        self.assertAlmostEqual(result["score"], expected, places=5)

    def test_bank_asset_tamper_rejected(self):
        path = self.root / "bank" / "profile.json"
        path.write_bytes(path.read_bytes() + b" ")
        result = compare(sequence(), self.bank, "SYNTHETIC_HORIZONTAL")
        self.assertEqual(result["reasons"], ["bank_integrity_error"])
        with self.assertRaisesRegex(ValueError, "checksum"):
            ReferenceBank(self.root / "bank")

    def test_manifest_tamper_rejected(self):
        path = self.root / "bank" / "manifest.json"
        path.write_bytes(path.read_bytes() + b" ")
        self.assertEqual(compare(sequence(), self.bank, "SYNTHETIC_HORIZONTAL")["status"], "reject")

    def test_existing_bank_not_overwritten(self):
        digest = self.bank.digest
        with self.assertRaisesRegex(ValueError, "already exists"):
            build_bank(self.manifest, self.root / "bank")
        self.assertEqual(sha256(self.root / "bank" / "manifest.json"), digest)

    def test_source_group_role_overlap_rejected(self):
        self.doc["samples"][8]["source_group"] = self.doc["samples"][0]["source_group"]
        self.save()
        with self.assertRaisesRegex(ValueError, "group overlaps"):
            audit_manifest(self.manifest)

    def test_declared_verified_speaker_overlap_rejected(self):
        for i in (0, 8):
            self.doc["samples"][i].update(speaker_id="personA", speaker_verified=True)
        self.save()
        with self.assertRaisesRegex(ValueError, "speaker overlaps"):
            audit_manifest(self.manifest)

    def test_unverified_speaker_is_not_partition_evidence(self):
        self.doc["samples"][0].update(speaker_id="unverified", speaker_verified=False)
        self.save()
        self.assertEqual(audit_manifest(self.manifest)[1]["partition_scope"], "source-groups-only")

    def test_duplicate_bytes_rejected(self):
        self.doc["samples"][1]["path"] = self.doc["samples"][0]["path"]
        self.save()
        with self.assertRaisesRegex(ValueError, "Duplicate source"):
            audit_manifest(self.manifest)

    def test_same_bytes_different_labels_rejected(self):
        self.doc["samples"][4]["path"] = self.doc["samples"][0]["path"]
        self.save()
        with self.assertRaisesRegex(ValueError, "conflicting labels"):
            audit_manifest(self.manifest)

    def test_reencoded_pose_duplicate_rejected(self):
        row0, row1 = self.doc["samples"][:2]
        data = strict_json((self.root / row0["path"]).read_text(encoding="utf-8"))
        data["timestamps_ms"] = [t + 2048 for t in data["timestamps_ms"]]
        # Use integer original timestamps to avoid floating subtraction rounding.
        data["timestamps_ms"] = list(range(0, 320, 10))
        original = copy.deepcopy(data)
        original["timestamps_ms"] = [t + 2048 for t in data["timestamps_ms"]]
        write_json(self.root / row0["path"], data)
        (self.root / row1["path"]).write_text(json.dumps(original), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "canonical pose"):
            audit_manifest(self.manifest)

    def test_path_escape_rejected(self):
        self.doc["samples"][0]["path"] = "../outside.json"
        self.save()
        with self.assertRaisesRegex(ValueError, "escapes"):
            audit_manifest(self.manifest)

    def test_permission_required(self):
        self.doc["samples"][0]["authorized"] = False
        self.save()
        with self.assertRaisesRegex(ValueError, "permission"):
            audit_manifest(self.manifest)

    def test_excluded_reference_has_reason(self):
        row = self.doc["samples"][0]
        seq = load_pose(self.root / row["path"])
        conf = seq.confidence.copy()
        conf[:, 3:5] = 0
        write_json(self.root / row["path"], changed(seq, confidence=conf).to_dict())
        build_bank(self.manifest, self.root / "new_bank")
        report = strict_json((self.root / "new_bank" / "build_report.json").read_text(encoding="utf-8"))
        self.assertEqual(report["excluded"][0]["id"], row["id"])
        self.assertIn("insufficient_group:left_hand", report["excluded"][0]["quality"]["reasons"])

    def test_evaluation_cannot_use_reference_role(self):
        with self.assertRaisesRegex(ValueError, "role"):
            diagnostics(self.manifest, self.bank, "reference")

    def test_diagnostic_cross_manifest_reference_overlap_rejected(self):
        self.doc["samples"] = [self.doc["samples"][0]]
        self.doc["samples"][0]["role"] = "evaluation"
        self.save()
        with self.assertRaisesRegex(ValueError, "deployed reference"):
            diagnostics(self.manifest, self.bank, "evaluation")

    def test_evaluation_cannot_reuse_calibration(self):
        receipt = strict_json((self.root / "policy.json").read_text(encoding="utf-8"))
        self.doc["samples"] = [self.doc["samples"][8]]
        self.doc["samples"][0]["role"] = "evaluation"
        self.save()
        with self.assertRaisesRegex(ValueError, "overlaps calibration"):
            diagnostics(self.manifest, self.bank, "evaluation", calibration_receipt=receipt)

    def test_policy_bound_to_bank(self):
        doc = strict_json((self.root / "policy.json").read_text(encoding="utf-8"))
        doc["bank_sha256"] = "0" * 64
        write_json(self.root / "bad_policy.json", doc)
        with self.assertRaisesRegex(ValueError, "does not match"):
            load_policy(self.root / "bad_policy.json", self.bank)

    def test_cli_failure_preserves_output(self):
        output = self.root / "bank"
        with contextlib.redirect_stderr(io.StringIO()):
            code = main(["build", "--manifest", str(self.manifest), "--out", str(output)])
        self.assertEqual(code, 2)
        self.assertTrue(Path(str(output) + ".failure.json").is_file())
        self.assertEqual(ReferenceBank(output).digest, self.bank.digest)


class MatchingTests(unittest.TestCase):
    def test_chimera_cannot_mix_references_per_cell(self):
        # No full exemplar contains both halves. A per-cell minimum would give 100.
        a = np.zeros((8, 6, 2)); b = a.copy(); b[:, 3:, 0] = 2
        user = a.copy(); user[:, 4:, 0] = 2
        tolerance = np.full((8, 6), .1)
        naive = np.minimum(np.linalg.norm(user - a, axis=-1), np.linalg.norm(user - b, axis=-1))
        self.assertEqual(float((naive <= tolerance).mean()), 1)
        scores = [match_template(user, ref, tolerance, list(range(6)), ComparePolicy())["score"] for ref in (a, b)]
        self.assertLess(max(scores), 85)

    def test_missing_cells_never_raise_score(self):
        ref = np.zeros((8, 6, 2)); user = ref.copy(); user[:, 3] = np.nan
        result = match_template(user, ref, np.full((8, 6), .1), list(range(6)), ComparePolicy())
        self.assertLess(result["score"], 100)
        self.assertFalse(result["valid"][:, 3].any())

    def test_dtw_identity_and_endpoints(self):
        seq, _ = prepare_pose(sequence(), 32, tuple(GROUPS))
        ui, ri = align(seq, seq, np.full((32, 6), .1), list(range(6)), "dtw")
        np.testing.assert_equal(ui, np.arange(32))
        np.testing.assert_equal(ri, np.arange(32))

    def test_dtw_path_monotone_bounded_and_shared(self):
        a, _ = prepare_pose(sequence(seed=0), 32, tuple(GROUPS))
        b, _ = prepare_pose(sequence(seed=0, speed=1.5), 32, tuple(GROUPS))
        ui, ri = align(a, b, np.full((32, 6), .1), list(range(6)), "dtw", .2)
        self.assertEqual((ui[0], ri[0], ui[-1], ri[-1]), (0, 0, 31, 31))
        self.assertTrue((np.diff(ui) >= 0).all() and (np.diff(ri) >= 0).all())
        self.assertLessEqual(int(abs(ui - ri).max()), 7)
        self.assertGreater(len(ui), 32)

    def test_policy_invalid_boolean_and_nan_rejected(self):
        for kwargs in ({"min_score": True}, {"min_margin": np.nan}, {"alignment": "unknown"}, {"band_fraction": 2}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                ComparePolicy(**kwargs)


if __name__ == "__main__":
    unittest.main()
