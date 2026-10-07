"""Write and read ``results/*.json`` with reproducibility metadata.

Every file gets ``meta = {created, git_sha, config_hash, versions}`` (docs/02_ARCHITECTURE.md).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


def save_result(data: dict[str, Any], path: str | Path) -> Path:
    """Add the ``meta`` block to ``data`` and write it as indented JSON."""
    raise NotImplementedError


def load_result(path: str | Path) -> dict[str, Any]:
    """Read a results JSON written by :func:`save_result`."""
    raise NotImplementedError
