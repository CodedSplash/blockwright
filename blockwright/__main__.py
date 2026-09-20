"""Точка входа: python -m blockwright

    python -m blockwright                       выбор исходников в консоли
    python -m blockwright "Лабораторная №1"     сразу построить схемы
"""

import sys

from . import vendored

# на Windows консоль часто в cp866/cp1251 — принудительно выводим в UTF-8
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass


def main(argv=None):
    if not vendored.activate():
        sys.stderr.write(vendored.install_hint())
        return 3
    from .cli import main as cli_main
    return cli_main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
