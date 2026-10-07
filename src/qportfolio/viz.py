"""One matplotlib function per figure (docs/05_BENCHMARK_PROTOCOL.md §7).

Every figure is saved as PNG (dpi 200) and SVG via :func:`save_figure`. Functions take plain
dicts (loaded from ``results/*.json``) and return a ``Figure``; they never read files.

Colours: a colour-blind-safe set (blue / orange / aqua, validated for deuteranopia,
protanopia and tritanopia) plus neutral grey for classical baselines. Colour is never the only
cue: every bar is also labelled on the axis and with its value.
"""

from __future__ import annotations

from math import comb
from pathlib import Path
from typing import TYPE_CHECKING, Any

import matplotlib.pyplot as plt
import numpy as np

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from matplotlib.figure import Figure

XY = "#2a78d6"  # blue: XY-QAOA (our method)
PENALTY = "#eb6834"  # orange: penalty-QAOA
AQUA = "#1baf7a"  # aqua: second series where needed (p = 2)
CLASSICAL = "#8c8a85"  # neutral grey: classical baselines
INK = "#24231f"  # text, reference lines
MUTED = "#6b6a65"

STYLE = {
    "font.size": 13,
    "axes.titlesize": 14,
    "axes.titleweight": "bold",
    "axes.labelsize": 13,
    "axes.edgecolor": MUTED,
    "axes.labelcolor": INK,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "axes.grid.axis": "y",
    "grid.color": "#e4e3df",
    "grid.linewidth": 0.8,
    "axes.axisbelow": True,
    "xtick.color": INK,
    "ytick.color": INK,
    "legend.frameon": False,
    "svg.fonttype": "none",  # keep text as text in the SVG (editable, searchable)
}

LABELS = {
    "random": "Random",
    "brute_force": "Brute\nforce",
    "greedy": "Greedy",
    "simulated_annealing": "Sim.\nanneal.",
    "penalty_qaoa_p1": "Penalty\np=1",
    "penalty_qaoa_p2": "Penalty\np=2",
    "xy_qaoa_p1": "XY\np=1",
    "xy_qaoa_p2": "XY\np=2",
    "xy_qaoa_p3": "XY\np=3",
}


def _colour(method: str) -> str:
    if method.startswith("xy_"):
        return XY
    if method.startswith("penalty_"):
        return PENALTY
    return CLASSICAL


def _methods(benchmark: dict[str, Any]) -> list[str]:
    """Method names in benchmark order, without the analytic random floor (drawn as a line)."""
    return [m for m in benchmark["instances"][0]["methods"] if m != "random"]


def _bar_labels(ax: Axes, bars: Any, values: Any, fmt: str = "{:.2f}", above: Any = None) -> None:
    """Value label on each bar; ``above`` (e.g. mean + std) lifts it clear of error bars."""
    tops = above if above is not None else [b.get_height() for b in bars]
    for bar, v, top in zip(bars, values, tops, strict=True):
        ax.annotate(
            fmt.format(v),
            (bar.get_x() + bar.get_width() / 2, top),
            xytext=(0, 3),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=10,
            color=INK,
        )


def _random_line(ax: Axes, y: float, label: str | None = "random") -> None:
    ax.axhline(y, color=INK, linestyle="--", linewidth=1.5, zorder=3)
    if label is None:  # caller puts the value somewhere collision-free (e.g. the title)
        return
    ax.annotate(
        f"{label} {y:.2f}",
        (1.0, y),
        xycoords=("axes fraction", "data"),
        xytext=(-2, 4),
        textcoords="offset points",
        ha="right",
        va="bottom",
        fontsize=10,
        color=INK,
    )


def save_figure(fig: Figure, name: str, outdir: str | Path = "results/figures") -> Path:
    """Save ``fig`` as ``<name>.png`` (dpi 200) and ``<name>.svg``; return the PNG path."""
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    png = outdir / f"{name}.png"
    fig.savefig(png, dpi=200, bbox_inches="tight", facecolor="white")
    # Fixed metadata so re-running does not change the SVG bytes (no timestamp diff noise).
    fig.savefig(
        outdir / f"{name}.svg", bbox_inches="tight", facecolor="white", metadata={"Date": None}
    )
    plt.close(fig)
    return png


