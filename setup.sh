#!/usr/bin/env bash
#
# Create a fresh conda environment for the llm-wiki repo.
# The skill scripts under .claude/skills/ and their unittest suites are
# standard-library only, so no test framework is needed. The ingest skill's
# figure extraction needs three runtime tools: PyMuPDF (pip) plus ImageMagick
# and Poppler (conda-forge, providing `magick`, `pdftoppm`, and `pdfimages`).
# black and ruff are the formatter and linter; both read their settings
# from pyproject.toml, which pins the single-quote, 79-column house
# style.
#
# Usage:
#   bash setup.sh
#
# After it finishes, activate the env with: conda activate llm-wiki

set -euo pipefail

# Name of the conda env to create and the Python version to pin it to.
ENV_NAME='llm-wiki'
PYTHON_VERSION='3.12'

# Create the conda env non-interactively. The -y flag auto-accepts
# the install prompt so the script can run end-to-end unattended.
echo "Creating conda env '${ENV_NAME}' with Python ${PYTHON_VERSION}."
conda create -n "${ENV_NAME}" "python=${PYTHON_VERSION}" -y

# Source conda's shell hook so 'conda activate' works inside this
# non-interactive script (the default shell init only runs for
# interactive sessions).
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate "${ENV_NAME}"

# System tools for the ingest skill's PDF figure extraction: ImageMagick
# provides `magick` (crop/convert), Poppler provides `pdftoppm` (page render)
# and `pdfimages` (embedded-raster pull). Installed from conda-forge into the
# env so they don't depend on a separate system package manager.
echo 'Installing ImageMagick and Poppler (ingest figure extraction).'
conda install -n "${ENV_NAME}" -c conda-forge imagemagick poppler -y

# Upgrade pip itself before installing packages so we get the latest
# resolver behavior and avoid warnings from stale pip versions.
echo 'Upgrading pip.'
pip install --upgrade pip

# Runtime dependency for the ingest skill's PDF figure extraction.
echo 'Installing PyMuPDF (ingest figure extraction).'
pip install \
    'PyMuPDF>=1.28.0'

# Formatter and linter for the skill scripts. Installed into the env
# rather than relied on globally: a global ruff or black sees no
# pyproject.toml and falls back to double quotes, silently reformatting
# the scripts away from the house style. Both read their settings from
# pyproject.toml at the repo root.
echo 'Installing ruff and black (formatter and linter).'
pip install \
    'ruff>=0.15' \
    'black>=26.5'

echo ''
echo "Done. Activate the env with: conda activate ${ENV_NAME}"
