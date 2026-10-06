import tempfile
from pathlib import Path
import unittest
from fastapi.testclient import TestClient
from pose_reference.server import create_app
from pose_reference.demo import create_demo, sequence


class ServerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "demo"
        create_demo(self.root)
        self.client = TestClient(create_app(self.root / "bank", self.root / "policy.json", self.root))

    def tearDown(self):
        self.client.close()
        self.temp.cleanup()

    def test_index_health_and_bank(self):
        self.assertEqual(self.client.get("/").status_code, 200)
        self.assertIn("Pose Reference", self.client.get("/").text)
        self.assertEqual(self.client.get("/health").json()["status"], "ready")
        doc = self.client.get("/bank").json()
        self.assertEqual(len(doc["glosses"]), 2)
        self.assertNotIn(str(self.root), str(doc))

    def test_synthetic_web_outcomes(self):
        for name, status in {"same":"match", "wrong":"low_similarity", "missing":"needs_recapture", "degenerate":"needs_recapture"}.items():
            pose = self.client.get("/demo/" + name).json()
            response = self.client.post("/compare", json={"target":"SYNTHETIC_HORIZONTAL", "pose":pose})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["status"], status)

    def test_invalid_json_rejected_without_score(self):
        for raw in (b'{"target":"A","target":"B"}', b'{"pose":NaN}', b'\xff'):
            response = self.client.post("/compare", content=raw)
            self.assertEqual(response.status_code, 400)
            self.assertIsNone(response.json()["score"])

    def test_invalid_pose_schema_rejected(self):
        response = self.client.post("/compare", json={"target":"SYNTHETIC_HORIZONTAL", "pose":{}})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["status"], "reject")

    def test_unknown_target_rejected(self):
        response = self.client.post("/compare", json={"target":"UNKNOWN", "pose":sequence().to_dict()})
        self.assertEqual(response.json()["reasons"], ["unknown_target"])

    def test_body_limit_enforced(self):
        self.assertEqual(self.client.post("/compare", content=b" " * 2_000_001).status_code, 413)

    def test_fixture_path_allowlist(self):
        self.assertEqual(self.client.get("/demo/other").status_code, 404)

    def test_tampered_bank_health_and_compare(self):
        path = self.root / "bank" / "profile.json"
        path.write_bytes(path.read_bytes() + b" ")
        self.assertEqual(self.client.get("/health").status_code, 503)
        response = self.client.post("/compare", json={"target":"SYNTHETIC_HORIZONTAL", "pose":sequence().to_dict()})
        self.assertEqual(response.json()["reasons"], ["bank_integrity_error"])


if __name__ == "__main__":
    unittest.main()
