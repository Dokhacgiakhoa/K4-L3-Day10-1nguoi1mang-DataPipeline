"""One-click test runner: pytest + coverage report cho toàn bộ src/.

Dùng:
    python script/run_tests.py
Tương đương chạy trực tiếp:
    python -m pytest tests/ -v --cov=src --cov-report=term-missing
"""

from __future__ import annotations

import sys

import pytest


def main() -> int:
    args = [
        "tests/",
        "-v",
        "--cov=src",
        "--cov-report=term-missing",
    ]
    return pytest.main(args)


if __name__ == "__main__":
    sys.exit(main())
