"""Q-Folio live demo: ``streamlit run app/streamlit_app.py`` (docs/07 §3).

Four tabs: build a basket live (brute force vs XY-QAOA on the ideal simulator), why XY beats
penalty-QAOA, noise and real hardware, limits. Heavy results are read from ``results/``; only
tab 1 computes, and it is cached and capped at n ≤ 6, p ≤ 2 to fit Streamlit Cloud.
"""

from __future__ import annotations

import multiprocessing
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import matplotlib

# Streamlit runs this script in a worker thread; a GUI backend (TkAgg on Windows) crashes the
# server natively when its figures are touched off the main thread. Agg renders to images only.
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))  # Streamlit Cloud does not pip-install the package

from qportfolio import viz  # noqa: E402
from qportfolio.benchmark import solve_live  # noqa: E402
from qportfolio.config import load_config  # noqa: E402
from qportfolio.data import load_prices, returns_stats  # noqa: E402
from qportfolio.io import load_result  # noqa: E402

RESULTS = ROOT / "results"
FIGURES = RESULTS / "figures"
HARDWARE_JOB = RESULTS / "hardware" / "db3b1bimb58s7387e0jg.json"
CFG = load_config(ROOT / "configs" / "default.yaml").raw
RESTARTS, SHOTS = 4, 4096  # app budget (docs/07 §3)

st.set_page_config(page_title="Q-Folio", page_icon="📈", layout="wide")


@st.cache_data(show_spinner=False)
def load_json(path: str) -> dict | None:
    """Read a results JSON, or None if it has not been generated."""
    return load_result(path) if Path(path).exists() else None


@st.cache_resource
def solver_pool() -> ProcessPoolExecutor:
    """One worker process for the live QAOA solve (created once per server).

    NOTE(achintya): on Windows the server crashed natively (access violation inside Qiskit's
    Rust circuit copy) when StatevectorEstimator ran in Streamlit's script thread; the same
    code is fine in a plain thread or process. Running it in its own process side-steps that.
    """
    return ProcessPoolExecutor(max_workers=1, mp_context=multiprocessing.get_context("spawn"))


@st.cache_data(show_spinner=False)
def solve(tickers: tuple[str, ...], k: int, q: float, reps: int, seed: int) -> dict:
    """Brute force + XY-QAOA (ideal simulator) on one instance; returns a viz-ready dict."""
    d = CFG["data"]
    mu, sigma = returns_stats(load_prices(ROOT / d["path"], list(tickers), d["start"], d["end"]))
    labels = tuple(t.removesuffix(".NS") for t in tickers)
    settings = {"restarts": RESTARTS, "maxiter": CFG["qaoa"]["maxiter"], "shots": SHOTS}
    future = solver_pool().submit(solve_live, mu, sigma, labels, k, q, reps, settings, seed)
    return {"instances": [{"tickers": list(tickers), **future.result()}]}


st.title("Q-Folio: constraint-preserving QAOA for portfolio selection")
st.caption("Qiskit Fall Fest 2026 · Industry Track I2 · ideal simulator unless stated otherwise")
tab1, tab2, tab3, tab4 = st.tabs(
    ["① Build basket", "② Why XY beats penalty", "③ Noise & hardware", "④ Limits"]
)

