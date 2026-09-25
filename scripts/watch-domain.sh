#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   ./scripts/watch-domain.sh cleofields.com 300
#
# Arg 1: domain to monitor (required)
# Arg 2: check interval in seconds (optional, default 300)

DOMAIN="${1:-}"
INTERVAL="${2:-300}"
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

if [[ -z "$DOMAIN" ]]; then
  echo "Usage: $0 <domain> [interval_seconds]"
  exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "Error: Python 3 is required."
  exit 1
fi
if [[ ! "$INTERVAL" =~ ^[1-9][0-9]*$ ]]; then
  echo "Error: check interval must be a positive integer."
  exit 1
fi
PYTHONPATH="$script_dir" python3 -B -c 'import sys; from domain_status import registry_url; registry_url(sys.argv[1])' "$DOMAIN"

notify() {
  local title="$1"
  local message="$2"
  osascript -e "display notification \"${message}\" with title \"${title}\"" >/dev/null 2>&1 || true
}

last_state=""
last_raw_status=""

echo "Watching $DOMAIN every ${INTERVAL}s using registry RDAP"

auto_ts() {
  date '+%Y-%m-%d %H:%M:%S'
}

while true; do
  ts="$(auto_ts)"

  if ! result="$(python3 -B "$script_dir/domain_status.py" "$DOMAIN")"; then
    echo "[$ts] Registry check failed; retaining previous status and retrying"
    sleep "$INTERVAL"
    continue
  fi

  state="$(printf '%s' "$result" | python3 -c 'import json,sys; print(json.load(sys.stdin)["state"])')"
  raw_status="$(printf '%s' "$result" | python3 -c 'import json,sys; print(", ".join(json.load(sys.stdin)["statuses"]))')"

  if [[ "$state" != "$last_state" ]] || [[ "$raw_status" != "$last_raw_status" ]]; then
    echo "[$ts] State changed -> $state (${raw_status:-no-status-lines})"
    notify "Domain Watcher" "$DOMAIN -> $state"
    if [[ "$state" == "available" && "$state" != "$last_state" ]]; then
      notify "Domain AVAILABLE" "$DOMAIN has no registry record. Confirm with a registrar."
    fi
    last_state="$state"
    last_raw_status="$raw_status"
  else
    echo "[$ts] $DOMAIN -> $state"
  fi

  sleep "$INTERVAL"
done
