"""Shared test setup: headless matplotlib (CI sets MPLBACKEND=Agg; local Windows uses Tk)."""

import matplotlib

matplotlib.use("Agg")