def headline(benchmark: dict[str, Any]) -> Figure:
    """P(optimal), approximation ratio and P(top-2) by method, each with a dashed random line.

    Bars = the headline real-data instance; black dots with whiskers = robustness-set
    mean ± std, so one lucky instance cannot carry the slide.
    """
    head = benchmark["instances"][0]
    methods = _methods(benchmark)
    summary = benchmark["summary"]
    panels = [
        ("p_optimal", "P(optimal)"),
        ("approx_ratio", "Approximation ratio"),
        ("p_top2", "P(top-2 baskets)"),
    ]
    x = np.arange(len(methods))
    with plt.rc_context(STYLE):
        fig, axes = plt.subplots(1, 3, figsize=(18, 5.6), sharey=True)
        for ax, (key, title) in zip(axes, panels, strict=True):
            vals = [head["methods"][m][key] for m in methods]
            bars = ax.bar(
                x - 0.12,
                vals,
                width=0.6,
                color=[_colour(m) for m in methods],
                edgecolor="white",
                linewidth=2,
            )
            _bar_labels(ax, bars, vals)
            means = [summary[m][f"{key}_mean"] for m in methods]
            stds = [summary[m][f"{key}_std"] for m in methods]
            ax.errorbar(
                x + 0.3,
                means,
                yerr=stds,
                fmt="o",
                color=INK,
                markersize=5,
                capsize=3,
                linewidth=1.2,
                zorder=4,
            )
            rnd = head["methods"]["random"][key]
            _random_line(ax, rnd, label=None)
            ax.set_title(f"{title}   (random = {rnd:.2f})")
            ax.set_xticks(x, [LABELS[m] for m in methods], fontsize=11)
            ax.set_ylim(0, 1.12)
        axes[0].set_ylabel("Score (1 = always the best basket)")
        n_rob = summary[methods[0]]["instances"]
        handles = [
            plt.Rectangle((0, 0), 1, 1, color=CLASSICAL, label="Classical baseline"),
            plt.Rectangle((0, 0), 1, 1, color=PENALTY, label="Penalty-QAOA"),
            plt.Rectangle((0, 0), 1, 1, color=XY, label="XY-QAOA (ours)"),
            plt.Line2D(
                [],
                [],
                marker="o",
                color=INK,
                linestyle="none",
                label=f"mean ± std over {n_rob} robustness instances",
            ),
            plt.Line2D([], [], color=INK, linestyle="--", label="uniform random basket"),
        ]
        fig.legend(handles=handles, loc="lower center", ncol=5, bbox_to_anchor=(0.5, -0.06))
        tickers = ", ".join(t.removesuffix(".NS") for t in head["tickers"])
        fig.suptitle(
            f"Headline instance: pick {head['k']} of {head['n']} NSE stocks "
            f"({tickers}), q = {head['q']}  ·  ideal simulator",
            fontsize=15,
            fontweight="bold",
        )
        fig.tight_layout(rect=(0, 0.04, 1, 1))
    return fig


def feasibility(benchmark: dict[str, Any]) -> Figure:
    """P(feasible) for penalty vs XY QAOA across reps p (robustness mean ± std)."""
    summary = benchmark["summary"]
    reps = sorted({int(m.rsplit("p", 1)[1]) for m in summary if "_qaoa_p" in m})
    width = 0.38
    with plt.rc_context(STYLE):
        fig, ax = plt.subplots(figsize=(9, 5.4))
        for offset, variant, colour, name in (
            (-width / 2, "penalty", PENALTY, "Penalty-QAOA"),
            (width / 2, "xy", XY, "XY-QAOA (ours)"),
        ):
            ps = [r for r in reps if f"{variant}_qaoa_p{r}" in summary]
            means = [summary[f"{variant}_qaoa_p{r}"]["p_feasible_mean"] for r in ps]
            stds = [summary[f"{variant}_qaoa_p{r}"]["p_feasible_std"] for r in ps]
            bars = ax.bar(
                np.array(ps) + offset,
                means,
                width,
                yerr=stds,
                color=colour,
                edgecolor="white",
                linewidth=2,
                capsize=4,
                label=name,
                error_kw={"ecolor": INK, "linewidth": 1.2},
            )
            _bar_labels(ax, bars, means, above=np.add(means, stds))
        n = benchmark["instances"][0]["n"]
        k = benchmark["instances"][0]["k"]
        _random_line(ax, comb(n, k) / 2**n, label=f"random bitstring C({n},{k})/2^{n} =")
        ax.set_xticks(reps, [f"p = {r}" for r in reps])
        ax.set_ylim(0, 1.15)
        ax.set_xlabel("QAOA depth")
        ax.set_ylabel(f"P(feasible): share of shots with exactly {k} assets")
        ax.set_title(
            f"Valid portfolios ({summary['xy_qaoa_p1']['instances']} instances, mean ± std)"
        )
        ax.legend(loc="upper left", ncol=2)
        fig.tight_layout()
    return fig


