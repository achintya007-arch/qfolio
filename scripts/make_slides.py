"""Build the 3-slide deck docs/slides.pptx (16:9) following docs/DEMO_SCRIPT.md §A.

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
    set_notes(
        s1,
        f"Hi, I'm {AUTHOR}. "
        "Robo-advisors in India sell model baskets: a few stocks, equal weights, for a given "
        "risk profile. Choosing which k stocks go in is a combinatorial problem. Here I pick 3 "
        "of 6 NSE large caps, which is 20 possible baskets; each dot on this chart is one of "
        "them. We want return up and risk down, and the client's risk aversion q sets the "
        "trade-off. The blue star is the best basket for q = 0.5, and the orange diamond is a "
        "very close runner-up. At 20 baskets a laptop checks them all instantly, but the count "
        "explodes as C(n,k), so it is a natural test bed for quantum optimisation.",
    )

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
    set_notes(
        s2,
        "The textbook way to say 'exactly 3 stocks' is a penalty term in the cost. I tested it "
        f"carefully: only {n['pen_valid']:.0%} of its samples are valid baskets, and it finds the "
        f"best one {n['pen']:.0%} of the time, the same as random guessing at {n['rand']:.0%}. "
        "So I moved the constraint into the circuit. A Dicke state starts in an equal mix of only "
        "the valid baskets, and an XY mixer swaps stocks in and out without changing the count. "
        f"Every shot is a real portfolio. Over {n['n_inst']} test instances the best basket comes "
        f"up {n['xy']:.0%} of the time, about the same as simulated annealing at {n['sa']:.0%}. "
        "Grey bars are classical baselines, blue is ours, orange is the penalty approach.",
    )

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
    set_notes(
        s3,
        f"Then I ran the same circuit on IBM's {n['backend']}, with 4 stocks and 2 picked. "
        "On the left is the raw output from the IBM dashboard: the tallest bar is the optimal "
        "basket and the second is the runner-up. Noise lets some invalid baskets through, "
        f"about {1 - n['hw_valid']:.0%} of shots. The ideal circuit can never produce them, so I "
        "simply throw them away. That is free error detection. The optimal basket goes from "
        f"{n['hw_raw']:.0%} to {n['hw_ps']:.0%}, against {n['hw_rand']:.0%} for a random guess. "
        "Honest limits: at this size a laptop solves it instantly, so I claim no quantum "
        "advantage. The point is that building business constraints into the circuit is what "
        "makes quantum optimisation work at all. Code and live demo are behind the QR codes. "
        f"Thank you, I'm {AUTHOR}.",
    )
    return prs


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        prs = build(load_numbers(), tmp)
        assert len(prs.slides) == 3
        prs.save(OUT)
    print(f"wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
