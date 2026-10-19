"""Language descriptions: loading, `extends`, hooks, errors, and the CLI on
every fixture."""

import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from blockwright import vendored  # noqa: E402

vendored.activate()

from blockwright import langs, project  # noqa: E402
from blockwright import model as M  # noqa: E402
from blockwright.cli import Opts, main  # noqa: E402

LANGS = os.path.join(HERE, "langs")
FIXTURES = os.path.join(HERE, "fixtures")


class Descriptions(unittest.TestCase):
    def tearDown(self):
        langs._DEFAULT = None

    def test_builtin_load_cleanly(self):
        reg = langs.Registry()
        self.assertEqual(reg.errors, [])
        for name in ("c", "cpp", "python", "pascal", "java", "csharp", "go", "javascript"):
            self.assertIn(name, reg.names())
            self.assertTrue(reg.get(name).available, name)

    def test_extends_and_hooks(self):
        reg = langs.registry([LANGS])
        self.assertEqual(reg.errors, [])
        spec = reg.get("mini")
        self.assertEqual(spec.extensions, [".mini"])
        # inherited from python.toml
        self.assertIn("print", spec.io_output)
        src = project.load(os.path.join(LANGS, "sample.mini"))
        self.assertEqual(src.spec.name, "mini")
        (chart,) = project.charts(src, Opts(), src.known)
        first, second = chart.body.items
        self.assertIsInstance(first, M.If)
        self.assertEqual(first.cond, "x > 0")
        self.assertEqual(second.text, "Вывод: x")

    def test_bad_description_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            with open(os.path.join(tmp, "bad.toml"), "w", encoding="utf-8") as fh:
                fh.write('name = "bad"\ngrammar = "tree_sitter_c"\n'
                         '[statements]\nif_statement = { kind = "iff" }\n')
            with open(os.path.join(tmp, "orphan.toml"), "w", encoding="utf-8") as fh:
                fh.write('name = "orphan"\nextends = "nope"\ngrammar = "tree_sitter_c"\n')
            reg = langs.Registry([tmp])
        self.assertIsNone(reg.get("bad"))
        self.assertIsNone(reg.get("orphan"))
        text = "\n".join(reg.errors)
        self.assertIn("iff", text)
        self.assertIn("nope", text)

    def test_missing_grammar(self):
        with tempfile.TemporaryDirectory() as tmp:
            with open(os.path.join(tmp, "ghost.toml"), "w", encoding="utf-8") as fh:
                fh.write('name = "ghost"\ngrammar = "tree_sitter_ghost"\n'
                         'extensions = [".ghost"]\n')
            reg = langs.Registry([tmp])
        spec = reg.get("ghost")
        self.assertFalse(spec.available)
        self.assertEqual(spec.install_hint(), "pip install tree-sitter-ghost")

    def test_guess(self):
        reg = langs.Registry()
        self.assertEqual(reg.guess("a.h", "int f(void);").name, "c")
        self.assertEqual(reg.guess("a.h", "namespace x {}").name, "cpp")
        self.assertEqual(reg.guess("a.py", "").name, "python")
        self.assertEqual(reg.guess("A.java", "").name, "java")
        self.assertEqual(reg.guess("a.c", "", {"cpp"}).name, "cpp")


class Cli(unittest.TestCase):
    def test_every_fixture_builds(self):
        for folder in sorted(os.listdir(FIXTURES)):
            with self.subTest(folder=folder), tempfile.TemporaryDirectory() as out:
                rc = main([os.path.join(FIXTURES, folder), "-o", out, "--no-ui", "-q"])
                self.assertEqual(rc, 0)
                svgs = [f for f in os.listdir(out) if f.endswith(".svg")]
                self.assertTrue(svgs)
                self.assertIn("index.html", os.listdir(out))

    def test_lang_filter(self):
        with tempfile.TemporaryDirectory() as out:
            rc = main([FIXTURES, "-o", out, "--no-ui", "-q", "--lang", "pascal"])
            self.assertEqual(rc, 0)
            svgs = sorted(f for f in os.listdir(out) if f.endswith(".svg"))
            self.assertEqual(svgs, ["lab__Fill.svg", "lab__IsEven.svg",
                                    "lab__Lab.svg", "lab__Swap.svg"])

    def test_unknown_lang(self):
        self.assertEqual(main([FIXTURES, "--no-ui", "--lang", "cobol"]), 2)


if __name__ == "__main__":
    unittest.main()
