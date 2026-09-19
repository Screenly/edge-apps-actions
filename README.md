# edge-apps-actions

Composite GitHub Actions for Screenly Edge Apps.

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
    environment: stage # optional, defaults to stage
    edge_app_id: ${{ vars.STAGE_EDGE_APP_ID }} # optional, see below
```

| Input                | Description                                    | Required | Default |
| -------------------- | ---------------------------------------------- | -------- | ------- |
| `screenly_api_token` | Screenly API token                             | Yes      |         |
| `edge_app_name`      | Edge App name (used for the CLI `--name` flag) | Yes      |         |
| `edge_app_title`     | Display title for the Edge App instance        | Yes      |         |
| `environment`        | Target environment (`stage` or `production`)   | No       | `stage` |
| `edge_app_id`        | Edge App ID for this environment               | No       | `""`    |

Always uses `screenly.yml` for both stage and production (no `screenly_qc.yml`). When `edge_app_id` is provided, it's exported as `EDGE_APP_ID` and takes precedence over any `id` in the manifest. On first-time initialize, omit `edge_app_id` — create does not need an id beforehand. After create succeeds, store the printed id in the repo vars `STAGE_EDGE_APP_ID` / `PRODUCTION_EDGE_APP_ID` and pass those on later runs (especially `update`). Requires `screenly/cli` `v26.9.0` or later; see the [`v26.9.0` release notes](https://github.com/Screenly/cli/releases/tag/v26.9.0) for details.

### `update`

Builds and deploys an existing Screenly Edge App.

```yaml
- uses: Screenly/edge-apps-actions/update@v1
  with:
    screenly_api_token: ${{ secrets.SCREENLY_API_TOKEN }}
    environment: stage # optional, defaults to stage
    delete_missing_settings: false # optional, defaults to false
    edge_app_id: ${{ vars.STAGE_EDGE_APP_ID }} # pass per environment
```

| Input                     | Description                                                      | Required | Default |
| ------------------------- | ---------------------------------------------------------------- | -------- | ------- |
| `screenly_api_token`      | Screenly API token                                               | Yes      |         |
| `environment`             | Target environment (`stage` or `production`)                     | No       | `stage` |
| `delete_missing_settings` | Delete settings that exist on the server but not in the manifest | No       | `false` |
| `edge_app_id`             | Edge App ID for this environment                                  | No       | `""`    |

Always uses `screenly.yml` for both stage and production (no `screenly_qc.yml`). With a shared manifest, pass `edge_app_id` per environment (`vars.STAGE_EDGE_APP_ID` / `vars.PRODUCTION_EDGE_APP_ID`) so stage and production do not rely on an `id` inside `screenly.yml`. When provided, it's exported as `EDGE_APP_ID` and takes precedence over any `id` in the manifest. Requires `screenly/cli` `v26.9.0` or later; see the [`v26.9.0` release notes](https://github.com/Screenly/cli/releases/tag/v26.9.0) for details.
