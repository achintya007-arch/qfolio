"""Load ``configs/default.yaml`` into a frozen dataclass and hash it for result metadata."""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

DEFAULT_CONFIG = Path("configs/default.yaml")


@dataclass(frozen=True)
class Config:
    """Read-only view of the experiment config.

    Attributes
    ----------
    seed : int
        Global seed; every random component derives its seed from this.
    raw : dict
        The full parsed YAML, so new keys need no code change.
    """

    seed: int
    raw: dict[str, Any] = field(default_factory=dict)


def load_config(path: str | Path = DEFAULT_CONFIG) -> Config:
    """Parse the YAML config, applying ``fast_mode`` overrides when ``QFOLIO_FAST=1``."""
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if is_fast_mode():
        fast = raw.get("fast_mode", {})
        for section in ("qaoa", "benchmark"):
            for key, value in fast.items():
                if key in raw.get(section, {}):
                    raw[section][key] = value
    return Config(seed=int(raw["seed"]), raw=raw)


def config_hash(path: str | Path = DEFAULT_CONFIG) -> str:
    """Return a short SHA-256 of the config file bytes, stored in every results JSON."""
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()[:12]


def is_fast_mode() -> bool:
    """Return True when the ``QFOLIO_FAST`` env var is set to ``1`` (CI / notebook smoke)."""
    return os.environ.get("QFOLIO_FAST") == "1"
