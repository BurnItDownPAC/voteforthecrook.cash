#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   ./scripts/watch-domain.sh cleofields.com 300
#
# Arg 1: domain to monitor (required)
# Arg 2: check interval in seconds (optional, default 300)

DOMAIN="${1:-}"
INTERVAL="${2:-300}"

if [[ -z "$DOMAIN" ]]; then
  echo "Usage: $0 <domain> [interval_seconds]"
  exit 1
fi

if ! command -v whois >/dev/null 2>&1; then
  echo "Error: 'whois' is required. Install it first."
  exit 1
fi

notify() {
  local title="$1"
  local message="$2"
  osascript -e "display notification \"${message}\" with title \"${title}\"" >/dev/null 2>&1 || true
}

classify_status() {
  local whois_out="$1"

  # If registry says no match / not found, domain is likely available.
  if echo "$whois_out" | grep -Eqi 'no match for|not found|status:\s*available'; then
    echo "available"
    return 0
  fi

  local statuses
  statuses="$(echo "$whois_out" | sed -nE 's/^Domain Status:[[:space:]]*([^ ]+).*/\1/ip' | tr '[:upper:]' '[:lower:]' | tr '\n' ',')"

  if [[ -z "$statuses" ]]; then
    echo "unknown"
    return 0
  fi

  if echo "$statuses" | grep -q 'pendingdelete'; then
    echo "pendingDelete"
  elif echo "$statuses" | grep -q 'redemptionperiod'; then
    echo "redemptionPeriod"
  elif echo "$statuses" | grep -q 'clienthold'; then
    echo "clientHold"
  elif echo "$statuses" | grep -q 'ok'; then
    echo "ok"
  else
    echo "other:${statuses%,}"
  fi
}

last_state=""
last_raw_status=""

echo "Watching $DOMAIN every ${INTERVAL}s"

auto_ts() {
  date '+%Y-%m-%d %H:%M:%S'
}

while true; do
  ts="$(auto_ts)"

  whois_out="$(whois "$DOMAIN" 2>/dev/null || true)"
  if [[ -z "$whois_out" ]]; then
    echo "[$ts] WHOIS empty/unavailable; retrying"
    sleep "$INTERVAL"
    continue
  fi

  state="$(classify_status "$whois_out")"
  raw_status="$(echo "$whois_out" | sed -nE 's/^Domain Status:[[:space:]]*([^ ]+).*/\1/ip' | tr '\n' ',' | sed 's/,$//')"

  if [[ "$state" != "$last_state" ]] || [[ "$raw_status" != "$last_raw_status" ]]; then
    echo "[$ts] State changed -> $state (${raw_status:-no-status-lines})"
    notify "Domain Watcher" "$DOMAIN -> $state"
    last_state="$state"
    last_raw_status="$raw_status"
  else
    echo "[$ts] $DOMAIN -> $state"
  fi

  if [[ "$state" == "available" ]]; then
    echo "[$ts] $DOMAIN appears available."
    notify "Domain AVAILABLE" "$DOMAIN may be available now"
    # Keep running in case of false positive / race conditions.
  fi

  sleep "$INTERVAL"
done
