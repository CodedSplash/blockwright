"""SVG to PNG through a headless Chromium-based browser (Edge or Chrome).

Edge ships with every Windows, so no rasterisation library is needed.
"""

import os
import re
import shutil
import subprocess

CANDIDATES = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files\Chromium\Application\chrome.exe",
    "/usr/bin/google-chrome", "/usr/bin/google-chrome-stable",
    "/usr/bin/chromium", "/usr/bin/chromium-browser",
    "/snap/bin/chromium", "/usr/bin/microsoft-edge",
    "/var/lib/flatpak/exports/bin/org.chromium.Chromium",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
]
NAMES = ["msedge", "chrome", "chromium", "chromium-browser", "google-chrome",
         "google-chrome-stable", "microsoft-edge", "microsoft-edge-stable"]

_SIZE_RE = re.compile(r'<svg[^>]*?\bwidth="([\d.]+)"[^>]*?\bheight="([\d.]+)"', re.S)


def find_browser():
    for name in NAMES:
        p = shutil.which(name)
        if p:
            return p
    for p in CANDIDATES:
        if os.path.isfile(p):
            return p
    return None


def svg_size(path):
    with open(path, encoding="utf-8") as fh:
        head = fh.read(4096)
    m = _SIZE_RE.search(head)
    if not m:
        return 1200, 900
    return float(m.group(1)), float(m.group(2))


def convert(svg_path, png_path, scale=2.0, browser=None, timeout=90):
    """Screenshot an SVG file into a PNG; True on success."""
    browser = browser or find_browser()
    if not browser:
        return False
    w, h = svg_size(svg_path)
    png_path = os.path.abspath(png_path)
    url = "file:///" + os.path.abspath(svg_path).replace("\\", "/")
    cmd = [browser, "--headless=new", "--disable-gpu", "--hide-scrollbars",
           "--no-first-run", "--disable-extensions",
           f"--force-device-scale-factor={scale}",
           f"--screenshot={png_path}",
           f"--window-size={int(round(w))},{int(round(h))}", url]
    try:
        subprocess.run(cmd, timeout=timeout, stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return False
    return os.path.isfile(png_path)
