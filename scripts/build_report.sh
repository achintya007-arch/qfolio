#!/usr/bin/env bash
# Build the static HTML report in site/ (docs/07_CI_CD_AND_DEPLOYMENT.md §2).
# 1. execute the notebook → site/qfolio.html
# 2. copy results/figures/* → site/figures/ (if any exist yet)
# 3. write a small landing page site/index.html
set -euo pipefail

mkdir -p site
jupyter nbconvert --to html --execute notebooks/qfolio.ipynb --output-dir site/

if [ -d results/figures ]; then
  mkdir -p site/figures
  cp -r results/figures/. site/figures/
fi

# NOTE(achintya): placeholder landing page; P6 adds the headline figure and results table.
cat > site/index.html <<'HTML'
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Q-Folio report</title>
</head>
<body>
  <h1>Q-Folio: constraint-preserving QAOA for portfolio selection</h1>
  <p>Qiskit Fall Fest 2026 &middot; Industry Track I2</p>
  <ul>
    <li><a href="qfolio.html">Executed notebook</a></li>
    <li><a href="https://github.com/achintya007-arch/qfolio">Repository</a></li>
  </ul>
</body>
</html>
HTML

echo "report written to site/"
