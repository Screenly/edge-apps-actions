# edge-apps-actions

Composite GitHub Actions for Screenly Edge Apps.

## Example workflows

Copy these into your app repo under `.github/workflows/`:

- [`examples/initialize-edge-app.yml`](examples/initialize-edge-app.yml) — manual create/deploy for stage or production
- [`examples/update-edge-app.yml`](examples/update-edge-app.yml) — deploy stage from `development`, production from `main`

Branch names are only used in your workflow triggers (`on.push.branches` / `github.ref`). The actions themselves work the same on `main` or `master` — change the branch names in the example to match your repo.

## GitHub secrets

Both **stage** and **production** need a Screenly API token. Add `SCREENLY_API_TOKEN` as a repository secret (shared by both), or as an environment secret on each of the `stage` and `production` GitHub Environments when the tokens differ.

| Secret | Required by | Description |
| ------ | ----------- | ----------- |
| `SCREENLY_API_TOKEN` | `initialize`, `update` (stage and production) | Screenly API token passed as `screenly_api_token` |

```yaml
screenly_api_token: ${{ secrets.SCREENLY_API_TOKEN }}
```

The token is forwarded to `screenly/cli` for create/deploy/instance commands. The `update` action also validates it with `Authorization: Token <token>` against `/api/v4.1/users/` on the target API (`https://api.screenlyappstage.com` for stage, `https://api.screenlyapp.com` for production).

## Repo variables

Use **only** these GitHub Actions repository variables for Edge App ids:

| Variable | Environment |
| -------- | ----------- |
| `STAGE_EDGE_APP_ID` | stage |
| `PRODUCTION_EDGE_APP_ID` | production |

Do not store Edge App ids as secrets. Leave each var **unset** until that environment’s first initialize succeeds, then store the printed id. Do not use placeholders (`0`, `false`, etc.) — any other non-empty value is treated as an app id.

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
    edge_app_id: ${{ (inputs.environment == 'production' && vars.PRODUCTION_EDGE_APP_ID) || (inputs.environment == 'stage' && vars.STAGE_EDGE_APP_ID) || '' }}
```

| Input                | Description                                    | Required | Default |
| -------------------- | ---------------------------------------------- | -------- | ------- |
| `screenly_api_token` | Screenly API token (`secrets.SCREENLY_API_TOKEN`) | Yes      |         |
| `edge_app_name`      | Edge App name (used for the CLI `--name` flag) | Yes      |         |
| `edge_app_title`     | Display title for the Edge App instance        | Yes      |         |
| `environment`        | Target environment (`stage` or `production`)   | No       | `stage` |
| `edge_app_id`        | Edge App ID for this environment               | No       | `""`    |

Always uses `screenly.yml` for both stage and production (no `screenly_qc.yml`). When `edge_app_id` is a real id, it is exported as `EDGE_APP_ID` and takes precedence over any `id` in the manifest. On first-time initialize, leave the matching repo var unset so the expression above is `""`. After create, set `STAGE_EDGE_APP_ID` or `PRODUCTION_EDGE_APP_ID` to the printed id for later `initialize` / `update` runs.

Use the scoped expression above (with trailing `|| ''`). Avoid `production && vars.PRODUCTION_EDGE_APP_ID || vars.STAGE_EDGE_APP_ID` — that can pass the stage id into production when the production var is unset.

Requires `screenly/cli` `v26.9.0` or later; see the [`v26.9.0` release notes](https://github.com/Screenly/cli/releases/tag/v26.9.0) for details.

### `update`

Builds and deploys an existing Screenly Edge App.

```yaml
- uses: Screenly/edge-apps-actions/update@v1
  with:
    screenly_api_token: ${{ secrets.SCREENLY_API_TOKEN }}
    environment: stage # optional, defaults to stage
    delete_missing_settings: false # optional, defaults to false
    edge_app_id: ${{ vars.STAGE_EDGE_APP_ID }} # production job: vars.PRODUCTION_EDGE_APP_ID
```

| Input                     | Description                                                      | Required | Default |
| ------------------------- | ---------------------------------------------------------------- | -------- | ------- |
| `screenly_api_token`      | Screenly API token (`secrets.SCREENLY_API_TOKEN`)                | Yes      |         |
| `environment`             | Target environment (`stage` or `production`)                     | No       | `stage` |
| `delete_missing_settings` | Delete settings that exist on the server but not in the manifest | No       | `false` |
| `edge_app_id`             | Edge App ID for this environment                                 | No       | `""`    |

Always uses `screenly.yml` for both stage and production (no `screenly_qc.yml`). Prefer separate jobs per environment (as in [`examples/update-edge-app.yml`](examples/update-edge-app.yml)), each passing only its own var — no `&&` / `||` switching. When `edge_app_id` is set, it is exported as `EDGE_APP_ID` and takes precedence over any `id` in the manifest.

Requires `screenly/cli` `v26.9.0` or later; see the [`v26.9.0` release notes](https://github.com/Screenly/cli/releases/tag/v26.9.0) for details.
