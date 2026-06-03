# Pipeline Command Reference

Condensed from [hubDocs: Local Dashboard Workflow](https://hubverse.io/en/latest/developer/dashboard-local.html).

## Variables

```bash
dash="/path/to/dashboard"   # dashboard repo root
hub="/path/to/hub"          # hub repo root
```

## Setup

```bash
# Get hub slug from dashboard config
hub_slug=$(yq '.hub' "$dash/site-config.yml" | tr -d '"' | sed 's|/$||')

# Clone hub (if not already local)
git clone "https://github.com/${hub_slug}.git" "$hub"

# Create output directories
mkdir -p "$dash/data/ptc/"{targets,forecasts}
mkdir -p "$dash/data/evals"
```

## Step 1: Forecasts (predtimechart, Python)

```bash
# Install in virtual environment
uv venv --seed "$dash/.venv"
source "$dash/.venv/bin/activate"
latest=$(gh api -X GET "repos/hubverse-org/hub-dashboard-predtimechart/releases/latest" --jq ".tag_name")
uv run pip install --quiet --upgrade pip
uv run pip install --quiet "git+https://github.com/hubverse-org/hub-dashboard-predtimechart@$latest"

# Generate target data
ptc_generate_target_json_files \
  "$hub" \
  "$dash/predtimechart-config.yml" \
  "$dash/data/ptc/targets"

# Generate forecast data + options
ptc_generate_json_files \
  "$hub" \
  "$dash/predtimechart-config.yml" \
  "$dash/data/ptc/predtimechart-options.json" \
  "$dash/data/ptc/forecasts"
```

## Step 2: Evaluations (predevals, Docker)

```bash
# Pull image
docker pull --platform=linux/amd64 ghcr.io/hubverse-org/hubpredevalsdata-docker:latest

# Generate eval data
docker run --rm --platform=linux/amd64 \
  -v "$dash":"/project" \
  -v "$hub":"/hub" \
  ghcr.io/hubverse-org/hubpredevalsdata-docker:latest \
  create-predevals-data.R \
    -h "/hub" \
    -c "predevals-config.yml" \
    -d "/hub/target-data/oracle-output.csv" \
    -o "data/evals"
```

### Alternative: Native R (no Docker)

Uses the same `create-predevals-data.R` script from the Docker image, run natively.

```bash
# Extract script from Docker image
docker pull --platform=linux/amd64 ghcr.io/hubverse-org/hubpredevalsdata-docker:latest
docker run --rm --platform=linux/amd64 --entrypoint cat \
  ghcr.io/hubverse-org/hubpredevalsdata-docker:latest \
  /usr/local/bin/create-predevals-data.R > "$dash/create-predevals-data.R"

# Install R dependencies
Rscript -e 'install.packages("hubEvals", repos = c("https://hubverse-org.r-universe.dev", "https://cloud.r-project.org")); remotes::install_github("hubverse-org/hubPredEvalsData", upgrade = "never")'

# Run
Rscript "$dash/create-predevals-data.R" \
  -h "$hub" \
  -c "$dash/predevals-config.yml" \
  -d "$hub/target-data/oracle-output.csv" \
  -o "$dash/data/evals"

# Clean up extracted script
rm -f "$dash/create-predevals-data.R"
```

For dev `hubPredEvalsData-docker`, use the script from the local repo instead:
```bash
Rscript "$hubPredEvalsData_docker_path/scripts/create-predevals-data.R" \
  -h "$hub" \
  -c "$dash/predevals-config.yml" \
  -d "$hub/target-data/oracle-output.csv" \
  -o "$dash/data/evals"
```

## Step 3: Site (site-builder, Docker)

### Local data mode

`render.sh` merges into an existing `_site` (`cp -R tmp/_site/ $PWD/_site`), so clear it first or stale files survive (e.g. an old CDN `predevals_interface.js`, a missing local `predevals.bundle.js`).

```bash
docker pull --platform=linux/amd64 ghcr.io/hubverse-org/hub-dash-site-builder:latest

rm -rf "$dash/_site"

docker run --rm \
  --platform=linux/amd64 \
  -v "$dash":"/site" \
  ghcr.io/hubverse-org/hub-dash-site-builder:latest \
  render.sh \
  -p "data/ptc" -e "data/evals" \
  -o "_site"
```

### Remote data mode (public repos)

```bash
docker run --rm \
  --platform=linux/amd64 \
  -v "$dash":"/site" \
  ghcr.io/hubverse-org/hub-dash-site-builder:latest \
  render.sh \
  -u "<owner>" -r "<repo>" \
  -o "_site"
```

## Preview

```bash
uv run python3 -m http.server 8080 -d "$dash/_site"
# Open http://localhost:8080
```

For a dev `predevals` build, the eval page's ES-module bundle is cached aggressively — a normal refresh often keeps serving the old (often CDN) bundle. Hard-refresh (Cmd/Ctrl+Shift+R) or use an incognito window, or serve with no-cache headers (`Cache-Control: no-store`) so every refresh re-fetches. Confirm server-side before assuming a build problem: `diff "$dash/_site/resources/predevals.bundle.js" "$predevals_path/dist/predevals.bundle.js"` and check the served interface imports `./predevals.bundle.js`, not the CDN.

## Expected output structure

```
dashboard/
  data/
    ptc/
      targets/          # JSON files per location/date
      forecasts/        # JSON files per model/location/date
      predtimechart-options.json
    evals/
      scores/           # Nested CSV directories
      predevals-options.json
  _site/
    index.html
    forecast.html
    eval.html           # Only if evals data was generated
    resources/
```

## Dev version overrides

### predtimechart (install from branch)
```bash
uv run pip install --quiet "git+https://github.com/hubverse-org/hub-dashboard-predtimechart@<branch>"
```

### hubPredEvalsData-docker (dev image, ephemeral smoke test)

The dev image inherits from a published base (`ghcr.io/hubverse-org/hubpredevalsdata-base:<R-minor>`) and is itself published. Images are tagged by R-minor version (e.g. `4.5`); there is no `:latest` tag.

**Smoke testing must never write a host `renv.lock`** (that is only for deliberate version bumps). So do **not** bind-mount any repo over `/project`; use the renv project baked into the image and mount everything else elsewhere, so all `renv` writes stay in the throwaway container.

```bash
# Pull the published dev image (build from a checkout only if it changes baked
# files: the Dockerfiles, DESCRIPTION, .Rprofile, renv/activate.R)
docker pull --platform=linux/amd64 ghcr.io/hubverse-org/hubpredevalsdata-dev:4.5

# Start a container with NOTHING over /project. hub read-only, dashboard
# read-write (for output), dev repos read-only under /dev.
docker run -d --platform=linux/amd64 --name dev-evals \
  -v "$hub":/hub:ro \
  -v "$dash":/dash \
  -v "$hubPredEvalsData_path":/dev/hubPredEvalsData:ro \
  -v "$hubPredEvalsData_docker_path":/dev/hubPredEvalsData-docker:ro \
  ghcr.io/hubverse-org/hubpredevalsdata-dev:4.5 sleep infinity

# Install released packages into the baked project, then layer dev packages
# (lock = TRUE updates the in-container lockfile only):
docker exec dev-evals Rscript scripts/update.R
docker exec dev-evals Rscript -e 'renv::install("/dev/hubPredEvalsData", lock = TRUE)'

# Run the pipeline. create-predevals-data.R is NOT on PATH in the dev image, so
# use Rscript. Run the MOUNTED checkout's script to exercise docker-repo changes;
# omit -d to test the forthcoming hubData oracle auto-discovery.
docker exec dev-evals Rscript /dev/hubPredEvalsData-docker/scripts/create-predevals-data.R \
  -h /hub -c /dash/predevals-config.yml -o /dash/data/evals

docker stop dev-evals && docker rm dev-evals
```

### predevals (native R from branch)
```r
remotes::install_github("hubverse-org/hubPredEvalsData@<branch>", upgrade = "always")
```

### site-builder (build dev Docker image)
```bash
git clone -b <branch> https://github.com/hubverse-org/hub-dash-site-builder.git /tmp/site-builder-dev
cd /tmp/site-builder-dev
docker build --platform=linux/amd64 -t hub-dash-site-builder:dev .
# Then use hub-dash-site-builder:dev in docker run
```

To test a dev `predevals` bundle through site-builder, before `docker build` patch the static resources in the checkout (see SKILL.md "Dev site-builder"): copy `predevals.bundle.js` into `static/resources/`, repoint the `predevals_interface.js` import from the CDN to `./predevals.bundle.js`, and add the bundle to `static/_quarto.yml` `resources:` so Quarto copies it. The site-builder `main` already loads the front-end libs the current predevals needs (d3, dataTables `columnControl`/`fixedColumns`).
