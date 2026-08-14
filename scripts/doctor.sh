#!/usr/bin/env bash
set -euo pipefail

fail=0
check() {
  local name="$1"
  local cmd="$2"
  if command -v "$cmd" >/dev/null 2>&1; then
    printf "[ok]   %-12s %s\n" "$name" "$(command -v "$cmd")"
  else
    printf "[miss] %-12s not found\n" "$name"
    fail=1
  fi
}

echo "ActivationLab environment check"
check "Python" python3
check "Node.js" node
check "npm" npm

if command -v docker >/dev/null 2>&1; then
  printf "[ok]   %-12s %s\n" "Docker" "$(command -v docker)"
else
  echo "[info] Docker is optional for fast local mode."
fi

if [ "$fail" -ne 0 ]; then
  echo "\nInstall missing required tools before running ./setup.sh"
  exit 1
fi

echo "\nRequired local tools are available."
