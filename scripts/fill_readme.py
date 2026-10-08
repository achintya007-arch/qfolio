"""Fill the README results tables from results/*.json (between the RESULTS markers).

Re-running is safe: everything between ``<!-- RESULTS:START -->`` and ``<!-- RESULTS:END -->``
is regenerated, so the README can never drift from the JSON.
Usage: python scripts/fill_readme.py
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
HW_JOB = "db3b1bimb58s7387e0jg"
PAGES_URL = "https://achintya007-arch.github.io/qfolio/"
STREAMLIT_URL = "https://qfolio.streamlit.app"
# IBM Quantum dashboard screenshots committed next to the job JSON.
SCREENSHOTS = " · ".join(
    f"[{label}](results/hardware/ibm_{name}.png)"
    for label, name in [
        ("workloads", "workloads"),
        ("job", "job_details"),
        ("histogram", "job_histogram"),
    ]
)
START, END = "<!-- RESULTS:START -->", "<!-- RESULTS:END -->"

# (key in benchmark.json, label shown in the README)
METHODS = [
    ("random", "Random valid basket"),
    ("brute_force", "Brute force (exact)"),
    ("greedy", "Greedy heuristic"),
    ("simulated_annealing", "Simulated annealing (same QUBO)"),
    ("penalty_qaoa_p2", "Penalty-QAOA (X mixer), p=2"),
    ("xy_qaoa_p1", "XY-QAOA (Dicke init), p=1"),
    ("xy_qaoa_p2", "**XY-QAOA (Dicke init), p=2**"),
    ("xy_qaoa_p3", "XY-QAOA (Dicke init), p=3"),
]


def _pm(mean: float, std: float) -> str:
    return f"{mean:.2f} ± {std:.2f}"


def _secs(s: float) -> str:
    if s == 0:
        return "—"
    return f"{s * 1000:.2f} ms" if s < 1 else f"{s:.0f} s"


def robustness_table(bench: dict) -> list[str]:
    """Mean ± std over the robustness instances (the fair, many-instance comparison)."""
    s = bench["summary"]
    n = s["xy_qaoa_p2"]["instances"]
    rows = [
        f"**Robustness: {n} random 3-of-6 instances** (mean ± std; random = 1/C(6,3) = 0.05)",
        "",
        "| Method | P(optimal) | P(top-2) | Approx. ratio | Valid portfolios | Wall time |",
        "|---|---|---|---|---|---|",
    ]
    for key, label in METHODS:
        m = s[key]
        rows.append(
            f"| {label} | {_pm(m['p_optimal_mean'], m['p_optimal_std'])} "
            f"| {_pm(m['p_top2_mean'], m['p_top2_std'])} "
            f"| {_pm(m['approx_ratio_mean'], m['approx_ratio_std'])} "
            f"| {m['p_feasible_mean']:.0%} | {_secs(m['seconds_mean'])} |"
        )
    return rows


def headline_table(bench: dict) -> list[str]:
    """The real NSE instance; near-degenerate, so P(top-2) and AR matter more than P(optimal)."""
    h, g = bench["headline"], bench["gaps"]["headline"]
    tickers = ", ".join(t.removesuffix(".NS") for t in bench["instances"][0]["tickers"])
    rows = [
        f"**Real NSE instance** ({tickers}; k = 3). The best and second-best baskets differ by "
        f"only {g['gap'] / g['cost_range']:.1%} of the cost range, so read P(top-2) and AR here.",
        "",
        "| Method | P(optimal) | P(top-2) | Approx. ratio | Valid | Top answer = optimum? |",
        "|---|---|---|---|---|---|",
    ]
    for key, label in METHODS:
        m = h[key]
        top1 = {True: "yes", False: "no", None: "—"}[m["top1_is_optimal"]]
        rows.append(
            f"| {label} | {m['p_optimal']:.2f} | {m['p_top2']:.2f} | {m['approx_ratio']:.2f} "
            f"| {m['p_feasible']:.0%} | {top1} |"
        )
    return rows


def noise_table(noisy: dict, hw: dict) -> list[str]:
    """4-asset (k = 2) instance, XY-QAOA p = 2: ideal → noisy sims → real IBM hardware."""
    rand = hw["p_random"]
    rows = [
        f"**Noise ladder: 2 of 4 stocks, XY-QAOA p = 2, {hw['shots']} shots** "
        f"(random = {rand:.2f})",
        "",
        "| Run | P(optimal) | Approx. ratio | Valid (raw) | Evidence |",
        "|---|---|---|---|---|",
    ]
    ideal = noisy["ideal"]["2"]
    rows.append(
        f"| Ideal statevector | {ideal['p_optimal']:.2f} | {ideal['approx_ratio']:.2f} "
        f"| 100% | `results/noisy.json` |"
    )
    for name, b in noisy["backends"].items():
        r = next(x for x in b["runs"] if x["reps"] == 2)
        rows.append(
            f"| {name} noise model: raw → post-selected "
            f"| {r['raw']['p_optimal']:.2f} → {r['postselected']['p_optimal']:.2f} "
            f"| {r['postselected']['approx_ratio']:.2f} | {r['raw']['p_feasible']:.0%} "
            f"| `results/noisy.json` |"
        )
    r = next(x for x in hw["runs"] if x["reps"] == 2)
    rows.append(
        f"| **`{hw['backend']}` (real hardware): raw → post-selected** "
        f"| **{r['raw']['p_optimal']:.2f} → {r['postselected']['p_optimal']:.2f}** "
        f"| {r['postselected']['approx_ratio']:.2f} | {r['raw']['p_feasible']:.0%} "
        f"| job `{hw['job_id']}`: {SCREENSHOTS} |"
    )
    return rows


def render(bench: dict, noisy: dict, hw: dict) -> str:
    """Build the full markdown block that goes between the markers."""
    parts = [
        *robustness_table(bench),
        "",
        *headline_table(bench),
        "",
        *noise_table(noisy, hw),
        "",
        "Wall time includes classical parameter optimisation on a statevector simulator "
        "(8 restarts). It is not a hardware speed measurement.",
        "",
        f"Full interactive report: **{PAGES_URL}** · Live demo: **{STREAMLIT_URL}**",
    ]
    return "\n".join(parts)


def fill(text: str, block: str) -> str:
    """Replace everything between the markers with ``block`` (markers must exist once)."""
    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.S)
    if len(pattern.findall(text)) != 1:
        raise ValueError("README must contain exactly one RESULTS:START/END block")
    return pattern.sub(lambda _: f"{START}\n{block}\n{END}", text)


def main() -> None:
    bench = json.loads((ROOT / "results" / "benchmark.json").read_text(encoding="utf-8"))
    noisy = json.loads((ROOT / "results" / "noisy.json").read_text(encoding="utf-8"))
    hw_path = ROOT / "results" / "hardware" / f"{HW_JOB}.json"
    hw = json.loads(hw_path.read_text(encoding="utf-8"))
    text = README.read_text(encoding="utf-8")
    README.write_text(fill(text, render(bench, noisy, hw)), encoding="utf-8")
    print("README results filled from results/*.json")


if __name__ == "__main__":
    main()
