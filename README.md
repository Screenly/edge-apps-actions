[![Version](https://img.shields.io/github/v/release/Screenly/edge-apps-actions)](https://github.com/Screenly/edge-apps-actions/releases/latest)

# Edge Apps GitHub Actions

Reusable GitHub workflows that check, build and deploy [Screenly Edge Apps](https://developer.screenly.io/edge-apps/):

- **Checks**: lint, format-check, build and test on pushes and pull requests.
- **Initialize**: create the Edge App and its first instance, once per environment.
- **Update**: deploy to **stage** on every push to the default branch, and to **production** on every `v*` tag.

Bun apps with a `build` script are built and deployed from `dist/`; plain HTML apps are deployed as-is.

## Set up an app

1. Copy the [examples](examples/) into the app's `.github/workflows/`: `checks.yml` (Bun apps only), `initialize-edge-app.yml`, `update-edge-app.yml`.
2. Create the GitHub environments `stage` and `production`, and add `SCREENLY_API_TOKEN` as an **environment secret** on both. Don't use a repository secret: it's readable from any branch and bypasses production approval.
3. Run **Actions → Initialize Edge App** for `stage`. When it **has finished successfully**, set the repo variable `STAGE_EDGE_APP_ID` to the id in its job summary.
4. Do the same for `production` → `PRODUCTION_EDGE_APP_ID`.
5. [Protect production](#protect-production).

Each example is a few lines that call this repo's workflows, so the logic lives here:

```yaml
jobs:
  update:
    uses: Screenly/edge-apps-actions/.github/workflows/update.yml@v26.10.2
    secrets:
      SCREENLY_API_TOKEN: ${{ secrets.SCREENLY_API_TOKEN }}
```

## Release an app

- **Stage** deploys on every push (or manual run) on the default branch (`main`/`master`), after approval if the `stage` environment has required reviewers. Other branches never deploy.
- **Production** deploys when you push a `v*` tag on the default branch, after a reviewer approves. We recommend [CalVer](https://calver.org/) `vYY.M.PATCH`:

```sh
git checkout main && git pull   # or master
git tag v26.10.0 && git push origin v26.10.0
gh release create v26.10.0 --verify-tag --generate-notes --title v26.10.0
```

To redo a failed or cancelled production deploy, re-run the latest tag's workflow run; you don't need a new tag.

## Keep it up to date

Pin an exact version and let Dependabot open the bump PRs; it also bumps reusable workflow refs. Add `.github/dependabot.yml`:

```yaml
version: 2
updates:
  - package-ecosystem: 'github-actions'
    directory: '/'
    schedule:
      interval: 'weekly'
    target-branch: 'development' # the branch you merge into before the default branch
    groups:
      github-actions:
        patterns: ['*']
```

Don't pin `@main` or a moving tag: a bad release would reach every app's production at once.

## Protect production

The workflow checks only catch mistakes; whoever pushes a tag controls the workflow file at that commit. Enforce it with repo settings:

1. **Tag ruleset** (Settings → Rules → Rulesets): target `v*`, restrict creations, updates and deletions; bypass only the release team and admins.
2. **`production` environment**: required reviewers with **Prevent self-review**, and deployment branches/tags limited to `v[0-9]*` tags. Run production Initialize first; afterwards it can only start from a `v*` tag.
3. **`stage` environment**: deployment branches limited to the default branch.

## How it works

- **One deploy at a time per environment.** A newer push or tag cancels the deploy in progress (or one waiting for approval), so the latest change wins. A cancelled deploy can stop part-way; the newer run fixes it once it deploys (after approval, if the environment requires it). Initialize is never cancelled.
- **Production tag check.** The tag's commit must be on the default branch.
- **Plain HTML apps** deploy the repo root; `.git/`, `.github/`, `.claude/` and `node_modules/` are always excluded. List anything else that isn't part of the app in `.ignore`.
- **Initialize safeguards.** It refuses to run when the environment's id variable is already set, or when an app with the same name already exists (so a double-click can't create a duplicate). If it can't check, it stops without creating anything.
- **Secrets.** Only `SCREENLY_API_TOKEN` is passed. The workflows run in the app's repo, so its environments, reviewers and variables apply.

## Troubleshooting

| Error | Fix |
| ----- | --- |
| `edge_app_id is required` | Set `STAGE_EDGE_APP_ID` / `PRODUCTION_EDGE_APP_ID` (steps 3–4 of setup). |
| `screenly_api_token is empty` / `validation failed` | Add or fix `SCREENLY_API_TOKEN` on that environment. |
| `This environment is already initialized` | Nothing to do; use Update to deploy. |
| `An Edge App named … already exists` | If a previous Initialize created it and then **failed**, delete that app and re-run Initialize (below). If it's this repo's working app, set the id variable instead. |
| `Tag … is not on <default branch>` | Tag a commit that's on the default branch (`main` or `master`). |

**Recovering from a failed Initialize:** if Initialize created the app but a later step failed, the app has no instance. Don't set the id variable (Update never creates the instance). Delete the app and re-run Initialize:

```sh
# stage: also set API_BASE_URL=https://api.screenlyappstage.com
API_TOKEN=<token> EDGE_APP_ID=<id from the job summary> screenly edge-app delete
```

## Reference

**Reusable workflows** (call with `uses:` at the job level):

| Workflow | Inputs | Secrets |
| -------- | ------ | ------- |
| [`checks.yml`](.github/workflows/checks.yml) | `bun-version` (default `latest`) | none |
| [`initialize.yml`](.github/workflows/initialize.yml) | `environment`, `edge_app_name`, `edge_app_title` | `SCREENLY_API_TOKEN` |
| [`update.yml`](.github/workflows/update.yml) | `delete_missing_settings` (default `true`) | `SCREENLY_API_TOKEN` |

**Actions** (used by the workflows; can also be used as steps):

| Action | Inputs |
| ------ | ------ |
| `checks` | `bun-version` |
| `initialize` | `screenly_api_token`, `edge_app_name`, `edge_app_title`, `environment` (`stage`/`production`), `edge_app_id` |
| `update` | `screenly_api_token`, `environment`, `edge_app_id` (required), `delete_missing_settings` (default `false`) |

- `edge_app_name` / `edge_app_title` can't contain `"`, `$`, `` ` ``, `\` or control characters.
- When calling `initialize` directly, scope the id per environment: `(inputs.environment == 'production' && vars.PRODUCTION_EDGE_APP_ID) || (inputs.environment == 'stage' && vars.STAGE_EDGE_APP_ID) || ''`.
- Requires `screenly/cli` `v26.9.0` or later.

## Versioning

Releases are immutable [CalVer](https://calver.org/) tags (`vYY.M.PATCH`); the legacy `@v1` tag is frozen. To release this repo, see [`CONTRIBUTING.md`](CONTRIBUTING.md#tagging-and-releases).
