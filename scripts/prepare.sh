#!/usr/bin/env bash
# First step of the initialize and update actions: check the inputs, pick the
# API for the environment, detect a build step and handle the Edge App id.
# Usage: prepare.sh initialize|update
set -euo pipefail

MODE="${1:-}"
case "$MODE" in
  initialize|update) ;;
  *)
    echo "::error::Usage: prepare.sh initialize|update"
    exit 1
    ;;
esac

if [ -z "${SCREENLY_API_TOKEN_INPUT:-}" ]; then
  echo "::error::screenly_api_token is empty. Add GitHub secret SCREENLY_API_TOKEN for this environment (stage and production both need a token)."
  exit 1
fi

# The name and title end up inside a double-quoted shell command run by
# screenly/cli, so reject characters that would break out of the quotes.
check_cli_arg() {
  if [ -z "$2" ]; then
    echo "::error::$1 is empty."
    exit 1
  fi
  case "$2" in
    *[\"\$\`\\]*)
      echo "::error::$1 must not contain \", \$, \` or \\."
      exit 1
      ;;
  esac
  if [[ "$2" =~ [[:cntrl:]] ]]; then
    echo "::error::$1 must not contain control characters (e.g. newlines)."
    exit 1
  fi
}
if [ "$MODE" = initialize ]; then
  check_cli_arg edge_app_name "${EDGE_APP_NAME_INPUT:-}"
  check_cli_arg edge_app_title "${EDGE_APP_TITLE_INPUT:-}"
fi

case "${ENVIRONMENT_INPUT:-}" in
  stage)
    echo "API_BASE_URL=https://api.screenlyappstage.com" >> "$GITHUB_ENV"
    ID_VAR=STAGE_EDGE_APP_ID
    ;;
  production)
    echo "API_BASE_URL=https://api.screenlyapp.com" >> "$GITHUB_ENV"
    ID_VAR=PRODUCTION_EDGE_APP_ID
    ;;
  *)
    echo "::error::environment must be 'stage' or 'production' (got '${ENVIRONMENT_INPUT:-}')."
    exit 1
    ;;
esac

# Apps with a build script are built and deployed from ./dist.
HAS_BUILD_STEP=false
if [ -f package.json ]; then
  # A parse error must stop here, not fall back to deploying the repo root.
  if ! BUILD_SCRIPT=$(jq -r '.scripts.build // empty' package.json); then
    echo "::error::Could not read scripts.build from package.json."
    exit 1
  fi
  if [ -n "$BUILD_SCRIPT" ]; then
    HAS_BUILD_STEP=true
  fi
fi
echo "has_build_step=$HAS_BUILD_STEP" >> "$GITHUB_OUTPUT"

# Apps without a build step are deployed from the repo root, and the CLI
# uploads every file there, hidden folders included.
if [ "$HAS_BUILD_STEP" = false ]; then
  if [ -s .ignore ] && [ -n "$(tail -c 1 .ignore)" ]; then
    echo >> .ignore
  fi
  for pattern in .git/ .github/ .claude/ node_modules/; do
    grep -qxF "$pattern" .ignore 2>/dev/null || echo "$pattern" >> .ignore
  done
fi
echo "MANIFEST_FILE_NAME=screenly.yml" >> "$GITHUB_ENV"

# Trim whitespace; treat Expression leftovers and placeholders as empty.
EDGE_APP_ID=$(printf '%s' "${EDGE_APP_ID_INPUT:-}" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
case "$(printf '%s' "$EDGE_APP_ID" | tr '[:upper:]' '[:lower:]')" in
  ''|false|true|null|none|0|undefined) EDGE_APP_ID= ;;
esac

if [ "$MODE" = initialize ]; then
  if [ -n "$EDGE_APP_ID" ]; then
    # A second run would create a second instance (and, if the variable were
    # later cleared, a second app). Deploys belong to update.
    echo "::error::This environment is already initialized (edge_app_id is ${EDGE_APP_ID}). Use the update action to deploy. To start over, delete the Edge App in Screenly and clear ${ID_VAR} first."
    exit 1
  fi
  echo "edge_app_id is empty: first-time create."
else
  if [ -z "$EDGE_APP_ID" ]; then
    echo "::error::edge_app_id is required for update. Set repo variable ${ID_VAR} to the id printed by initialize (do not use placeholders like 0 or false)."
    exit 1
  fi
  delimiter="ghadelim_${RANDOM}${RANDOM}${RANDOM}_$$"
  {
    echo "EDGE_APP_ID<<${delimiter}"
    echo "${EDGE_APP_ID}"
    echo "${delimiter}"
  } >> "$GITHUB_ENV"
  echo "Using EDGE_APP_ID=${EDGE_APP_ID}"
fi
