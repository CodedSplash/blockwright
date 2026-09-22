"""Режим «без установки»: парсеры tree-sitter из папки vendor.

В репозитории рядом лежат готовые сборки парсеров для разных платформ и
версий CPython. Если в системе их нет, точка входа подключает подходящую
папку к sys.path — и утилита работает сразу после копирования, без pip.

Исключение — Termux на Android: там своя libc, колёс на PyPI для неё нет,
поэтому парсеры собираются на месте (см. tools/install-termux.sh).
"""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def is_termux():
    """Termux на Android: свой префикс и libc, готовых колёс для него нет."""
    return ("com.termux" in os.environ.get("PREFIX", "")
            or os.path.isdir("/data/data/com.termux/files/usr"))


def platform_tag():
    """Имя папки vendor для текущей ОС и архитектуры."""
    import platform
    arch = platform.machine().lower()
    if sys.platform.startswith("win"):
        return "win_amd64" if sys.maxsize > 2 ** 32 else "win32"
    if sys.platform.startswith("linux"):
        if is_termux():
            return "android_" + (arch or "unknown")
        if arch in ("x86_64", "amd64"):
            return "linux_x86_64"
        return "linux_" + (arch or "unknown")
    if sys.platform == "darwin":
        return "macos_arm64" if arch in ("arm64", "aarch64") else "macos_x86_64"
    return sys.platform


def paths(root=None):
    """Папки vendor, подходящие текущему интерпретатору."""
    tag = f"cp{sys.version_info.major}{sys.version_info.minor}"
    base = os.path.join(root or ROOT, "vendor", platform_tag())
    return [p for p in (os.path.join(base, tag), os.path.join(base, "common"))
            if os.path.isdir(p)]


def have_parsers():
    try:
        import tree_sitter  # noqa: F401
        import tree_sitter_c  # noqa: F401
        import tree_sitter_cpp  # noqa: F401
        return True
    except Exception:  # noqa: BLE001
        return False


def activate(root=None):
    """Подключает парсеры из vendor, если в системе их нет."""
    if have_parsers():
        return True
    for p in paths(root):
        if p not in sys.path:
            sys.path.insert(0, p)
    return have_parsers()


def web_asset(*parts):
    """Файл из vendor/web (библиотеки редактора) или None, если его нет.

    Они одни на все платформы. В собранном exe папка лежит внутри архива
    PyInstaller, и ROOT указывает как раз туда.
    """
    p = os.path.join(ROOT, "vendor", "web", *parts)
    return p if os.path.isfile(p) else None


def install_hint():
    """Понятное объяснение, что делать, если парсеров нет."""
    req = os.path.join(ROOT, "requirements.txt")
    head = ("Не найдены парсеры tree-sitter.\n"
            f"Python {sys.version.split()[0]}, платформа {platform_tag()}.\n")
    if is_termux():
        return head + ("Termux собирает парсеры сам — нужен компилятор:\n"
                       "    pkg install python clang\n"
                       f"    pip install -r {req}\n"
                       "Либо разом: sh tools/install-termux.sh\n")
    return head + ("В комплекте есть сборки для CPython 3.10–3.14: "
                   "Windows x64 и Linux x86-64.\n"
                   "Для другой платформы выполните один раз:\n"
                   f"    {os.path.basename(sys.executable)} -m pip install -r {req}\n")
