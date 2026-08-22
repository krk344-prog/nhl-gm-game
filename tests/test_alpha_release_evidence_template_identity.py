from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

spec = importlib.util.spec_from_file_location(
    "run_alpha_release_handoff", SCRIPTS / "run_alpha_release_handoff.py"
)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class AlphaReleaseEvidenceTemplateIdentityTests(unittest.TestCase):
    def setUp(self):
        self.identity = {
            "commit_sha": "a" * 40,
            "api_base_url": "http://192.168.1.20:8000/api/v1",
            "application_package": module.APPLICATION_PACKAGE,
            "build_type": module.BUILD_TYPE,
            "apk_sha256": "b" * 64,
        }

    def test_complete_template_receives_exact_candidate_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            template_path = root / "template.json"
            output_path = root / "record.json"
            template = {**{key: "" for key in self.identity}, "route_pass": False}
            template_path.write_text(json.dumps(template), encoding="utf-8")

            result = module._write_prefilled_record(
                str(template_path), str(output_path), self.identity
            )

            self.assertEqual(result, str(output_path))
            record = json.loads(output_path.read_text(encoding="utf-8"))
            for key, value in self.identity.items():
                self.assertEqual(record[key], value)
            self.assertFalse(record["route_pass"])

    def test_template_missing_release_identity_field_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            template_path = root / "template.json"
            output_path = root / "record.json"
            template = {key: "" for key in self.identity if key != "apk_sha256"}
            template_path.write_text(json.dumps(template), encoding="utf-8")

            with self.assertRaisesRegex(
                RuntimeError,
                "missing required release identity fields: apk_sha256",
            ):
                module._write_prefilled_record(
                    str(template_path), str(output_path), self.identity
                )

            self.assertFalse(output_path.exists())


if __name__ == "__main__":
    unittest.main()
