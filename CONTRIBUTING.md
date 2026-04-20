# Contributing to edge-apps-actions

We welcome contributions from the community! To keep the codebase healthy and changes reviewable, we ask that all contributors work from a personal fork and submit pull requests. Direct pushes to the main repository are reserved for maintainers.

## Development Workflow

### Contributors

1. Fork the repository on GitHub.
2. Clone your fork and create a branch off `main`:
   ```sh
   git checkout -b your-feature-branch
   git push -u origin your-feature-branch
   ```
3. Make your changes and commit them.
4. Open a pull request against `Screenly/edge-apps-actions@main`.

### Maintainers

1. Create a branch off `main`:
   ```sh
   git checkout -b your-feature-branch
   git push -u origin your-feature-branch
   ```
2. Make your changes and commit them.
3. Open a pull request against `main`.
4. Once merged, tag the release (see below).

## Tagging and Releases

This repo follows the GitHub Actions tagging convention: **both** a fixed (immutable) version tag and a floating major tag must be pushed for every release.

- **Fixed tag** (`v1.0.0`): immutable, points to a specific commit forever. Consumers who want a pinned, reproducible version use this.
- **Floating tag** (`v1`): moves with each release in the same major version. Consumers who reference `@v1` in their workflows always get the latest stable release within that major. **Both tags are required.**

### Pushing tags

After merging to `main`, pull the latest and tag the release:

```sh
git checkout main
git pull

# Create the fixed tag
git tag v1.0.0

# Create or update the floating major tag
git tag -f v1

# Push both
git push origin v1.0.0
git push origin v1 --force
```

> `--force` is required when updating the floating tag because it moves an existing tag to a new commit.

### When to bump versions

| Change type | Example | Version bump |
|---|---|---|
| Patch | Bug fix, minor tweak | `v1.0.0` → `v1.0.1` |
| Minor | New optional input, new action | `v1.0.0` → `v1.1.0` |
| Major | Breaking change to inputs/behavior | `v1.x.x` → `v2.0.0` |

For major bumps, introduce a new floating tag (e.g. `v2`) and stop updating the old one.