def distribution(benchmark: dict[str, Any], method: str | None = None) -> Figure:
    """Probability of each feasible basket (ranked by cost) for XY-QAOA vs uniform random.

    ``method`` defaults to the XY-QAOA depth with the highest P(optimal) on the headline
    instance. Ranking by cost (1 = optimum) keeps near-tied baskets apart on the x-axis.
    """
    head = benchmark["instances"][0]
    if method is None:
        xy = [m for m in head["methods"] if m.startswith("xy_")]
        method = max(xy, key=lambda m: head["methods"][m]["p_optimal"])
    counts = head["counts"][method]
    shots = sum(counts.values())
    baskets = sorted(head["baskets"], key=lambda b: b["cost"])
    probs = [counts.get(b["bits"], 0) / shots for b in baskets]
    rank = np.arange(1, len(baskets) + 1)
    with plt.rc_context(STYLE):
        fig, ax = plt.subplots(figsize=(11, 5.4))
        colours = [XY] * len(rank)
        bars = ax.bar(
            rank,
            probs,
            width=0.75,
            color=colours,
            edgecolor="white",
            linewidth=2,
            label=f"{LABELS[method].replace(chr(10), ' ')} QAOA samples",
        )
        _bar_labels(ax, bars[:3], probs[:3])
        _random_line(ax, 1 / len(baskets), label="uniform random 1/" + str(len(baskets)) + " =")
        best = baskets[0]
        ax.annotate(
            f"optimum: {'+'.join(best['assets'])}",
            (1, probs[0]),
            xytext=(len(baskets) * 0.3, max(probs) * 0.75),
            textcoords="data",
            fontsize=11,
            color=INK,
            arrowprops={"arrowstyle": "->", "color": INK},
        )
        ax.set_xticks(rank)
        ax.set_xlabel(
            f"Feasible basket, ranked by cost C(x)  (1 = optimum, {len(baskets)} = worst)"
        )
        ax.set_ylabel("Probability")
        ax.set_title(f"Where the shots land: headline instance, {shots} shots")
        ax.legend(loc="upper right")
        fig.tight_layout()
    return fig


