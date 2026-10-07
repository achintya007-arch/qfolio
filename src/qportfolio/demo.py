"""Checkpoint demo: ``python -m qportfolio.demo``.

Builds the default instance (configs/default.yaml), draws the p=1 XY-QAOA circuit, optimises
and samples it on the ideal statevector simulator, and compares it with penalty-QAOA p=1 and
the brute-force optimum. Set ``QFOLIO_FAST=1`` for fewer restarts and shots.
"""

from __future__ import annotations

import sys

from qiskit import QuantumCircuit
from qiskit.circuit import Parameter
from qiskit.circuit.library import PauliEvolutionGate

from qportfolio.circuits import build_qaoa, dicke_state, xy_ring_mixer
from qportfolio.classical import brute_force
from qportfolio.config import load_config
from qportfolio.data import load_prices, returns_stats
from qportfolio.metrics import evaluate_counts
from qportfolio.problem import PortfolioProblem, bitstring_to_x, x_to_bitstring
from qportfolio.qaoa import optimize, sample


def default_problem() -> PortfolioProblem:
    """Build the headline instance from the cached NSE prices and the default config."""
    cfg = load_config().raw
    d, prob = cfg["data"], cfg["problem"]
    mu, sigma = returns_stats(load_prices(d["path"], d["tickers"], d["start"], d["end"]))
    labels = tuple(t.removesuffix(".NS") for t in d["tickers"])
    return PortfolioProblem(mu, sigma, k=prob["k"], q=prob["q"], labels=labels)


def basket(p: PortfolioProblem, bits: str) -> str:
    """Human-readable basket for a Qiskit bitstring, e.g. ``"TCS+ITC+LT (101010)"``."""
    x = bitstring_to_x(bits)
    names = "+".join(name for name, b in zip(p.labels, x, strict=True) if b) or "∅"
    flag = "" if x.sum() == p.k else ", infeasible"
    return f"{names} ({bits}{flag})"


def block_diagram(p: PortfolioProblem) -> QuantumCircuit:
    """p=1 XY-QAOA drawn as blocks: Dicke(n, k) → exp(−iγH) → XY-ring mixer.

    NOTE(achintya): same building blocks as ``build_qaoa``, but the Dicke state and cost layer
    stay boxed. Drawing the decomposed ansatz prints ~70 KB of gates, useless on a slide.
    """
    qc = QuantumCircuit(p.n)
    qc.append(dicke_state(p.n, p.k).to_gate(label=f"Dicke({p.n},{p.k})"), range(p.n))
    qc.append(PauliEvolutionGate(p.to_ising(0.0), Parameter("γ"), label="exp(-iγH)"), range(p.n))
    return qc.compose(xy_ring_mixer(p.n))


def main() -> None:
    """Run the checkpoint demo."""
    # Windows consoles default to cp1252, which cannot print the circuit's box characters.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    cfg = load_config()
    q = cfg.raw["qaoa"]
    p = default_problem()
    best, costs = brute_force(p)
    optimum = basket(p, x_to_bitstring(best.x))
    print(f"Instance: n = {p.n} assets, pick k = {p.k}, q = {p.q}  ({', '.join(p.labels)})")
    print(f"Random guess P(optimal) = 1/{len(costs)} = {1 / len(costs):.3f}\n")

    rows = []
    for variant in ("xy", "penalty"):
        ansatz, H = build_qaoa(p, reps=1, variant=variant)
        if variant == "xy":
            print("XY-QAOA, p = 1  (Dicke state → cost layer → XY-ring mixer):")
            print(block_diagram(p).draw(output="text", fold=120))
            cx = ansatz.count_ops()["cx"]
            print(f"decomposed: depth {ansatz.depth()}, {cx} CNOTs (before transpiling)\n")
        res = optimize(ansatz, H, restarts=q["restarts"], maxiter=q["maxiter"], seed=cfg.seed)
        counts = sample(ansatz, res.params, shots=q["shots"], seed=cfg.seed)
        m = evaluate_counts(counts, p, costs, best.x)
        top1 = max(counts, key=counts.get)  # most frequent bitstring overall
        rows.append((f"{variant}-QAOA p=1", m["p_feasible"], m["p_optimal"], basket(p, top1)))

    header = ("method", "P(feasible)", "P(optimal)", "top-1 basket", "brute-force optimum")
    print(" | ".join(header))
    print(" | ".join("-" * len(h) for h in header))
    for name, pf, po, top in rows:
        print(f"{name} | {pf:.3f} | {po:.3f} | {top} | {optimum}")
    print(f"\n({q['shots']} shots, ideal statevector simulator, seed {cfg.seed})")


if __name__ == "__main__":
    main()
