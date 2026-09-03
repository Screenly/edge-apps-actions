# Contributing to edge-apps-actions

We welcome contributions from the community! To keep the codebase healthy and changes reviewable, we ask that all contributors work from a personal fork and submit pull requests. Direct pushes to the main repository are reserved for maintainers.

## Development Workflow

### Contributors

1. Fork the repository on GitHub.
2. Clone your fork locally:
   ```sh
   git clone https://github.com/<your-username>/edge-apps-actions.git
   cd edge-apps-actions
   ```
3. Add the upstream remote so you can sync with the original repository:
   ```sh
   git remote add upstream https://github.com/Screenly/edge-apps-actions.git
   ```
4. Create a branch off an up-to-date `main`:
   ```sh
   git fetch upstream
   git checkout main
   git merge upstream/main  # sync your local main with upstream before branching
   git checkout -b your-feature-branch
   ```
5. Make your changes, commit them, and push:
   ```sh
   git add .
   git commit -m "Describe your change"
   git push -u origin your-feature-branch
   ```
6. Open a pull request against `Screenly/edge-apps-actions@main`.

### Maintainers

1. Create a branch off `main`:
   ```sh
   git checkout main
   git pull  # ensure your local main is up to date before branching
   git checkout -b your-feature-branch
   ```
2. Make your changes, commit them, and push:
   ```sh
   git add .
   git commit -m "Describe your change"
   git push -u origin your-feature-branch
   ```
3. Open a pull request against `main`.
4. Once merged, tag the release (see below).

## Tagging and Releases

This repo follows [Calendar Versioning](https://calver.org/) using a `YY.M.PATCH` scheme (e.g. `v26.8.0`), a SemVer-compatible variant of CalVer: `YY` is the last two digits of the year, `M` is the month (both non-zero-padded, e.g. `8` for August, not `08`), and `PATCH` resets to `0` for the first release of a given year/month and increments for any additional release within that same month. Git tags are always `v`-prefixed (e.g. `v26.8.0`).

Only a **fixed (immutable)** tag is pushed per release, no floating tag is created or moved. Every consumer pins an exact `vYY.M.PATCH` in their workflow and bumps it deliberately when they want a newer release; nothing changes underneath them without an explicit edit on their side.

> **Legacy `v1` tag:** this repo previously followed SemVer with a floating `v1` major tag that moved with every release. `v1` now stays frozen at its last SemVer-era commit and will **not** be updated again. Existing consumers pinned to `@v1` are unaffected and keep working, but they will not receive any future fixes or features, those only ship under new `vYY.M.PATCH` tags. If you're setting up a new workflow, or maintain one still on `@v1`, pin an explicit `vYY.M.PATCH` instead.

### Pushing tags

After merging to `main`, pull the latest and tag the release. Replace `vYY.M.PATCH` with the version you are releasing:

```sh
git checkout main
git pull

git tag vYY.M.PATCH
git push origin vYY.M.PATCH
```

### When to bump versions

| Change type                               | Example               |
| ------------------------------------------ | ---------------------- |
| Another release in the same month          | `v26.8.0` → `v26.8.1` |
| First release in a new month (same year)   | `v26.8.1` → `v26.9.0` |
| First release in a new year                | `v26.9.0` → `v27.1.0` |

Version numbers no longer signal whether a change is breaking, since CalVer tracks release timing, not compatibility. Call out breaking changes explicitly in the release notes so consumers know to review before bumping their pin.
