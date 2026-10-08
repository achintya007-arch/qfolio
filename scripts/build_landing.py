"""Write the GitHub Pages landing page from ``results/*.json`` (called by build_report.sh).

python scripts/build_landing.py site/index.html
"""

from __future__ import annotations

import html
import sys
from pathlib import Path

from qportfolio.benchmark import METHODS
from qportfolio.io import load_result

REPO = "https://github.com/achintya007-arch/qfolio"
STREAMLIT = "https://qfolio.streamlit.app"
NAMES = {
    "random": "Random basket (analytic)",
    "brute_force": "Brute force",
    "greedy": "Greedy",
    "simulated_annealing": "Simulated annealing",
    "penalty_qaoa_p1": "Penalty-QAOA p=1",
    "penalty_qaoa_p2": "Penalty-QAOA p=2",
    "xy_qaoa_p1": "XY-QAOA p=1",
    "xy_qaoa_p2": "XY-QAOA p=2",
    "xy_qaoa_p3": "XY-QAOA p=3",
}

PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Q-Folio report</title>
<style>
  :root {{ --bg:#fcfcfb; --ink:#1d1c19; --muted:#5d5c57; --line:#e4e3df; --accent:#2a78d6; }}
  @media (prefers-color-scheme: dark) {{
    :root {{ --bg:#1a1a19; --ink:#f4f3ef; --muted:#c3c2b7; --line:#3a3936; --accent:#3987e5; }}
  }}
  body {{ margin:0; background:var(--bg); color:var(--ink);
         font:16px/1.55 system-ui, -apple-system, "Segoe UI", sans-serif; }}
  main {{ max-width:1100px; margin:0 auto; padding:32px 16px 64px; }}
  h1 {{ font-size:1.9rem; margin:0 0 4px; }}
  .sub {{ color:var(--muted); margin:0 0 24px; }}
  a {{ color:var(--accent); }}
  nav a {{ margin-right:18px; font-weight:600; }}
  img {{ max-width:100%; height:auto; background:#fff; border-radius:6px; margin:16px 0; }}
  .scroll {{ overflow-x:auto; }}
  table {{ border-collapse:collapse; width:100%; font-variant-numeric:tabular-nums; }}
  th, td {{ padding:8px 10px; border-bottom:1px solid var(--line); text-align:right; }}
  th:first-child, td:first-child {{ text-align:left; }}
  th {{ color:var(--muted); font-weight:600; }}
  .note {{ color:var(--muted); font-size:.92rem; }}
</style>
</head>
<body><main>
<h1>Q-Folio: constraint-preserving QAOA for portfolio selection</h1>
<p class="sub">Qiskit Fall Fest 2026 · Industry Track I2 · Achintya Akella</p>
<nav><a href="qfolio.html">Executed notebook</a><a href="{repo}">Repository</a>
<a href="{streamlit}">Live demo (Streamlit)</a></nav>
<p>Pick exactly k of n NSE stocks for an equal-weight basket. XY-QAOA (Dicke start + XY-ring mixer)
keeps every sample a valid basket; we compare it with brute force, greedy, simulated annealing and
penalty-QAOA on the same objective, then run it on IBM hardware.</p>
<img src="figures/headline.png" alt="P(optimal), approximation ratio and P(top-2) by method">
<h2>Robustness set ({n_inst} instances, mean ± std, ideal simulator)</h2>
<div class="scroll"><table>
<tr><th>Method</th><th>P(optimal)</th><th>P(top-2)</th><th>Approx. ratio</th><th>P(feasible)</th>
<th>Wall time (s)</th></tr>
{rows}
</table></div>
<p class="note">Wall time includes QAOA angle optimisation on a statevector simulator, which is not
quantum runtime. Brute force is exact and fastest at this size. No quantum advantage is claimed.</p>
{hardware}
<img src="figures/noise_ladder.png" alt="P(optimal) from ideal simulation to real IBM hardware">
<p class="note">Generated {created} from commit {sha}.</p>
</main></body></html>
"""


def main() -> None:
    """Render the page."""
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "site/index.html")
    bench = load_result("results/benchmark.json")
    s = bench["summary"]
    rows = []
    for m in METHODS:
        r = s[m]
        rows.append(
            f"<tr><td>{html.escape(NAMES.get(m, m))}</td>"
            f"<td>{r['p_optimal_mean']:.3f} ± {r['p_optimal_std']:.3f}</td>"
            f"<td>{r['p_top2_mean']:.3f} ± {r['p_top2_std']:.3f}</td>"
            f"<td>{r['approx_ratio_mean']:.3f} ± {r['approx_ratio_std']:.3f}</td>"
            f"<td>{r['p_feasible_mean']:.3f}</td><td>{r['seconds_mean']:.3g}</td></tr>"
        )
    hw_path = Path("results/hardware/db3b1bimb58s7387e0jg.json")
    hardware = ""
    if hw_path.exists():
        hw = load_result(hw_path)
        cells = " · ".join(
            f"p={r['reps']}: raw {r['raw']['p_optimal']:.2f} → post-selected "
            f"{r['postselected']['p_optimal']:.2f}"
            for r in hw["runs"]
        )
        hardware = (
            f"<h2>Real hardware</h2><p>{html.escape(hw['backend'])}, job "
            f"<code>{html.escape(hw['job_id'])}</code>, 4 stocks pick 2, {hw['shots']} shots. "
            f"P(optimal): {cells} (random guess {hw['p_random']:.2f}).</p>"
        )
    page = PAGE.format(
        repo=REPO,
        streamlit=STREAMLIT,
        n_inst=s["brute_force"]["instances"],
        rows="\n".join(rows),
        hardware=hardware,
        created=bench["meta"]["created"],
        sha=bench["meta"]["git_sha"],
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding="utf-8")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
