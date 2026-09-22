#!/usr/bin/env python
"""Пересобирает папку vendor: парсеры tree-sitter для всех платформ.

    python tools/vendor.py                 Windows x64 + Linux x86-64
    python tools/vendor.py --only linux    только одна платформа

Колёса скачиваются с PyPI и распаковываются в vendor/<платформа>/<cpXY>.
Нужен доступ в интернет; запускать достаточно раз в полгода — чтобы
подтянуть свежие грамматики или поддержать новую версию Python.
"""

import argparse
import glob
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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


def main():
    ap = argparse.ArgumentParser(description="Пересборка папки vendor")
    ap.add_argument("--only", choices=sorted({**TARGETS, **OPTIONAL}),
                    help="только одна платформа (в том числе необязательная)")
    args = ap.parse_args()
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
