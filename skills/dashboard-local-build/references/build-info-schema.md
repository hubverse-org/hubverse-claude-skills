# Build Info Schema and Version Collection

Reference for collecting tool versions during local dashboard builds and the shared `build-info.json` schema used by both the local build skill and CI.

## Version collection commands

### Forecasts (predtimechart)

```bash
# Python version
python3 --version 2>&1

# predtimechart package version
"$dash/.venv/bin/pip" show hub-dashboard-predtimechart 2>/dev/null | grep '^Version:' | cut -d' ' -f2

# hubdata package version (dependency)
"$dash/.venv/bin/pip" show hubdata 2>/dev/null | grep '^Version:' | cut -d' ' -f2
```

For dev installs, check the install location to distinguish local from release:
```bash
"$dash/.venv/bin/pip" show hub-dashboard-predtimechart 2>/dev/null | grep '^Location:'
```

### Evals (predevals)

**Docker path:**
```bash
# Registry digest of the pulled image
docker inspect ghcr.io/hubverse-org/hubpredevalsdata-docker:latest \
  --format='{{index .RepoDigests 0}}' 2>/dev/null
```

**Native R path:**
```bash
# R version and hubverse package versions with sources
Rscript -e '
  message("R version: ", getRversion())
  hub_pkgs <- grep("^hub|^Hub", installed.packages()[,"Package"], value = TRUE)
  for (pkg in hub_pkgs) {
    desc <- packageDescription(pkg)
    message(pkg, " ", desc$Version, " (",
      if (!is.null(desc$Repository)) desc$Repository
      else if (!is.null(desc$RemoteType)) paste0(desc$RemoteType, ": ", desc$RemoteRepo, "@", substr(desc$RemoteSha, 1, 7))
      else if (!is.null(desc$Built)) "local"
      else "unknown",
    ")")
  }
'
```

### Site (site-builder)

```bash
# Registry digest of the pulled image
docker inspect ghcr.io/hubverse-org/hub-dash-site-builder:latest \
  --format='{{index .RepoDigests 0}}' 2>/dev/null
```

### Repos (all checkpoints)

```bash
# Dashboard commit and branch
git -C "$dash" branch --show-current
git -C "$dash" rev-parse --short HEAD

# Hub commit and branch
git -C "$hub" branch --show-current
git -C "$hub" rev-parse --short HEAD

# Remote slug (for URLs)
git -C "$dash" remote get-url origin 2>/dev/null | sed 's|.*github.com[:/]||;s|\.git$||'
git -C "$hub" remote get-url origin 2>/dev/null | sed 's|.*github.com[:/]||;s|\.git$||'
```

## build-info.json schema

This schema is the shared contract between local builds (this skill) and CI builds (the composite action in each dashboard repo). The `build_source` field distinguishes the two.

Fields are included only when the corresponding build step was executed. For example, a forecasts-only build would omit `predevals` and `site_builder`.

```jsonc
{
  "build_timestamp": "ISO-8601 UTC",
  "build_source": "local|ci",

  "predtimechart": {
    "version": "v1.2.3",
    "repo": "hubverse-org/hub-dashboard-predtimechart",
    "url": "https://github.com/hubverse-org/hub-dashboard-predtimechart/releases/tag/v1.2.3",
    // Dev variant adds:
    "source": "dev",
    "path": "/local/repo/path",
    "branch": "feature-x"
  },

  "predevals": {
    "method": "docker",
    // Docker released:
    "image": "ghcr.io/hubverse-org/hubpredevalsdata-docker:latest",
    "digest": "sha256:...",
    "url": "https://github.com/hubverse-org/hubPredEvalsData-docker/pkgs/container/hubpredevalsdata-docker"
    // Docker dev built from a hubPredEvalsData-docker checkout (no registry digest):
    //   "source": "dev",
    //   "image": "ghcr.io/hubverse-org/hubpredevalsdata-dev:4.5",
    //   "path": "/local/repo/path",
    //   "branch": "feature-x"
    // Docker dev pulled (dev R packages layered on the published dev image):
    //   "source": "dev",
    //   "image": "ghcr.io/hubverse-org/hubpredevalsdata-dev:4.5",
    //   "digest": "sha256:...",
    //   "packages": { /* dev R package sources, as in native-r below */ }
    // Native R:
    //   "method": "native-r",
    //   "r_version": "4.5.2",
    //   "packages": {
    //     "hubPredEvalsData": { "version": "0.1.0", "source": "GitHub: hubverse-org/hubPredEvalsData@76c0821" },
    //     "hubEvals": { "version": "0.2.0", "source": "r-universe" }
    //   }
  },

  "site_builder": {
    "image": "ghcr.io/hubverse-org/hub-dash-site-builder:latest",
    "digest": "sha256:...",
    "url": "https://github.com/hubverse-org/hub-dash-site-builder/pkgs/container/hub-dash-site-builder",
    // Dev variant (no registry digest):
    "source": "dev",
    "path": "/local/repo/path",
    "branch": "feature-x"
  },

  "dashboard": {
    "repo": "owner/repo",
    "branch": "branch-name",
    "commit": "abc1234",
    "url": "https://github.com/owner/repo/commit/full-sha"
  },

  "hub": {
    "repo": "owner/repo",
    "branch": "branch-name",
    "commit": "abc1234",
    "url": "https://github.com/owner/repo/commit/full-sha"
  },

  "control_room": {
    "repo": "hubverse-org/hub-dashboard-control-room",
    "ref": "main",
    "url": "https://github.com/hubverse-org/hub-dashboard-control-room"
  }
}
```

### Schema notes

- **`build_source`**: `"local"` for skill builds, `"ci"` for GitHub Actions builds.
- **`predevals.method`**: `"docker"` or `"native-r"`. Determines which sub-fields are present.
- **`source: "dev"`**: Present on any tool installed from a local repo checkout. When set, `path` and `branch` replace release URLs/digests.
- **Docker digests**: Use `docker inspect --format='{{index .RepoDigests 0}}'` for pulled images (matches `crane digest`). Dev-built images have no registry digest.
- **Omitted sections**: If a build step was skipped (e.g., evals-only build), the corresponding top-level keys are omitted rather than set to null.
