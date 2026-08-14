#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

if [ ! -d "$ROOT/backend/.venv" ] || [ ! -d "$ROOT/frontend/node_modules" ]; then
  echo "Dependencies are not installed. Run ./scripts/bootstrap-local.sh first."
  exit 1
fi

cleanup() {
  kill "${BACKEND_PID:-}" "${FRONTEND_PID:-}" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

cd "$ROOT/backend"
source .venv/bin/activate
export DB_ENGINE=sqlite
export USE_CELERY=0
python manage.py runserver 127.0.0.1:8000 &
BACKEND_PID=$!

cd "$ROOT/frontend"
npm run dev &
FRONTEND_PID=$!

printf '\nActivationLab is starting:\n  UI:  http://127.0.0.1:5173\n  API: http://127.0.0.1:8000/api/health/\n\nPress Ctrl+C to stop.\n'
wait
