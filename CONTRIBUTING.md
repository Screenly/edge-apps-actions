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

This repo follows the GitHub Actions tagging convention: **both** a fixed (immutable) version tag and a floating major tag must be pushed for every release.

- **Fixed tag** (`vX.Y.Z`): immutable, points to a specific commit forever. Consumers who want a pinned, reproducible version use this.
- **Floating tag** (`vX`): moves with each release in the same major version. Consumers who reference `@vX` in their workflows always get the latest stable release within that major. **Both tags are required.**

### Pushing tags

After merging to `main`, pull the latest and tag the release. Replace `vX.Y.Z` and `vX` with the actual version you are releasing:

```sh
git checkout main
git pull

# Create the fixed tag
git tag vX.Y.Z

# Create or update the floating major tag
git tag -f vX

# Push both
git push origin vX.Y.Z
git push origin vX --force
```

> `--force` is required when updating the floating tag because it moves an existing tag to a new commit. A tag ruleset on `v*` ensures only authorized maintainers can do this. Always verify you are on the correct commit before tagging.

### When to bump versions

| Change type | Example                            | Version bump            |
| ----------- | ---------------------------------- | ----------------------- |
| Patch       | Bug fix, minor tweak               | `vX.Y.Z` → `vX.Y.(Z+1)` |
| Minor       | New optional input, new action     | `vX.Y.Z` → `vX.(Y+1).0` |
| Major       | Breaking change to inputs/behavior | `vX.Y.Z` → `v(X+1).0.0` |

For major bumps, introduce a new floating tag for the next major version (for example, `v2` after `v1`) and stop updating the old one.
