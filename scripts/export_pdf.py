"""Export a Markdown doc (e.g. the business brief) to PDF via HTML + Edge/Chrome headless.

Usage: python scripts/export_pdf.py docs/BUSINESS_BRIEF.md docs/BUSINESS_BRIEF.pdf
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import markdown

# Compact print styles so the brief fits on one A4 page.
CSS = """
@page { size: A4; margin: 14mm 16mm; }
body { font-family: 'Segoe UI', Arial, sans-serif; font-size: 10.2pt;
       line-height: 1.38; color: #111; }
h1 { font-size: 17pt; margin: 0 0 2px; color: #3b1f7a; }
p { margin: 5px 0; }
ul { margin: 3px 0 5px; padding-left: 18px; }
li { margin: 2px 0; }
code { font-family: Consolas, monospace; font-size: 0.9em; background: #f2f0f7; padding: 0 3px; }
a { color: #3b1f7a; }
sub { font-size: 8pt; color: #555; }
"""

BROWSERS = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    "msedge",
    "google-chrome",
    "chromium",
]


def find_browser() -> str:
    """Return the first available Chromium-based browser executable."""
    for b in BROWSERS:
        if Path(b).exists() or shutil.which(b):
            return b
    raise SystemExit("No Edge/Chrome found for headless PDF export.")


def html_to_pdf(html_path: Path, pdf_path: Path) -> None:
    """Print an HTML file to PDF with a headless Chromium browser."""
    subprocess.run(
        [
            find_browser(),
            "--headless",
            "--disable-gpu",
            "--no-pdf-header-footer",
            f"--print-to-pdf={pdf_path.resolve()}",
            html_path.resolve().as_uri(),
        ],
        check=True,
        capture_output=True,
    )


def main(src: str, dst: str) -> None:
    body = markdown.markdown(Path(src).read_text(encoding="utf-8"), extensions=["tables"])
    html = f"<!doctype html><meta charset='utf-8'><style>{CSS}</style><body>{body}</body>"
    with tempfile.TemporaryDirectory() as tmp:
        html_path = Path(tmp) / "doc.html"
        html_path.write_text(html, encoding="utf-8")
        html_to_pdf(html_path, Path(dst))
    print(f"wrote {dst}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
