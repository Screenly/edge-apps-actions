# edge-apps-actions

Composite GitHub Actions for Screenly Edge Apps.

## Example workflows

Copy these into your app repo under `.github/workflows/`:

- [`examples/initialize-edge-app.yml`](examples/initialize-edge-app.yml) — manual create/deploy for stage or production
- [`examples/update-edge-app.yml`](examples/update-edge-app.yml) — deploy stage from `development`, production from `main`

Branch names are only used in your workflow triggers (`on.push.branches` / `github.ref`). The actions themselves work the same on `main` or `master` — change the branch names in the example to match your repo.

After the first successful initialize, store the printed Edge App id in repo variables `STAGE_EDGE_APP_ID` / `PRODUCTION_EDGE_APP_ID` and pass them as `edge_app_id` on later runs. Leave those vars **unset** (do not use placeholders like `0` or `false`) until create has printed a real id — any non-empty string is treated as an app id.

## Available Actions

### `checks`

Builds, lints, formats, and tests a Screenly Edge App.

```yaml
- uses: Screenly/edge-apps-actions/checks@v1
  with:
    bun-version: latest # optional
```

| Input         | Description        | Required | Default  |
| ------------- | ------------------ | -------- | -------- |
| `bun-version` | Bun version to use | No       | `latest` |

### `initialize`

Creates and deploys a new Screenly Edge App instance.

```yaml
- uses: Screenly/edge-apps-actions/initialize@v1
  with:
    screenly_api_token: ${{ secrets.SCREENLY_API_TOKEN }}
    edge_app_name: my-edge-app
    edge_app_title: My Edge App
    environment: ${{ inputs.environment }} # stage or production
    # First create: leave the matching var unset so this resolves to "".
    # After create: set STAGE_EDGE_APP_ID / PRODUCTION_EDGE_APP_ID to the printed id.
    edge_app_id: ${{ (inputs.environment == 'production' && vars.PRODUCTION_EDGE_APP_ID) || (inputs.environment == 'stage' && vars.STAGE_EDGE_APP_ID) || '' }}
```

| Input                | Description                                    | Required | Default |
| -------------------- | ---------------------------------------------- | -------- | ------- |
| `screenly_api_token` | Screenly API token                             | Yes      |         |
| `edge_app_name`      | Edge App name (used for the CLI `--name` flag) | Yes      |         |
| `edge_app_title`     | Display title for the Edge App instance        | Yes      |         |
| `environment`        | Target environment (`stage` or `production`)   | No       | `stage` |
| `edge_app_id`        | Edge App ID for this environment               | No       | `""`    |

Always uses `screenly.yml` for both stage and production (no `screenly_qc.yml`). When `edge_app_id` is non-empty, it is exported as `EDGE_APP_ID` and takes precedence over any `id` in the manifest. On first-time initialize, pass an empty value (omit the input, or use the expression above with the env var unset) — create does not need an id beforehand. After create succeeds, store the printed id in `STAGE_EDGE_APP_ID` / `PRODUCTION_EDGE_APP_ID` and pass those on later runs (especially `update`).

**GitHub Actions expression tip:** prefer the scoped form above (with a trailing `|| ''`). Patterns like `production && vars.PRODUCTION_EDGE_APP_ID || vars.STAGE_EDGE_APP_ID` can pass the stage id into a production job when the production var is unset, and nested `&&` / `||` forms can evaluate to boolean `false`, which the action treats as a literal app id string `"false"`.

Requires `screenly/cli` `v26.9.0` or later; see the [`v26.9.0` release notes](https://github.com/Screenly/cli/releases/tag/v26.9.0) for details.

### `update`

Builds and deploys an existing Screenly Edge App.

```yaml
- uses: Screenly/edge-apps-actions/update@v1
  with:
    screenly_api_token: ${{ secrets.SCREENLY_API_TOKEN }}
    environment: stage # optional, defaults to stage
    delete_missing_settings: false # optional, defaults to false
    edge_app_id: ${{ vars.STAGE_EDGE_APP_ID }} # use PRODUCTION_EDGE_APP_ID in the production job
```

| Input                     | Description                                                      | Required | Default |
| ------------------------- | ---------------------------------------------------------------- | -------- | ------- |
| `screenly_api_token`      | Screenly API token                                               | Yes      |         |
| `environment`             | Target environment (`stage` or `production`)                     | No       | `stage` |
| `delete_missing_settings` | Delete settings that exist on the server but not in the manifest | No       | `false` |
| `edge_app_id`             | Edge App ID for this environment                                 | No       | `""`    |

Always uses `screenly.yml` for both stage and production (no `screenly_qc.yml`). With a shared manifest, pass `edge_app_id` per environment (`vars.STAGE_EDGE_APP_ID` / `vars.PRODUCTION_EDGE_APP_ID`) so stage and production do not rely on an `id` inside `screenly.yml`. When provided and non-empty, it's exported as `EDGE_APP_ID` and takes precedence over any `id` in the manifest. Separate jobs (as in [`examples/update-edge-app.yml`](examples/update-edge-app.yml)) are safer than a single expression that switches vars with `&&` / `||`. Requires `screenly/cli` `v26.9.0` or later; see the [`v26.9.0` release notes](https://github.com/Screenly/cli/releases/tag/v26.9.0) for details.
