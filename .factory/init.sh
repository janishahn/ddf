#!/bin/bash
set -e

# Frontend dependencies
cd /Users/janishahn/Documents/PythonProjects/ddf/frontend
if [ ! -d "node_modules" ]; then
  npm install
fi

# Verify Python environment (backend uses uv)
cd /Users/janishahn/Documents/PythonProjects/ddf
if ! command -v uv &> /dev/null; then
  echo "Installing uv..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
fi

echo "Environment ready."
