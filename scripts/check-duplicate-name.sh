#!/usr/bin/env bash
# Refuses when an Edge App named EDGE_APP_NAME_INPUT already exists, so a
# second Initialize run can't create a duplicate. Fails closed: if the apps
# can't be listed, it stops instead of letting Initialize create one.
set -uo pipefail

BODY=$(mktemp)
STATUS=$(curl -s -o "$BODY" -w "%{http_code}" \
  --connect-timeout 10 \
  --max-time 30 \
  --retry 3 \
  --retry-delay 2 \
  -H "Authorization: Token ${SCREENLY_API_TOKEN_INPUT}" \
  "$API_BASE_URL/v4/edge-apps?select=id,name&deleted=eq.false") || true
if [ "$STATUS" != "200" ] || ! jq -e 'type == "array"' "$BODY" >/dev/null 2>&1; then
  echo "::error::Could not list existing Edge Apps in ${ENVIRONMENT_INPUT} (HTTP $STATUS), so a duplicate can't be ruled out. Nothing was created; re-run Initialize to try again."
  exit 1
fi
if ! EXISTING=$(jq -r --arg name "$EDGE_APP_NAME_INPUT" '[.[] | select(type == "object" and .name == $name) | .id | tostring] | join(", ")' "$BODY"); then
  echo "::error::Could not read the list of existing Edge Apps in ${ENVIRONMENT_INPUT}, so a duplicate can't be ruled out. Nothing was created; re-run Initialize to try again."
  exit 1
fi
if [ -n "$EXISTING" ]; then
  echo "::error::An Edge App named '${EDGE_APP_NAME_INPUT}' already exists in ${ENVIRONMENT_INPUT} (id: ${EXISTING}). If an earlier Initialize run for this repo created it and then failed, delete that app in Screenly and re-run Initialize (see README, 'Recovering from a failed Initialize'). If it is this repo's fully initialized app, set the ${ENVIRONMENT_INPUT} id variable to that id instead. Otherwise choose a different name."
  exit 1
fi
echo "No existing Edge App named '${EDGE_APP_NAME_INPUT}' in ${ENVIRONMENT_INPUT}."
