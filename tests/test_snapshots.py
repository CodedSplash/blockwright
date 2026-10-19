"""Flowchart IR snapshots for every fixture folder in tests/fixtures.

    python -m unittest discover tests                  check
    BLOCKWRIGHT_UPDATE=1 python -m unittest discover tests   rewrite snapshots
"""

import dataclasses
import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from blockwright import vendored  # noqa: E402

vendored.activate()

from blockwright import parse as P  # noqa: E402
from blockwright.build import Builder  # noqa: E402
from blockwright.cli import CHART_WORDS, Opts  # noqa: E402

FIXTURES = os.path.join(HERE, "fixtures")
SNAPSHOTS = os.path.join(HERE, "snapshots")
UPDATE = bool(os.environ.get("BLOCKWRIGHT_UPDATE"))

VARIANTS = {
    "default": {},
    "list": {"io_style": "list", "for_style": "decision", "return_style": "value"},
    "code": {"io_style": "code", "for_style": "hexagon", "return_style": "end",
             "keep_std": True, "lang": "en"},
}


def make_opts(**kw):
    words = CHART_WORDS[kw.get("lang", "ru")]
    return Opts(yes_label=words["yes"], no_label=words["no"],
                begin_label=words["begin"], end_label=words["end"],
                default_label=words["default"], **kw)


def ir(obj):
    if dataclasses.is_dataclass(obj):
        out = {"type": type(obj).__name__}
        for f in dataclasses.fields(obj):
            out[f.name] = ir(getattr(obj, f.name))
        return out
    if isinstance(obj, list):
        return [ir(x) for x in obj]
    return obj


def analyze(folder, opts):
    files = P.discover([folder])
    parsed, known = [], set()
    for path in files:
        with open(path, "rb") as fh:
            src = fh.read()
        lang = P.guess_language(path, src.decode("utf-8", "replace"))
        tree, lang, errs = P.parse_source(src, lang)
        known |= P.collect_known_names(src, tree.root_node)
        parsed.append((path, src, tree, lang, errs))
    result = {}
    for path, src, tree, lang, errs in parsed:
        builder = Builder(src, opts, known)
        funcs = []
        for node in P.collect_functions(src, tree.root_node):
            info = P.describe_function(src, node)
            body = builder.build_body(info["body"], is_main=info["base"] == "main")
            funcs.append({"name": info["name"], "signature": info["signature"],
                          "short": info["short"], "line": info["line"],
                          "body": ir(body)})
        rel = os.path.relpath(path, folder).replace("\\", "/")
        result[rel] = {"lang": lang, "errors": errs, "functions": funcs}
    return result


class Snapshots(unittest.TestCase):
    maxDiff = None


def _make_test(folder, path):
    def test(self):
        got = {name: analyze(path, make_opts(**kw))
               for name, kw in VARIANTS.items()}
        snap = os.path.join(SNAPSHOTS, folder + ".json")
        text = json.dumps(got, ensure_ascii=False, indent=1, sort_keys=True) + "\n"
        if UPDATE or not os.path.exists(snap):
            os.makedirs(SNAPSHOTS, exist_ok=True)
            with open(snap, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(text)
            return
        with open(snap, encoding="utf-8") as fh:
            want = json.load(fh)
        self.assertEqual(want, json.loads(text))
    return test


for _folder in sorted(os.listdir(FIXTURES)):
    if os.path.isdir(os.path.join(FIXTURES, _folder)):
        setattr(Snapshots, "test_" + _folder,
                _make_test(_folder, os.path.join(FIXTURES, _folder)))
Snapshots.test_examples = _make_test("examples", os.path.join(ROOT, "examples"))


if __name__ == "__main__":
    unittest.main()
