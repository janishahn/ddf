#!/bin/bash
PROJECT_DIR="~/Documents/ddf"
cd "$PROJECT_DIR"
source .venv/bin/activate
uvicorn main:app --reload --port 8005 --host 0.0.0.0