def noise_ladder(
    ideal: dict[str, dict[str, Any]],
    dry_run: dict[str, Any],
    hardware: dict[str, Any],
) -> Figure:
    """P(optimal) down the ladder: ideal → fake noisy → real raw → post-selected → + mitigated.

    ``ideal`` maps reps (as str) to ``evaluate_counts`` output on the exact statevector with the
    same angles; ``dry_run`` / ``hardware`` are ``results/hardware/*.json``. The last rung is
    post-selection applied to the readout-mitigated distribution (both corrections together).
    """
    hw_runs = {str(r["reps"]): r for r in hardware["runs"]}
    fake_runs = {str(r["reps"]): r for r in dry_run["runs"]}
    reps = sorted(hw_runs, key=int)
    backend = hardware["backend"]
    rungs = [
        "Ideal\n(statevector)",
        f"{dry_run['backend']}\nnoisy sim, raw",
        f"{backend}\nraw",
        f"{backend}\npost-selected",
        f"{backend}\npost-sel. +\nreadout-mit.",
    ]

    def values(r: str) -> list[float]:
        hw = hw_runs[r]
        return [
            ideal[r]["p_optimal"],
            fake_runs[r]["raw"]["p_optimal"],
            hw["raw"]["p_optimal"],
            hw["postselected"]["p_optimal"],
            hw["mitigated"]["p_optimal_postselected"],  # post-select the mitigated distribution
        ]

    width = 0.38
    x = np.arange(len(rungs))
    inst = hardware["instance"]
    with plt.rc_context(STYLE):
        fig, ax = plt.subplots(figsize=(12, 5.8))
        for i, (r, colour) in enumerate(zip(reps, (XY, AQUA), strict=False)):
            vals = values(r)
            bars = ax.bar(
                x + (i - 0.5) * width,
                vals,
                width,
                color=colour,
                edgecolor="white",
                linewidth=2,
                label=f"XY-QAOA p = {r}",
            )
            _bar_labels(ax, bars, vals)
        _random_line(ax, hardware["p_random"], label="random guess")
        ax.axvspan(1.5, len(rungs) - 0.5, color="#f1f0ec", zorder=0)
        ax.text(
            len(rungs) - 0.55,
            0.97,
            f"real IBM hardware, job {hardware['job_id']}",
            ha="right",
            va="top",
            fontsize=10,
            color=MUTED,
            transform=ax.get_xaxis_transform(),
        )
        ax.set_xticks(x, rungs, fontsize=11)
        ax.set_ylim(0, 1.05)
        ax.set_ylabel("P(optimal basket)")
        tick = "+".join(t.removesuffix(".NS") for t in inst["tickers"])
        ax.set_title(
            f"Noise ladder: pick {inst['k']} of {len(inst['tickers'])} ({tick}), "
            f"{hardware['shots']} shots"
        )
        ax.legend(loc="upper left", ncol=2)
        fig.tight_layout()
    return fig


def transpile(noisy: dict[str, Any]) -> Figure:
    """Depth, 2-qubit gate count and estimated fidelity vs optimisation level, per backend.

    Colour = backend, line style + marker = QAOA depth p (so identity is not colour-only).
    """
    panels = [
        ("depth", "Circuit depth"),
        ("two_qubit_gates", "Two-qubit gates"),
        ("est_fidelity", "Estimated fidelity"),
    ]
    styles = {"1": ("-", "o"), "2": ("--", "s"), "3": (":", "^")}
    with plt.rc_context({**STYLE, "axes.grid.axis": "both"}):
        fig, axes = plt.subplots(1, 3, figsize=(16, 5.2))
        for (name, data), colour in zip(noisy["backends"].items(), (XY, PENALTY), strict=False):
            for reps, rows in data["transpile"].items():
                ls, marker = styles.get(reps, ("-", "o"))
                levels = [r["level"] for r in rows]
                for ax, (key, _) in zip(axes, panels, strict=True):
                    ax.plot(
                        levels,
                        [r[key] for r in rows],
                        linestyle=ls,
                        marker=marker,
                        color=colour,
                        linewidth=2,
                        markersize=8,
                        label=f"{name}, p = {reps}",
                    )
        for ax, (_, title) in zip(axes, panels, strict=True):
            ax.set_title(title)
            ax.set_xlabel("Transpiler optimisation level")
            ax.set_xticks([0, 1, 2, 3])
        axes[2].set_ylim(0, 1)
        axes[0].legend(loc="upper right", fontsize=11)
        inst = noisy["instance"]
        fig.suptitle(
            f"Transpiling XY-QAOA ({len(inst['tickers'])} qubits, pick {inst['k']}) "
            "for IBM Heron devices",
            fontsize=15,
            fontweight="bold",
        )
        fig.tight_layout()
    return fig


