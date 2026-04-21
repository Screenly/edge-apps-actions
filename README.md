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
```

| Input                | Description                                    | Required | Default |
| -------------------- | ---------------------------------------------- | -------- | ------- |
| `screenly_api_token` | Screenly API token                             | Yes      |         |
| `edge_app_name`      | Edge App name (used for the CLI `--name` flag) | Yes      |         |
| `edge_app_title`     | Display title for the Edge App instance        | Yes      |         |
| `environment`        | Target environment (`stage` or `production`)   | No       | `stage` |

## Planned Actions

The following actions are planned for future implementation:

- **`update/`**: Updates an existing Screenly Edge App
