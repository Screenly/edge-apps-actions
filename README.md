[![Version](https://img.shields.io/github/v/release/Screenly/edge-apps-actions)](https://github.com/Screenly/edge-apps-actions/releases/latest)

# Edge Apps GitHub Actions

Reusable GitHub Actions and workflows that check, build and deploy [Screenly Edge Apps](https://developer.screenly.io/edge-apps/). Add them to an Edge App repo to:

- **`checks`**: lint, format-check, build and test the app on every pull request.
- **`initialize`**: create the Edge App and its first instance in stage or production (once per environment).
- **`update`**: deploy every push to the default branch to stage, and every `v*` release tag to production.

Bun apps with a `build` script are built and deployed from `dist/`; plain HTML apps are deployed as-is. Copy the [example workflows](#example-workflows) to get started.

## Versioning

This repo uses [Calendar Versioning](https://calver.org/) with `vYY.M.PATCH` tags (e.g. `v26.10.0`). Each release is an immutable `vYY.M.PATCH` tag; pin an exact one and bump it deliberately. The legacy `@v1` tag is frozen and receives no fixes. See [`CONTRIBUTING.md`](CONTRIBUTING.md#tagging-and-releases) for the full scheme.

## Example workflows

Copy these into your app repo under `.github/workflows/`:

- [`examples/initialize-edge-app.yml`](examples/initialize-edge-app.yml) — manual create/deploy for stage or production
- [`examples/update-edge-app.yml`](examples/update-edge-app.yml) — deploy stage on every push to the default branch (`main`/`master`) or a manual run from it (rolling); deploy production when a version tag like `v26.10.0` is pushed

The examples are short callers of the [reusable workflows](#reusable-workflows) in this repo, so the deploy logic lives in one place and every app gets changes by bumping one version:

```yaml
jobs:
  update:
    uses: Screenly/edge-apps-actions/.github/workflows/update.yml@v26.10.2
    secrets:
      SCREENLY_API_TOKEN: ${{ secrets.SCREENLY_API_TOKEN }}
```

The update example triggers on both `main` and `master`; the reusable workflow only deploys stage for the repo's default branch, so the file works unchanged in either kind of repo.

To release to production, tag the commit on `main`/`master` and push the tag. The production job refuses to deploy tags whose commit is not on the repo's default branch. We recommend the same CalVer `vYY.M.PATCH` scheme for app releases (e.g. `v26.10.0` for the first release in October 2026, `v26.10.1` for the next one that month):

```sh
git tag v26.10.0
git push origin v26.10.0
```

Then publish a GitHub Release whose notes list the pull requests merged since the previous release. Add `--draft` to review the notes before publishing:

```sh
gh release create v26.10.0 --verify-tag --generate-notes --title v26.10.0
```

## Keeping up to date

Pin an exact release (`@vYY.M.PATCH`) and let [Dependabot](https://docs.github.com/en/code-security/dependabot/working-with-dependabot/keeping-your-actions-up-to-date-with-dependabot) open the bump PRs: its `github-actions` updates also bump the ref of reusable workflow calls. Add `.github/dependabot.yml` to the app repo:

```yaml
version: 2
updates:
  - package-ecosystem: 'github-actions'
    directory: '/'
    schedule:
      interval: 'weekly'
    # Use the branch you merge into before the default branch; otherwise bump
    # PRs target the default branch and deploy stage when merged.
    target-branch: 'development'
    groups:
      github-actions:
        patterns:
          - '*'
```

Don't pin a moving ref (`@main` or a re-pointed tag): a bad release would then reach every app's production deploy at once, with no change recorded in the app repo.

## Protecting production

A tag push runs the workflow file from the tagged commit, not the one on the default branch. Anyone who can push a `v*` tag can therefore tag a commit whose workflow drops the default-branch check, so that check guards against mistakes, not misuse. Protect production with repository settings instead:

1. **Restrict who can push version tags.** Add a tag ruleset (Settings → Rules → Rulesets → New tag ruleset) targeting `v*`, with **Restrict creations**, **Restrict updates** and **Restrict deletions** enabled. Put your release team (e.g. `edge-app-release-manager`) and repository admins on the bypass list; they are then the only people who can push a version tag.
2. **Restrict the `production` environment to tags.** Under Settings → Environments → `production` → Deployment branches and tags, allow only tags matching `v[0-9]*`. Run production **Initialize** before this step; afterwards it can only be started from a `v*` tag (choose the tag under "Use workflow from").
3. **Require approval for production.** Add required reviewers to the `production` environment, and enable **Prevent self-review** so the person who pushed a tag cannot approve its deploy.

Rulesets apply to the repository they are set on, so each app repo needs its own, or an organization admin can add one ruleset that covers every app repo.

## Setup checklist

1. Create GitHub Environments named `stage` and `production` (the reusable workflows set `environment:` to these names).
2. Add secret `SCREENLY_API_TOKEN` as an **environment secret** on both `stage` and `production` (see [GitHub secrets](#github-secrets)).
3. Do **not** create `STAGE_EDGE_APP_ID` / `PRODUCTION_EDGE_APP_ID` yet.
4. Run **Initialize Edge App** for stage, then for production.
5. After each initialize run **has finished successfully**, copy the Edge App id from its job summary into the matching repo variable.
6. Use **Update Edge App** for later deploys (requires those vars to be set).
7. Protect production with a `v*` tag ruleset, a tag-only `production` environment and required reviewers (see [Protecting production](#protecting-production)).

## GitHub secrets

Both **stage** and **production** need a Screenly API token. Add `SCREENLY_API_TOKEN` as an **environment secret** on each of the `stage` and `production` GitHub Environments. An environment secret is only released to a job after that environment's rules pass (allowed branches/tags, required reviewers). A repository secret is readable by a workflow on any branch, which bypasses production approval, so don't store the production token there.

| Secret | Required by | Description |
| ------ | ----------- | ----------- |
| `SCREENLY_API_TOKEN` | `initialize`, `update` (stage and production) | Screenly API token passed as `screenly_api_token` |

```yaml
screenly_api_token: ${{ secrets.SCREENLY_API_TOKEN }}
```

Both actions validate the token against `/api/v4.1/users/` on the target API (`https://api.screenlyappstage.com` for stage, `https://api.screenlyapp.com` for production) before calling the CLI. An empty or invalid token fails fast with a clear error.

## Repo variables

Use **only** these GitHub Actions repository variables for Edge App ids (never secrets):

| Variable | Environment | When to set |
| -------- | ----------- | ----------- |
| `STAGE_EDGE_APP_ID` | stage | After first successful stage initialize |
| `PRODUCTION_EDGE_APP_ID` | production | After first successful production initialize |

**First create:** leave the matching var unset. The example expression then resolves to `""`, and `initialize` creates a new app.

**Later runs:** set the var to the real id from initialize. `update` requires it and will fail if the value is missing or a placeholder (`false`, `0`, `null`, etc.). `initialize` refuses to run once it is set, so a re-run can't create a duplicate app or instance.

## Build and deploy

`initialize` and `update` build the app when `package.json` has a `build` script: they run `bun install --frozen-lockfile` and `bun run build`, then deploy `./dist`. Otherwise they deploy the repo root as-is.

When deploying the repo root, the actions add `.git/`, `.github/`, `.claude/` and `node_modules/` to `.ignore` (in the runner's workspace only) so they are not uploaded. The CLI uploads every other file in the root; list anything else that isn't part of the app in your `.ignore`.

## Reusable workflows

Call these from an app repo with `uses:` at the job level, passing only the token (see the examples):

```yaml
    secrets:
      SCREENLY_API_TOKEN: ${{ secrets.SCREENLY_API_TOKEN }}
```

They run in the app repo's context: the app's `vars`, environments (secrets, reviewers, branch rules) and `github` event are used. The token can exist only as a `stage`/`production` environment secret: GitHub releases the matching environment's value to the reusable workflow's job that sets `environment:`. Passing it is required (the workflows declare it `required: true`); if it's missing, the secret is empty and the actions fail with "screenly_api_token is empty" ([GitHub Docs](https://docs.github.com/en/actions/how-tos/reuse-automations/reuse-workflows)). Passing it by name instead of `secrets: inherit` keeps the app's other secrets out of these workflows.

`initialize` also refuses to create an app when one with the same name already exists in that environment, so a second Initialize run (e.g. dispatched twice) can't create a duplicate.

| Workflow | Inputs | What it does |
| -------- | ------ | ------------ |
| [`.github/workflows/update.yml`](.github/workflows/update.yml) | `delete_missing_settings` (boolean, default `true`) | **Stage** job: runs only for pushes and manual runs on the repo's default branch; other triggers are ignored. **Production** job: runs only for a pushed `v*` tag, and refuses tags whose commit is not on the default branch. |
| [`.github/workflows/initialize.yml`](.github/workflows/initialize.yml) | `environment`, `edge_app_name`, `edge_app_title` (all required) | Creates the Edge App and its first instance in the given environment, reading the id variable for that environment. |

Both workflows:

- run one job per environment at a time. **Update** uses the groups `edge-app-stage` / `edge-app-production` with `cancel-in-progress: true`: a newer push or tag cancels the deploy in progress (or one still waiting for production approval), so runs don't pile up and the latest change wins. A cancelled deploy can stop part-way; the run that cancelled it deploys straight after. **Initialize** uses its own groups (`edge-app-initialize-stage` / `-production`) and is never cancelled by a deploy.
- use a read-only `GITHUB_TOKEN` (`permissions: contents: read`).
- pin `initialize` / `update` to the same release as the workflow itself.

Don't add a `concurrency` group with the same name to the calling job; caller and called jobs in the same group block each other.

## Available Actions

The reusable workflows use these actions. You can also call them directly from your own workflow steps.

### `checks`

Builds, lints, formats, and tests a Screenly Edge App.

```yaml
- uses: Screenly/edge-apps-actions/checks@v26.10.2
  with:
    bun-version: latest # optional
```

| Input         | Description        | Required | Default  |
| ------------- | ------------------ | -------- | -------- |
| `bun-version` | Bun version to use | No       | `latest` |

### `initialize`

Creates and deploys a new Screenly Edge App instance.

```yaml
- uses: Screenly/edge-apps-actions/initialize@v26.10.2
  with:
    screenly_api_token: ${{ secrets.SCREENLY_API_TOKEN }}
    edge_app_name: my-edge-app
    edge_app_title: My Edge App
    environment: ${{ inputs.environment }} # stage or production
    edge_app_id: ${{ (inputs.environment == 'production' && vars.PRODUCTION_EDGE_APP_ID) || (inputs.environment == 'stage' && vars.STAGE_EDGE_APP_ID) || '' }}
```

| Input                | Description                                       | Required | Default |
| -------------------- | ------------------------------------------------- | -------- | ------- |
| `screenly_api_token` | Screenly API token (`secrets.SCREENLY_API_TOKEN`) | Yes      |         |
| `edge_app_name`      | Edge App name (used for the CLI `--name` flag)    | Yes      |         |
| `edge_app_title`     | Display title for the Edge App instance           | Yes      |         |
| `environment`        | `stage` or `production` only                      | No       | `stage` |
| `edge_app_id`        | Edge App ID for this environment                  | No       | `""`    |

`edge_app_name` and `edge_app_title` must not contain `"`, `$`, `` ` ``, `\` or control characters; the action fails before calling the CLI if they do.

Always uses `screenly.yml` for both stage and production. When `edge_app_id` is a real id, the environment is already initialized and the action fails; use `update` to deploy. Empty / placeholder values are treated as unset (first create). The new app's id is printed in the job summary right after the app is created, so it is not lost if a later step fails.

**Safe expression:** use the scoped form above with trailing `|| ''`. Do **not** use `production && vars.PRODUCTION_EDGE_APP_ID || vars.STAGE_EDGE_APP_ID` — that can pass the stage id into production when the production var is unset.

Requires `screenly/cli` `v26.9.0` or later; see the [`v26.9.0` release notes](https://github.com/Screenly/cli/releases/tag/v26.9.0) for details.

### `update`

Builds and deploys an existing Screenly Edge App.

```yaml
- uses: Screenly/edge-apps-actions/update@v26.10.2
  with:
    screenly_api_token: ${{ secrets.SCREENLY_API_TOKEN }}
    environment: stage # or production
    delete_missing_settings: false # optional, defaults to false
    edge_app_id: ${{ vars.STAGE_EDGE_APP_ID }} # production job: vars.PRODUCTION_EDGE_APP_ID
```

| Input                     | Description                                                      | Required | Default |
| ------------------------- | ---------------------------------------------------------------- | -------- | ------- |
| `screenly_api_token`      | Screenly API token (`secrets.SCREENLY_API_TOKEN`)                | Yes      |         |
| `environment`             | `stage` or `production` only                                     | No       | `stage` |
| `delete_missing_settings` | Delete settings that exist on the server but not in the manifest | No       | `false` |
| `edge_app_id`             | Edge App ID for this environment (required, real id)             | Yes\*    | `""`    |

\*Required at runtime: empty or placeholder values fail the job with a message to set `STAGE_EDGE_APP_ID` / `PRODUCTION_EDGE_APP_ID`.

Always uses `screenly.yml`. Prefer separate jobs per environment (as in [`examples/update-edge-app.yml`](examples/update-edge-app.yml)), each passing only its own var.

Requires `screenly/cli` `v26.9.0` or later; see the [`v26.9.0` release notes](https://github.com/Screenly/cli/releases/tag/v26.9.0) for details.
