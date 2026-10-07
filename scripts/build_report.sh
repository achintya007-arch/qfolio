#!/usr/bin/env bash
# Build the static HTML report in site/ (docs/07_CI_CD_AND_DEPLOYMENT.md §2).
# 1. execute the notebook → site/qfolio.html (uses committed results/, recomputes nothing heavy)
# 2. copy results/figures/* → site/figures/
# 3. write the landing page site/index.html (results table generated from results/*.json)
set -euo pipefail

PY="${PYTHON:-python}"
mkdir -p site
QFOLIO_FAST="${QFOLIO_FAST:-1}" "$PY" -m jupyter nbconvert --to html --execute \
  notebooks/qfolio.ipynb --output-dir site/

if [ -d results/figures ]; then
  mkdir -p site/figures
  cp -r results/figures/. site/figures/
fi

"$PY" scripts/build_landing.py site/index.html
echo "report written to site/"
