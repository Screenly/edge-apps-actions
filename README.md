# edge-apps-actions

Composite GitHub Actions for Screenly Edge Apps.

## Available Actions

### `checks`

Builds, lints, formats, and tests a Screenly Edge App.

```yaml
- uses: Screenly/edge-apps-actions/checks@v1
  with:
    bun-version: latest  # optional
```

## Planned Actions

The following actions are planned for future implementation:

- **`create/`** — Creates a new Screenly Edge App
- **`update/`** — Updates an existing Screenly Edge App
