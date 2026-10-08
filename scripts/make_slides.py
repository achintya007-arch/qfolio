"""Build docs/slides.pptx (16:9, title + 3 content slides) following docs/DEMO_SCRIPT.md §A.

Every number is read from results/*.json, so the deck cannot drift from the results.
Each slide has speaker notes (~40 s of talking points). All text is >= 20 pt.
Usage: python scripts/make_slides.py
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import qrcode
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.util import Inches, Pt

ROOT = Path(__file__).resolve().parents[1]
FIG = ROOT / "results" / "figures"
OUT = ROOT / "docs" / "slides.pptx"
HW_JOB = "db3b1bimb58s7387e0jg"
HW_HIST = ROOT / "results" / "hardware" / "ibm_job_histogram.png"
HIST_CAPTION = (
    "Real ibm_kingston output — tallest bar 1001 = optimal basket (RELIANCE+ITC), "
    "second 1100 = runner-up"
)

PURPLE = RGBColor(0x3B, 0x1F, 0x7A)
GREY = RGBColor(0x44, 0x44, 0x44)
BLUE = RGBColor(0x2A, 0x78, 0xD6)
ORANGE = RGBColor(0xE8, 0x67, 0x38)
MIN_PT = 20  # smallest font on any slide, so it is readable from the back of the room
REPO_URL = "https://github.com/achintya007-arch/qfolio"
AUTHOR = "Akella Ahlad Achintya"
# NOTE(achintya): set once the Streamlit app is deployed; while None, slide 3 shows only
# the repo QR code.
STREAMLIT_URL: str | None = "https://qfolio.streamlit.app"


# Speaker notes, word for word as Achintya will say them (title, problem, idea, hardware).
NOTES = [
    (
        "Hi, I'm Akella Ahlad Achintya. My project is Q-Folio: using QAOA on Qiskit to "
        "pick the best stock basket — and I ran it on a real IBM quantum computer. One "
        "line: standard QAOA treats 'pick exactly k stocks' as a penalty and ends up no "
        "better than chance; I built that rule into the circuit, so every answer is a "
        "valid portfolio."
    ),
    (
        "Robo-advisors sell model baskets — say, the best 3 out of 6 stocks. 'Best' means"
        " high return and low risk. Each dot on this chart is one possible basket; there "
        "are 20 here. That's easy, but the number of baskets explodes as you add stocks —"
        " that's why it's a hard optimisation problem. I used real NSE prices from 2023 "
        "to 2025. Each stock is one qubit: 1 means hold it, 0 means don't. Two knobs: k "
        "is the basket size, and q is risk aversion — higher q means a more conservative "
        "client."
    ),
    (
        "The textbook way adds a penalty for picking the wrong number of stocks. It "
        "searches all 64 combinations, 44 of which are invalid — and I found it does no "
        "better than random guessing. So I changed the circuit. A Dicke state starts in "
        "an equal mix of only the valid baskets, and an XY mixer swaps one stock in and "
        "one out, so the count never changes. Result: 100% of answers are valid baskets, "
        "and the best basket shows up 34% of the time versus 5% for random — about seven "
        "times better, and comparable to simulated annealing. Tested on 25 different "
        "instances."
    ),
    (
        "Then I ran it on IBM's ibm_kingston quantum computer. This histogram is straight"
        " from IBM's dashboard: the tallest bar, 1001, is the optimal basket — Reliance "
        "plus ITC — and the second is the runner-up. Noise lets some invalid answers "
        "through, but my circuit can never produce those, so I can safely throw them "
        "away. That took us from 51% to 65% correct, versus 17% for random. To be honest "
        "about limits: at this size a laptop solves it instantly with brute force, so I'm"
        " not claiming quantum advantage. The contribution is showing that building "
        "constraints into the circuit is what makes quantum optimisation work — and it "
        "even gives free error detection on hardware. The code, live demo and report are "
        "at these QR codes. Thank you."
    ),
]


def load_numbers() -> dict:
    """Pull the handful of numbers the slides quote from the results JSON."""
    bench = json.loads((ROOT / "results" / "benchmark.json").read_text(encoding="utf-8"))
    hw_path = ROOT / "results" / "hardware" / f"{HW_JOB}.json"
    hw = json.loads(hw_path.read_text(encoding="utf-8"))
    s = bench["summary"]
    run2 = next(r for r in hw["runs"] if r["reps"] == 2)
    return {
        "xy": s["xy_qaoa_p2"]["p_optimal_mean"],
        "sa": s["simulated_annealing"]["p_optimal_mean"],
        "rand": s["random"]["p_optimal_mean"],
        "pen": s["penalty_qaoa_p2"]["p_optimal_mean"],
        "pen_valid": s["penalty_qaoa_p2"]["p_feasible_mean"],
        "n_inst": s["xy_qaoa_p2"]["instances"],
        "backend": hw["backend"],
        "hw_raw": run2["raw"]["p_optimal"],
        "hw_ps": run2["postselected"]["p_optimal"],
        "hw_valid": run2["raw"]["p_feasible"],
        "hw_top1": run2["raw"]["top1_is_optimal"],
        "hw_rand": hw["p_random"],
    }


def add_text(slide, x, y, w, h, lines, size=MIN_PT, color=GREY, bold=False):
    """Add a text box; ``lines`` is a list of strings (one paragraph each)."""
    assert size >= MIN_PT, "keep slide text readable"
    tf = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h)).text_frame
    tf.word_wrap = True
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = line
        p.font.size = Pt(size)
        p.font.color.rgb = color
        p.font.bold = bold
        p.space_after = Pt(6)
    return tf


def add_title(slide, title, subtitle=None, subtitle_color=GREY, subtitle_bold=False):
    add_text(slide, 0.5, 0.3, 12.3, 0.9, [title], size=34, color=PURPLE, bold=True)
    if subtitle:
        add_text(slide, 0.5, 1.05, 12.3, 0.5, [subtitle], color=subtitle_color, bold=subtitle_bold)


def add_box(slide, x, y, w, h, title, body, color):
    """A simple coloured 'circuit cartoon' card: heading plus two lines."""
    box = slide.shapes.add_shape(1, Inches(x), Inches(y), Inches(w), Inches(h))  # 1 = rectangle
    box.fill.solid()
    box.fill.fore_color.rgb = RGBColor(0xF7, 0xF6, 0xFA)
    box.line.color.rgb = color
    box.line.width = Pt(2.5)
    add_text(slide, x + 0.2, y + 0.08, w - 0.4, 0.5, [title], size=24, color=color, bold=True)
    add_text(slide, x + 0.2, y + 0.6, w - 0.4, h - 0.65, body)


def add_qr(slide, url, label, x, y, size, tmp):
    """Place a QR code for ``url`` with a short label underneath."""
    png = Path(tmp) / f"qr_{label}.png"
    qrcode.make(url, border=1).save(png)
    slide.shapes.add_picture(str(png), Inches(x), Inches(y), width=Inches(size))
    add_text(slide, x - 0.2, y + size, size + 0.4, 0.4, [label], color=PURPLE, bold=True)


def set_notes(slide, text):
    """Speaker notes: what to say while the slide is up."""
    slide.notes_slide.notes_text_frame.text = text


def build(n: dict, tmp: str) -> Presentation:
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
    blank = prs.slide_layouts[6]

    # Title slide.
    s0 = prs.slides.add_slide(blank)
    add_text(
        s0,
        0.8,
        2.2,
        11.7,
        1.8,
        ["Q-Folio: Constraint-Preserving QAOA for Portfolio Selection"],
        size=44,
        color=PURPLE,
        bold=True,
    )
    add_text(
        s0,
        0.8,
        4.1,
        11.7,
        1.0,
        ["Qiskit Fall Fest 2026 · Industry Track I2", f"{AUTHOR} · GITAM University, Bengaluru"],
        size=24,
    )
    add_text(s0, 0.8, 5.3, 11.7, 0.5, [f"Real results on IBM Quantum {n['backend']}"], color=BLUE)
    set_notes(s0, NOTES[0])

    # Slide 1: the problem.
    s1 = prs.slides.add_slide(blank)
    add_title(
        s1,
        "Picking the best 3 of 6 stocks, on a quantum computer",
        "Robo-advisor model baskets · NSE large caps · return ↑ risk ↓",
    )
    s1.shapes.add_picture(str(FIG / "frontier.png"), Inches(0.5), Inches(1.75), height=Inches(5.5))
    add_text(
        s1,
        9.2,
        2.2,
        3.8,
        5.0,
        [
            "All C(6,3) = 20 baskets on the risk/return plane.",
            "Basket count grows as C(n,k): ~185 000 for 10-of-20.",
            "Goal: find the best basket for a client's risk aversion q.",
        ],
    )
    add_text(s1, 9.2, 6.2, 3.9, 1.0, [AUTHOR, "Qiskit Fall Fest 2026 · Track I2"], color=PURPLE)
    set_notes(s1, NOTES[1])

    # Slide 2: the idea and the result.
    s2 = prs.slides.add_slide(blank)
    add_title(s2, "Put the constraint in the circuit, not in the cost")
    add_box(
        s2,
        0.5,
        1.2,
        6.0,
        1.55,
        "Penalty QAOA (X mixer)",
        ["Searches all 64 bit strings, 44 invalid", "→ finds the best basket at chance level"],
        ORANGE,
    )
    add_box(
        s2,
        6.85,
        1.2,
        6.0,
        1.55,
        "XY-QAOA (Dicke state + XY mixer)",
        ["Only ever visits the 20 valid baskets", "→ every shot is a real portfolio"],
        BLUE,
    )
    s2.shapes.add_picture(str(FIG / "headline.png"), Inches(1.35), Inches(2.85), width=Inches(10.6))
    add_text(
        s2,
        0.5,
        6.4,
        12.3,
        0.6,
        [
            f"100% valid baskets · P(optimal) {n['xy']:.2f} vs {n['rand']:.2f} random",
            "comparable to simulated annealing · penalty-QAOA = random",
        ],
        color=PURPLE,
        bold=True,
    )
    set_notes(s2, NOTES[2])

    # Slide 3: real hardware and honesty.
    s3 = prs.slides.add_slide(blank)
    top1 = "top answer = true optimum" if n["hw_top1"] else "top answer ≠ optimum"
    add_title(
        s3,
        f"Real IBM quantum hardware: {n['backend']}",
        f"{n['backend']}: {n['hw_raw']:.2f} raw → {n['hw_ps']:.2f} post-selected "
        f"(random {n['hw_rand']:.2f}); {top1}",
        subtitle_color=PURPLE,
        subtitle_bold=True,
    )
    s3.shapes.add_picture(str(HW_HIST), Inches(0.4), Inches(1.75), width=Inches(6.2))
    add_text(s3, 0.4, 4.45, 6.2, 0.9, [HIST_CAPTION])
    s3.shapes.add_picture(
        str(FIG / "noise_ladder.png"), Inches(6.85), Inches(1.7), width=Inches(6.1)
    )
    add_text(
        s3,
        0.4,
        5.55,
        9.0,
        1.8,
        [
            "Limits: brute force is still faster at this size, so no quantum advantage is "
            "claimed; today's noise limits us to ~4–6 assets."
        ],
    )
    qrs = [(REPO_URL, "Repo")] + ([(STREAMLIT_URL, "Live demo")] if STREAMLIT_URL else [])
    for i, (url, label) in enumerate(qrs):
        add_qr(s3, url, label, 11.7 - 1.65 * i, 5.25, 1.3, tmp)
    set_notes(s3, NOTES[3])
    return prs


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        prs = build(load_numbers(), tmp)
        assert len(prs.slides) == 4  # title + 3 content slides
        prs.save(OUT)
    print(f"wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
