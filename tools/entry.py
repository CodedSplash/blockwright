"""Точка входа для PyInstaller.

Собранный файл запускается как обычный скрипт, поэтому относительные
импорты пакета из blockwright/__main__.py напрямую не работают — здесь
пакет импортируется обычным образом.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from blockwright.__main__ import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
