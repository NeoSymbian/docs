# SPDX-License-Identifier: Apache-2.0
import importlib.util
import os
import tempfile
import unittest

_spec = importlib.util.spec_from_file_location(
    "check_links", os.path.join(os.path.dirname(__file__), "check-links.py")
)
assert _spec and _spec.loader
cl = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cl)


class SlugTest(unittest.TestCase):
    def test_github_rules(self):
        self.assertEqual(
            cl.slug("FS7: installing a big system area (Z:)"),
            "fs7-installing-a-big-system-area-z",
        )
        self.assertEqual(cl.slug("C7: complete calls"), "c7-complete-calls")
        self.assertEqual(cl.slug("`ENTRY_THUMB`"), "entry_thumb")
        self.assertEqual(
            cl.slug("Later (daily-phone stage)"), "later-daily-phone-stage"
        )
        self.assertEqual(cl.slug("TP4 policy (1.21)"), "tp4-policy-121")
        self.assertEqual(cl.slug("A – B"), "a--b")
        self.assertEqual(cl.slug("See [kit](kit.md)"), "see-kit")


class CheckTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.root = self.dir.name
        os.makedirs(os.path.join(self.root, "sub"))
        self.write("sub/b.md", '# Title\n## Same\n## Same\n<a id="x"></a>\n')

    def tearDown(self):
        self.dir.cleanup()

    def write(self, name, text):
        with open(os.path.join(self.root, name), "w", encoding="utf-8") as f:
            f.write(text)

    def errors(self, text):
        self.write("a.md", text)
        return cl.check_file(os.path.join(self.root, "a.md"), self.root)

    def test_good_links(self):
        text = (
            "[b](sub/b.md) [t](sub/b.md#title) [d](sub/b.md#same-1) [x](sub/b.md#x) [dir](sub/)\n"
            "[web](https://example.com/nope.md) [self](#top)\n# Top\n[r]: sub/b.md#same\n"
        )
        self.assertEqual(self.errors(text), [])

    def test_broken(self):
        errs = self.errors("[m](missing.md) [a](sub/b.md#nope) [s](sub/b.md#same-2)\n")
        self.assertEqual(len(errs), 3, errs)

    def test_code_is_ignored(self):
        self.assertEqual(
            self.errors("`[m](missing.md)`\n```\n[m](missing.md)\n```\n"), []
        )

    def test_percent_escape(self):
        self.write("sub/c d.md", "# X\n")
        self.assertEqual(self.errors("[c](sub/c%20d.md#x)\n"), [])


if __name__ == "__main__":
    unittest.main()
