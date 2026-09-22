#!/usr/bin/env python
"""Render the terminal picker as a terminal-window screenshot for the docs.

    python tools/screenshot_picker.py           -> docs/picker.html
    python tools/screenshot_picker.py --png     -> docs/picker.png as well

The screen is drawn by blockwright.tui itself and ANSI colours become HTML;
the path shown is replaced with a made-up one.
"""

import argparse
import io
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.stdout.reconfigure(encoding="utf-8")

from blockwright import vendored  # noqa: E402

vendored.activate(ROOT)
from blockwright import png as PNG  # noqa: E402
from blockwright import tui  # noqa: E402

COLS, ROWS = 118, 20
DEMO_PATH = r"D:\Projects\flowchart-demo"
FG, BG = "#c9d1d9", "#0d1117"


def xterm256():
    pal = ["#000000", "#cd3131", "#0dbc79", "#e5e510", "#2472c8", "#bc3fbc",
           "#11a8cd", "#e5e5e5", "#666666", "#f14c4c", "#23d18b", "#f5f543",
           "#3b8eea", "#d670d6", "#29b8db", "#ffffff"]
    levels = [0, 95, 135, 175, 215, 255]
    for r in levels:
        for g in levels:
            for b in levels:
                pal.append(f"#{r:02x}{g:02x}{b:02x}")
    for i in range(24):
        v = 8 + i * 10
        pal.append(f"#{v:02x}{v:02x}{v:02x}")
    return pal


PALETTE = xterm256()


def ansi_to_html(text):
    state = {"fg": None, "bg": None, "bold": False, "inv": False}
    out, buf = [], []

    def flush():
        if not buf:
            return
        fg, bg = state["fg"] or FG, state["bg"]
        if state["inv"]:
            fg, bg = bg or BG, fg
        style = f"color:{fg}"
        if bg:
            style += f";background:{bg}"
        if state["bold"]:
            style += ";font-weight:600"
        chunk = ("".join(buf).replace("&", "&amp;")
                 .replace("<", "&lt;").replace(">", "&gt;"))
        out.append(f'<span style="{style}">{chunk}</span>')
        buf.clear()

    i = 0
    while i < len(text):
        if text[i] == "\x1b" and text[i + 1:i + 2] == "[":
            j = text.find("m", i)
            if j < 0:
                break
            flush()
            params = [p for p in text[i + 2:j].split(";") if p] or ["0"]
            k = 0
            while k < len(params):
                p = int(params[k])
                if p == 0:
                    state.update(fg=None, bg=None, bold=False, inv=False)
                elif p == 1:
                    state["bold"] = True
                elif p == 7:
                    state["inv"] = True
                elif p in (38, 48) and params[k + 1:k + 2] == ["5"]:
                    state["fg" if p == 38 else "bg"] = PALETTE[int(params[k + 2]) % 256]
                    k += 2
                elif 30 <= p <= 37:
                    state["fg"] = PALETTE[p - 30]
                elif 90 <= p <= 97:
                    state["fg"] = PALETTE[p - 90 + 8]
                elif 40 <= p <= 47:
                    state["bg"] = PALETTE[p - 40]
                k += 1
            i = j + 1
            continue
        buf.append(text[i])
        i += 1
    flush()
    return "".join(out)


def capture(source):
    import shutil
    shutil.get_terminal_size = lambda d=(80, 24): os.terminal_size((COLS, ROWS))
    picker = tui.Picker(source, dict(tui.DEFAULTS))
    for i, (kind, _, name) in enumerate(picker.visible_entries()):
        if kind == "dir" and name == "examples":
            picker.cur[0] = i
            break
    picker.cwd = DEMO_PATH
    buf, old = io.StringIO(), sys.stdout
    sys.stdout = buf
    try:
        picker.draw()
    finally:
        sys.stdout = old
    return buf.getvalue()


PAGE = """<!doctype html><meta charset="utf-8">
<style>
  body {{ margin:0; padding:26px; background:transparent;
         font-family:'Cascadia Mono','Consolas','Segoe UI Symbol',monospace; }}
  .win {{ width:max-content; border-radius:12px; overflow:hidden;
          box-shadow:0 18px 50px rgba(0,0,0,.45); background:{bg};
          border:1px solid #21262d; }}
  .bar {{ height:38px; display:flex; align-items:center; gap:8px; padding:0 14px;
          background:#161b22; border-bottom:1px solid #21262d; }}
  .dot {{ width:12px; height:12px; border-radius:50%; }}
  .title {{ margin-left:10px; color:#8b949e; font-size:12.5px;
            font-family:'Segoe UI',sans-serif; }}
  .screen {{ padding:12px 14px 14px; font-size:14px; line-height:1.38; color:{fg}; }}
  .ln {{ white-space:pre; height:1.38em; }}
</style>
<div class="win">
  <div class="bar">
    <div class="dot" style="background:#ff5f57"></div>
    <div class="dot" style="background:#febc2e"></div>
    <div class="dot" style="background:#28c840"></div>
    <div class="title">{cap}</div>
  </div>
  <div class="screen">{body}</div>
</div>"""


def render_png(html_path, png_path):
    browser = PNG.find_browser()
    if not browser:
        print("Для --png нужен Chrome или Edge", file=sys.stderr)
        return False
    url = "file:///" + os.path.abspath(html_path).replace("\\", "/")
    cmd = [browser, "--headless=new", "--disable-gpu", "--hide-scrollbars",
           "--default-background-color=00000000", "--force-device-scale-factor=2",
           f"--screenshot={os.path.abspath(png_path)}",
           "--window-size=1120,470", url]
    try:
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                       check=False, timeout=120)
    except (OSError, subprocess.TimeoutExpired):
        return False
    return os.path.isfile(png_path)


def main():
    ap = argparse.ArgumentParser(description="Скриншот консольного выбора")
    ap.add_argument("--source", default=ROOT, help="папка, которую показывать")
    ap.add_argument("--png", action="store_true", help="сразу растеризовать")
    ap.add_argument("--lang", choices=["ru", "en"], default="ru",
                    help="язык интерфейса на скриншоте")
    ap.add_argument("--out", default=None, help="имя файла без расширения")
    args = ap.parse_args()
    tui.LANG = args.lang

    raw = capture(args.source)
    rows = {}
    for m in re.finditer(r"\x1b\[(\d+);1H(.*?)(?=\x1b\[\d+;1H|\x1b\[J|$)", raw, re.S):
        rows[int(m.group(1))] = m.group(2).replace("\x1b[K", "")
    body = "\n".join(f'<div class="ln">{ansi_to_html(rows.get(i, "")) or "&nbsp;"}</div>'
                     for i in range(1, ROWS + 1))

    stem = args.out or ("picker" if args.lang == "ru" else "picker-en")
    out_html = os.path.join(ROOT, "docs", stem + ".html")
    with open(out_html, "w", encoding="utf-8") as fh:
        fh.write(PAGE.format(body=body, fg=FG, bg=BG,
                             cap="blockwright — " + ("выбор исходников"
                                 if args.lang == "ru" else "pick the sources")))
    print(out_html)
    if args.png:
        out_png = os.path.join(ROOT, "docs", stem + ".png")
        print(out_png if render_png(out_html, out_png) else "PNG не создан")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
