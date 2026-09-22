#!/usr/bin/env python
"""Пересобирает папку vendor: парсеры tree-sitter и библиотеки редактора.

    python tools/vendor.py                 Windows x64 + Linux x86-64 + web
    python tools/vendor.py --only linux    только одна платформа
    python tools/vendor.py --web           только библиотеки для браузера

Колёса скачиваются с PyPI и распаковываются в vendor/<платформа>/<cpXY>.
Трассировщик линий libavoid-js берётся с npm и кладётся в vendor/web —
он один на все платформы. Node.js для этого не нужен.
Нужен доступ в интернет; запускать достаточно раз в полгода — чтобы
подтянуть свежие грамматики или поддержать новую версию Python.
"""

import argparse
import base64
import glob
import hashlib
import io
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# консоль Windows бывает в cp1252/cp866 — иначе русский текст печатается кашей
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

PYTHONS = ["3.10", "3.11", "3.12", "3.13", "3.14"]
# По умолчанию собираются только две ходовые платформы — иначе папка
# vendor/ разрастается. ARM-сборки берутся из релиза или ставятся через pip.
TARGETS = {
    "win_amd64": "win_amd64",
    "linux_x86_64": "manylinux2014_x86_64",
}
OPTIONAL = {
    "linux_aarch64": "manylinux2014_aarch64",
    "macos_arm64": "macosx_11_0_arm64",
    "macos_x86_64": "macosx_10_9_x86_64",
}
GRAMMARS = {"tree_sitter_c": "tree_sitter_c", "tree_sitter_cpp": "tree_sitter_cpp"}


def download(pkgs, dest, py, platform_tag):
    cmd = [sys.executable, "-m", "pip", "download", *pkgs, "-d", dest,
           "--only-binary=:all:", "--python-version", py,
           "--platform", platform_tag, "-q"]
    return subprocess.call(cmd) == 0


def extract(whl, dest, keep):
    with zipfile.ZipFile(whl) as z:
        for name in z.namelist():
            top = name.split("/")[0]
            if top.endswith(".dist-info") or top.endswith(".data") or top not in keep:
                continue
            z.extract(name, dest)


