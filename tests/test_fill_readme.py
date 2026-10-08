"""fill_readme.py: the RESULTS block is regenerated from JSON and nothing else changes."""

import importlib.util
import json
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "fill_readme.py"


def _load_script():
    spec = importlib.util.spec_from_file_location("fill_readme", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_fill_replaces_only_the_marked_block_and_is_idempotent():
    fr = _load_script()
    text = f"before\n{fr.START}\nold ⟨…⟩\n{fr.END}\nafter\n"
    once = fr.fill(text, "NEW")
    assert once == f"before\n{fr.START}\nNEW\n{fr.END}\nafter\n"
    assert fr.fill(once, "NEW") == once


def test_fill_requires_exactly_one_block():
    fr = _load_script()
    with pytest.raises(ValueError):
        fr.fill("no markers here", "NEW")


def test_committed_readme_matches_results_json():
    """The README tables must be exactly what the committed JSON produces."""
    fr = _load_script()
    root = SCRIPT.parents[1]
    bench = json.loads((root / "results" / "benchmark.json").read_text(encoding="utf-8"))
    noisy = json.loads((root / "results" / "noisy.json").read_text(encoding="utf-8"))
    hw_file = root / "results" / "hardware" / f"{fr.HW_JOB}.json"
    hw = json.loads(hw_file.read_text(encoding="utf-8"))
    readme = fr.README.read_text(encoding="utf-8")
    assert fr.fill(readme, fr.render(bench, noisy, hw)) == readme
