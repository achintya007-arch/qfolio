# ADR-0004: GitHub Pages report as primary deployment, Streamlit Cloud as live demo

**Status:** Accepted · 2026-10-07

## Context
Judges need a link that always works, with no install. A live app is more impressive but can be cold-started or rate-limited.

## Decision
- Primary: a static HTML report (executed notebook + figures) built by GitHub Actions and deployed to GitHub Pages.
- Secondary: a Streamlit Community Cloud app that auto-deploys from `main`.
- Fallback: Hugging Face Spaces (Docker).

## Consequences
+ Zero-cost, zero-secret CI/CD; the report is always available.
− Two deployment surfaces to keep in sync. Both read the same `results/` JSON.
