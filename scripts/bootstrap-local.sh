#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

printf '\n[1/4] Creating Python environment...\n'
cd "$ROOT/backend"
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt

printf '\n[2/4] Migrating SQLite database...\n'
export DB_ENGINE=sqlite
export USE_CELERY=0
python manage.py migrate

printf '\n[3/4] Seeding demo experiment data...\n'
python manage.py seed_demo --sessions 120

printf '\n[4/4] Installing frontend packages...\n'
cd "$ROOT/frontend"
npm install

printf '\nDone. Start the app with: ./scripts/run-local.sh\n'
