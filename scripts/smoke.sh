#!/usr/bin/env bash
# Post-up smoke check: backend health and the LiveKit signaling port.
set -uo pipefail

fail=0

code="$(curl -s -o /dev/null -m 5 -w '%{http_code}' http://localhost:8000/health 2>/dev/null || echo 000)"
if [ "$code" = "200" ]; then
  echo "backend /health: ok (200)"
else
  echo "backend /health: FAIL (got $code)"
  fail=1
fi

if command -v nc >/dev/null 2>&1 && nc -z localhost 7880 2>/dev/null; then
  echo "livekit :7880: ok"
else
  echo "livekit :7880: FAIL (not reachable)"
  fail=1
fi

exit "$fail"
