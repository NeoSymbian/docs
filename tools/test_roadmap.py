# SPDX-License-Identifier: Apache-2.0
import importlib.util
import os
import tempfile
import unittest

_spec = importlib.util.spec_from_file_location(
    "roadmap", os.path.join(os.path.dirname(__file__), "roadmap.py")
)
assert _spec and _spec.loader
rm = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rm)

GOOD = """# Storage
<!-- stages -->
| Stage | What | State | Updated | Next / evidence |
|---|---|---|---|---|
| FS7 | Install a big Z: | active | 2026-11-26 | step 0 done |
<!-- /stages -->
"""


class RoadmapTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        vars(rm)["ROOT"] = self.dir.name
        os.makedirs(os.path.join(self.dir.name, "storage", "history"))
        self.write(
            "roadmap.md", "# Roadmap\n<!-- board -->\nold\n<!-- /board -->\nend\n"
        )

    def tearDown(self):
        self.dir.cleanup()

    def write(self, name, text):
        with open(os.path.join(self.dir.name, name), "w", encoding="utf-8") as f:
            f.write(text)

    def read(self, name):
        with open(os.path.join(self.dir.name, name), encoding="utf-8") as f:
            return f.read()

    def test_write_then_check(self):
        self.write("storage/filesystem.md", GOOD)
        self.write(
            "storage/history/old.md", GOOD.replace("FS7", "FS0")
        )  # history is not on the board
        self.assertEqual(rm.main(["roadmap.py", "--check"]), 1)
        self.assertEqual(rm.main(["roadmap.py"]), 0)
        text = self.read("roadmap.md")
        self.assertIn(
            "| FS7 | Install a big Z: | 🔵 active | 2026-11-26 | step 0 done | [storage/filesystem](storage/filesystem.md) |",
            text,
        )
        self.assertNotIn("FS0", text)
        self.assertTrue(text.endswith("<!-- /board -->\nend\n"))
        self.assertEqual(rm.main(["roadmap.py", "--check"]), 0)

    def test_bad_state_and_date(self):
        self.write(
            "storage/filesystem.md", GOOD.replace("active | 2026-11-26", "busy | 26.11")
        )
        errors = []
        rm.blocks(os.path.join(self.dir.name, "storage/filesystem.md"), errors)
        self.assertEqual(len(errors), 1, errors)
        self.assertEqual(rm.main(["roadmap.py"]), 1)


if __name__ == "__main__":
    unittest.main()
