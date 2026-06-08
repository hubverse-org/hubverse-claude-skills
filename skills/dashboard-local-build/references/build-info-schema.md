# Build Info Schema

The shared `build-info.json` contract used by both the local build skill and CI, plus notes on how its fields are populated. The commands that collect each version are inline in `SKILL.md` at the step that produces them; this file defines the shape they feed into.

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
    //   "r_version": "4.5.2",
    //   "packages": {
    //     "hubPredEvalsData": { "version": "0.1.0", "source": "GitHub: hubverse-org/hubPredEvalsData@76c0821" },
    //     "hubEvals": { "version": "0.2.0", "source": "local" }
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
- **`predevals.method`**: always `"docker"`. The variant (released image, dev image built from a checkout, or published dev image with dev R packages layered in) is distinguished by `source`, `digest`, and `packages`.
- **`source: "dev"`**: Present on any tool installed from a local repo checkout. When set, `path` and `branch` replace release URLs/digests.
- **Docker digests**: Use `docker inspect --format='{{index .RepoDigests 0}}'` for pulled images (matches `crane digest`). Dev-built images have no registry digest.
- **Omitted sections**: If a build step was skipped (e.g., evals-only build), the corresponding top-level keys are omitted rather than set to null.