with tab1:
    universe = CFG["data"]["universe"]
    c1, c2, c3, c4 = st.columns([3, 1, 1, 1])
    tickers = c1.multiselect(
        "Candidate stocks (4–6)",
        universe,
        default=CFG["data"]["tickers"],
        max_selections=6,
        format_func=lambda t: t.removesuffix(".NS"),
    )
    n = len(tickers)
    k = c2.slider("Hold k", 1, max(n - 1, 1), min(3, max(n - 1, 1)))
    q = c3.selectbox(
        "Risk aversion q",
        [0.25, 0.5, 1.0],
        index=1,
        format_func=lambda v: {0.25: "0.25 growth", 0.5: "0.5 balanced", 1.0: "1.0 conservative"}[
            v
        ],
    )
    reps = c4.selectbox("QAOA depth p", [1, 2], index=0)
    if n < 4:
        st.info("Pick at least 4 stocks.")
    elif st.button("Find the basket", type="primary"):
        with st.spinner("Optimising XY-QAOA angles on the statevector simulator…"):
            out = solve(tuple(tickers), k, q, reps, CFG["seed"])
        inst = out["instances"][0]
        m = inst["methods"][f"xy_qaoa_p{reps}"]
        best_assets = min(inst["baskets"], key=lambda b: b["cost"])["assets"]
        n_baskets = len(inst["baskets"])
        st.success(f"Optimal basket (brute force): **{' + '.join(best_assets)}**")
        cols = st.columns(4)
        cols[0].metric(
            "P(optimal)", f"{m['p_optimal']:.2f}", f"random {1 / n_baskets:.2f}", delta_color="off"
        )
        cols[1].metric(
            "P(top-2)", f"{m['p_top2']:.2f}", f"random {2 / n_baskets:.2f}", delta_color="off"
        )
        cols[2].metric("Approximation ratio", f"{m['approx_ratio']:.2f}")
        cols[3].metric("P(valid basket)", f"{m['p_feasible']:.2f}")
        g1, g2 = st.columns(2)
        g1.pyplot(viz.distribution(out))
        g2.pyplot(viz.frontier(out))
        st.caption(
            f"{SHOTS} shots, {RESTARTS} optimiser restarts, angle optimisation took "
            f"{m['seconds']:.1f} s. Simulation time is not quantum runtime."
        )

with tab2:
    st.markdown(
        "**Penalty-QAOA** starts in all 2ⁿ bitstrings and adds a penalty for the wrong number of "
        "stocks. Most shots are invalid baskets. **XY-QAOA** starts in a Dicke state (only valid "
        "baskets) and mixes with `XXPlusYYGate`, which swaps one stock for another, so every shot "
        "is a valid basket."
    )
    bench = load_json(str(RESULTS / "benchmark.json"))
    if bench is None:
        st.warning("results/benchmark.json not found: run scripts/run_benchmark.py")
    else:
        st.pyplot(viz.feasibility(bench))
        st.pyplot(viz.headline(bench))
        n_inst = bench["summary"]["brute_force"]["instances"]
        st.caption(
            f"Bars: headline NSE instance. Dots: mean ± std over {n_inst} instances. "
            "Brute force is exact and fastest at this size; no quantum advantage is "
            "claimed."
        )

with tab3:
    hw = load_json(str(HARDWARE_JOB))
    for name, caption in (
        ("noise_ladder", "Ideal → noisy simulator → real IBM hardware"),
        ("transpile", "Transpiler study on IBM Heron fake backends"),
    ):
        png = FIGURES / f"{name}.png"
        if png.exists():
            st.image(str(png), caption=caption, width="stretch")
    if hw is not None:
        rows = {
            f"p = {r['reps']}": {
                "raw": r["raw"]["p_optimal"],
                "post-selected": r["postselected"]["p_optimal"],
                "post-sel. + readout-mitigated": r["mitigated"]["p_optimal_postselected"],
            }
            for r in hw["runs"]
        }
        st.markdown(
            f"**Real device:** `{hw['backend']}`, job `{hw['job_id']}`, "
            f"{hw['shots']} shots. P(optimal), random guess = {hw['p_random']:.3f}:"
        )
        st.dataframe(pd.DataFrame(rows).T.style.format("{:.3f}"))

with tab4:
    st.markdown(
        "- **Scale:** 6 stocks, 20 baskets. Brute force wins easily and will until n ≈ 40; "
        "classical heuristics handle hundreds of assets.\n"
        "- **What would need to be true:** lower-error hardware for deeper circuits, evidence that "
        "QAOA's success probability decays more slowly than classical heuristics', and cheap "
        "parameter setting at scale.\n"
        "- **Model limits:** equal weights, static covariance, no transaction costs.\n"
        "- **Takeaway:** build the constraint into the circuit; the same symmetry gives free "
        "error detection on hardware."
    )
    png = FIGURES / "scaling.png"
    if png.exists():
        st.image(str(png), width="stretch")
    st.caption("Search-space sizes: C(20,10) = 184,756; C(100,50) ≈ 10²⁹.")

plt.close("all")  # figures were already sent to the browser; free them
