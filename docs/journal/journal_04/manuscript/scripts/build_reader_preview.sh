#!/usr/bin/env bash
set -euo pipefail

# Compile the shared main.tex source in Elsevier 5p/two-column mode.
# This is a journal-style reader preview, not the publisher's typeset article.

cd "$(dirname "$0")/.."
export TEXMFVAR="${TEXMFVAR:-/tmp/texmf-var-rcrs-wpi}"
mkdir -p "$TEXMFVAR"

reader_input='\def\RCRSReader{1}\input{main.tex}'
pdflatex -interaction=nonstopmode -halt-on-error -jobname=reader_preview "$reader_input"
bibtex reader_preview
pdflatex -interaction=nonstopmode -halt-on-error -jobname=reader_preview "$reader_input"
pdflatex -interaction=nonstopmode -halt-on-error -jobname=reader_preview "$reader_input"