def frontier(benchmark: dict[str, Any]) -> Figure:
    """Risk vs return of all C(n, k) baskets with the optimum (and runner-up) highlighted."""
    head = benchmark["instances"][0]
    baskets = sorted(head["baskets"], key=lambda b: b["cost"])
    xy = [m for m in head["methods"] if m.startswith("xy_")]
    star_label = "optimum"
    if xy and head["methods"][xy[0]]["top1_is_optimal"]:
        star_label = "optimum (= XY-QAOA's most frequent answer)"
    risk = np.array([b["risk"] for b in baskets]) * 100
    ret = np.array([b["return"] for b in baskets]) * 100
    with plt.rc_context({**STYLE, "axes.grid.axis": "both"}):
        fig, ax = plt.subplots(figsize=(9.5, 6.2))
        ax.scatter(
            risk[2:],
            ret[2:],
            s=70,
            color=CLASSICAL,
            edgecolor="white",
            linewidth=1.5,
            label=f"other baskets ({len(baskets) - 2})",
            zorder=3,
        )
        ax.scatter(
            risk[1],
            ret[1],
            s=140,
            marker="D",
            color=PENALTY,
            edgecolor="white",
            linewidth=1.5,
            label="runner-up",
            zorder=4,
        )
        ax.scatter(
            risk[0],
            ret[0],
            s=320,
            marker="*",
            color=XY,
            edgecolor="white",
            linewidth=1.5,
            label=star_label,
            zorder=5,
        )
        for i, dx in ((0, 10), (1, 10)):
            ax.annotate(
                "+".join(baskets[i]["assets"]),
                (risk[i], ret[i]),
                xytext=(dx, -4),
                textcoords="offset points",
                fontsize=11,
                color=INK,
            )
        ax.set_xlabel("Risk: annualised volatility of the equal-weight basket (%)")
        ax.set_ylabel("Annualised return (%)")
        ax.set_title(f"All {len(baskets)} baskets of {head['k']} stocks  ·  q = {head['q']}")
        ax.legend(loc="best")
        fig.tight_layout()
    return fig


def scaling(rows: list[dict[str, Any]], hardware: dict[str, Any] | None = None) -> Figure:
    """Search-space size and p=1 XY-QAOA 2-qubit gate count vs n; honest context, no timing.

    Two panels instead of a dual axis. ``rows`` comes from ``benchmark.scaling_rows``; the
    optional ``hardware`` JSON adds the measured post-routing gate count on the real device.
    """
    n = np.array([r["n"] for r in rows])
    with plt.rc_context({**STYLE, "axes.grid.axis": "both"}):
        fig, (a1, a2) = plt.subplots(1, 2, figsize=(14, 5.4))
        a1.semilogy(
            n,
            [r["all_bitstrings"] for r in rows],
            "o-",
            color=PENALTY,
            linewidth=2,
            markersize=8,
            label="all bitstrings 2ⁿ (penalty-QAOA explores)",
        )
        a1.semilogy(
            n,
            [r["feasible"] for r in rows],
            "s-",
            color=XY,
            linewidth=2,
            markersize=8,
            label="valid baskets C(n, n/2) (XY-QAOA explores)",
        )
        a1.set_xlabel("Number of candidate assets n (= qubits)")
        a1.set_ylabel("Number of states (log scale)")
        a1.set_title("Search space")
        a1.legend(loc="upper left")
        a2.plot(
            n,
            [r["two_qubit_gates"] for r in rows],
            "s-",
            color=XY,
            linewidth=2,
            markersize=8,
            label="logical, all-to-all (transpiled)",
        )
        if hardware is not None:
            tq = hardware["transpiled"][0]["two_qubit_gates"]
            a2.plot(
                len(hardware["instance"]["tickers"]),
                tq,
                "*",
                color=INK,
                markersize=16,
                label=f"{hardware['backend']} after routing",
            )
        for r in rows:
            a2.annotate(
                str(r["two_qubit_gates"]),
                (r["n"], r["two_qubit_gates"]),
                xytext=(-6, 8),
                textcoords="offset points",
                fontsize=10,
                color=INK,
                ha="right",
            )
        a2.set_xlabel("Number of candidate assets n (= qubits), k = n/2")
        a2.set_ylabel("Two-qubit gates, p = 1")
        a2.set_title("Circuit cost of XY-QAOA (p = 1)")
        a2.legend(loc="upper left")
        for ax in (a1, a2):
            ax.set_xticks(n)
        fig.tight_layout()
    return fig