def build(platform_name, pip_tag):
    out = os.path.join(ROOT, "vendor", platform_name)
    if os.path.isdir(out):
        shutil.rmtree(out)
    os.makedirs(os.path.join(out, "common"), exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        for py in PYTHONS:
            if not download(["tree_sitter", "tree_sitter_c", "tree_sitter_cpp"],
                            tmp, py, pip_tag):
                print(f"  ! не удалось скачать для Python {py}", file=sys.stderr)
        for pkg in GRAMMARS:
            found = sorted(glob.glob(os.path.join(tmp, pkg.replace("_", "_") + "-*.whl")))
            if not found:
                print(f"  ! нет колеса {pkg}", file=sys.stderr)
                continue
            extract(found[-1], os.path.join(out, "common"), {pkg})
        for whl in glob.glob(os.path.join(tmp, "tree_sitter-*.whl")):
            tag = os.path.basename(whl).split("-")[2]
            if tag.startswith("cp"):
                extract(whl, os.path.join(out, tag), {"tree_sitter"})
    size = sum(os.path.getsize(os.path.join(r, f))
               for r, _, fs in os.walk(out) for f in fs)
    print(f"{platform_name}: {sorted(os.listdir(out))}  ({size / 1024 / 1024:.1f} МБ)")


# --------------------------------------------------------------- web
# libavoid (Adaptagrams) — ортогональная трассировка линий с обходом блоков,
# та же, что в Inkscape и Dunnart. Сборка под WebAssembly — libavoid-js.
AVOID_VERSION = "0.5.0-beta.5"
AVOID_URL = f"https://registry.npmjs.org/libavoid-js/-/libavoid-js-{AVOID_VERSION}.tgz"
AVOID_SHA512 = ("jHkn6A10815TgFhZ1paUD/NDnQkg4C66qJc2Juj1NpmO/"
                "+QXnJ4UjIdKQarkXLmI/QgXhEO3RWDxMi3i+uHPwA==")
AVOID_README = """\
# libavoid-js {version}

Ортогональная трассировка линий для редактора схем (index.html).

* Исходники: https://github.com/Aksem/libavoid-js — порт libavoid из
  Adaptagrams (https://github.com/mjwybrow/adaptagrams) в WebAssembly.
* Лицензия: LGPL-2.1-or-later, текст — в файле LICENSE рядом.
* libavoid.wasm — без изменений из npm-пакета libavoid-js@{version}.
* libavoid.js — dist/index.js того же пакета, переделанный из ES-модуля в
  обычный скрипт: `import.meta.url` заменён, вместо `export` выставлена
  глобальная фабрика `AvoidModule`. Иначе модуль не грузится со страницы,
  открытой как file://.

Пересобрать: `python tools/vendor.py --web`.
"""


def _classic_script(js):
    """ES-модуль Emscripten -> обычный скрипт с глобальной AvoidModule."""
    js = js.replace("import.meta.url", '(typeof document<"u"&&document.baseURI||"")')
    js = re.sub(r"\n?//# sourceMappingURL=\S*\s*$", "", js)
    # в конце: var W=Wrap(Factory);export{W as AvoidLib};
    tail = re.search(r"var (\w+)=\w+\((\w+)\);export\s*\{\s*\1 as AvoidLib\s*\};?\s*$", js)
    if not tail:
        raise SystemExit("libavoid-js: не узнаю конец модуля — формат пакета сменился")
    js = js[:tail.start()] + f"return {tail.group(2)};"
    if re.search(r"\bimport\.meta\b|\bexport\s*\{", js):
        raise SystemExit("libavoid-js: в модуле остались import/export")
    return (f"/* libavoid-js {AVOID_VERSION} (LGPL-2.1-or-later), "
            "https://github.com/Aksem/libavoid-js */\n"
            f"var AvoidModule=(function(){{{js}\n}})();\n")


def build_web():
    out = os.path.join(ROOT, "vendor", "web", "libavoid")
    print(f"Скачиваю libavoid-js {AVOID_VERSION} …")
    with urllib.request.urlopen(AVOID_URL, timeout=60) as resp:
        blob = resp.read()
    digest = base64.b64encode(hashlib.sha512(blob).digest()).decode()
    if digest != AVOID_SHA512:
        raise SystemExit("libavoid-js: контрольная сумма не совпала")
    with tarfile.open(fileobj=io.BytesIO(blob), mode="r:gz") as tar:
        read = lambda name: tar.extractfile(f"package/{name}").read()  # noqa: E731
        js, wasm, lic = read("dist/index.js"), read("dist/libavoid.wasm"), read("LICENSE")
    if os.path.isdir(out):
        shutil.rmtree(out)
    os.makedirs(out)
    with open(os.path.join(out, "libavoid.js"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(_classic_script(js.decode("utf-8")))
    with open(os.path.join(out, "libavoid.wasm"), "wb") as fh:
        fh.write(wasm)
    with open(os.path.join(out, "LICENSE"), "wb") as fh:
        fh.write(lic)
    with open(os.path.join(out, "README.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(AVOID_README.format(version=AVOID_VERSION))
    size = sum(os.path.getsize(os.path.join(out, f)) for f in os.listdir(out))
    print(f"web: {sorted(os.listdir(out))}  ({size / 1024:.0f} КБ)")


def main():
    ap = argparse.ArgumentParser(description="Пересборка папки vendor")
    ap.add_argument("--only", choices=sorted({**TARGETS, **OPTIONAL}),
                    help="только одна платформа (в том числе необязательная)")
    ap.add_argument("--web", action="store_true",
                    help="только библиотеки редактора (libavoid-js)")
    args = ap.parse_args()
    if args.web:
        build_web()
        return 0
    if not args.only:
        build_web()
    targets = dict(TARGETS)
    if args.only and args.only in OPTIONAL:
        targets = {args.only: OPTIONAL[args.only]}
    for name, tag in targets.items():
        if args.only and args.only != name:
            continue
        print(f"Собираю {name} …")
        build(name, tag)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
