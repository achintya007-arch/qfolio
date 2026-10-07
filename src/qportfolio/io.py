"""Write and read ``results/*.json`` with reproducibility metadata.

Every file gets ``meta = {created, git_sha, config_hash, versions}`` (docs/02_ARCHITECTURE.md).
"""

from __future__ import annotations

import json
import subprocess
from datetime import UTC, datetime
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

import numpy as np

from qportfolio.config import DEFAULT_CONFIG, config_hash

_PACKAGES = ("qiskit", "qiskit-aer", "qiskit-ibm-runtime", "numpy", "scipy", "pandas")


def _versions() -> dict[str, str]:
    out = {}
    for pkg in _PACKAGES:
        try:
            out[pkg] = version(pkg)
        except PackageNotFoundError:
            out[pkg] = "not installed"
    return out


def _git_sha() -> str:
    try:
        res = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, check=True
        )
        return res.stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def _to_json(obj: Any) -> Any:
    """Make NumPy scalars / arrays JSON-serialisable."""
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, np.generic):
        return obj.item()
    raise TypeError(f"not JSON serialisable: {type(obj).__name__}")


def save_result(
    data: dict[str, Any], path: str | Path, config_path: str | Path = DEFAULT_CONFIG
) -> Path:
    """Add the ``meta`` block to ``data`` and write it as indented JSON."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    meta = {
        "created": datetime.now(UTC).isoformat(timespec="seconds"),
        "git_sha": _git_sha(),
        "config_hash": config_hash(config_path) if Path(config_path).exists() else "none",
        "versions": _versions(),
    }
    payload = {"meta": meta, **{k: v for k, v in data.items() if k != "meta"}}
    path.write_text(json.dumps(payload, indent=2, default=_to_json) + "\n", encoding="utf-8")
    return path


def load_result(path: str | Path) -> dict[str, Any]:
    """Read a results JSON written by :func:`save_result`."""
    return json.loads(Path(path).read_text(encoding="utf-8"))
