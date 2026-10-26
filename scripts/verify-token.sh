#!/usr/bin/env bash
# Fails unless SCREENLY_API_TOKEN_INPUT is accepted by the API at API_BASE_URL.
set -euo pipefail

STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
  --connect-timeout 10 \
  --max-time 30 \
  --retry 3 \
  --retry-delay 2 \
  -H "Authorization: Token ${SCREENLY_API_TOKEN_INPUT}" \
  "$API_BASE_URL/api/v4.1/users/") || true
echo "Auth check status: $STATUS"
if [ "$STATUS" != "200" ]; then
  echo "::error::SCREENLY_API_TOKEN validation failed for ${ENVIRONMENT_INPUT} (HTTP $STATUS). Check the secret for this environment."
  exit 1
fi
echo "Token is valid"
