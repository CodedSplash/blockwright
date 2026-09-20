"""Режим «без установки»: парсеры tree-sitter из папки vendor.

В репозитории рядом лежат готовые сборки парсеров для разных платформ и
версий CPython. Если в системе их нет, точка входа подключает подходящую
папку к sys.path — и утилита работает сразу после копирования, без pip.
"""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def platform_tag():
    """Имя папки vendor для текущей ОС и архитектуры."""
    import platform
    arch = platform.machine().lower()
    if sys.platform.startswith("win"):
        return "win_amd64" if sys.maxsize > 2 ** 32 else "win32"
    if sys.platform.startswith("linux"):
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


def install_hint():
    return (
        "Не найдены парсеры tree-sitter.\n"
        f"Python {sys.version.split()[0]}, платформа {platform_tag()}.\n"
        "В комплекте есть сборки для CPython 3.10–3.14: Windows x64 и Linux x86-64.\n"
        "Для другой платформы выполните один раз:\n"
        f"    {os.path.basename(sys.executable)} -m pip install -r "
        f"{os.path.join(ROOT, 'requirements.txt')}\n")
