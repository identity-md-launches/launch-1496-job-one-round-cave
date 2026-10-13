#!/usr/bin/env python3
"""Behavior checks for destination planning; fixtures stay in test/scratch."""

import json
from pathlib import Path
import shutil
import unittest

import landing


ROOT = Path("test/scratch/line2-landing-tests")
DESTINATION = str(ROOT / "received")


class LandingTests(unittest.TestCase):
    def setUp(self):
        if ROOT.exists():
            shutil.rmtree(ROOT)
        ROOT.mkdir(parents=True)
        self.receipt = landing.INSPECT.inspect_path("line-2/handoff.zip")

    def tearDown(self):
        shutil.rmtree(ROOT)

    def test_real_archive_on_new_destination(self):
        result = landing.plan("line-2/handoff.zip", DESTINATION)
        self.assertTrue(result["ready"])
        self.assertEqual(result["file_count"], 2)
        self.assertEqual(result["path_issues"], [])
        self.assertEqual(landing.main(["check", "line-2/handoff.zip", DESTINATION]), 0)

    def test_occupied_file_and_directory(self):
        target = ROOT / "received"
        target.mkdir()
        (target / "README.md").write_text("public fixture")
        (target / "handoff.py").mkdir()
        result = landing.plan_receipt(self.receipt, DESTINATION)
        self.assertFalse(result["ready"])
        self.assertEqual({issue["kind"] for issue in result["path_issues"]},
                         {"existing-file", "directory-at-file"})

    def test_symlink_and_file_ancestors(self):
        (ROOT / "received").symlink_to("elsewhere")
        result = landing.plan_receipt(self.receipt, DESTINATION)
        self.assertEqual({issue["kind"] for issue in result["path_issues"]},
                         {"symlink-at-leaf"})
        (ROOT / "received").unlink()
        (ROOT / "received").write_text("public fixture")
        result = landing.plan_receipt(self.receipt, DESTINATION)
        self.assertEqual({issue["kind"] for issue in result["path_issues"]},
                         {"file-at-leaf"})

    def test_nested_file_as_directory(self):
        target = ROOT / "received"
        target.mkdir()
        (target / "nested").write_text("public fixture")
        receipt = dict(self.receipt)
        receipt["files"] = [{"path": "nested/tool.py"}]
        result = landing.plan_receipt(receipt, DESTINATION)
        self.assertEqual(result["path_issues"][0]["kind"], "file-ancestor")

    def test_internal_collision_and_portability(self):
        receipt = dict(self.receipt)
        receipt["files"] = [{"path": "a"}, {"path": "a/b"},
                            {"path": "CON"}]
        result = landing.plan_receipt(receipt, DESTINATION)
        self.assertFalse(result["ready"])
        self.assertIn("archive-file-as-directory",
                      {issue["kind"] for issue in result["path_issues"]})
        self.assertIn("windows-device-name",
                      {issue["code"] for issue in result["portability_issues"]})

    def test_bad_archive_or_destination_has_no_report(self):
        bad = ROOT / "bad.zip"
        bad.write_bytes(Path("line-2/handoff.zip").read_bytes() + b"bad")
        with self.assertRaises(ValueError):
            landing.plan(str(bad), DESTINATION)
        for value in ("../outside", "/tmp/outside", "a/../b", "a//b", "a\\b", ""):
            with self.assertRaises(ValueError, msg=value):
                landing.destination_parts(value)

    def test_demo_is_read_only(self):
        result = landing.demo()
        self.assertTrue(result["fresh"]["ready"])
        self.assertFalse(result["occupied"]["ready"])
        self.assertFalse(Path("line-2/tools/handoff-landing/unpacked-demo").exists())


if __name__ == "__main__":
    unittest.main()
