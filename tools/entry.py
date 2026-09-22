"""PyInstaller entry point.

The bundle runs this as a plain script, where the relative imports of
blockwright/__main__.py would fail, so the package is imported normally.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from blockwright.__main__ import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
