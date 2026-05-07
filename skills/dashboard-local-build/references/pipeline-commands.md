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

```bash
docker pull --platform=linux/amd64 ghcr.io/hubverse-org/hub-dash-site-builder:latest

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

### predevals (build dev Docker image)
```bash
git clone -b <branch> https://github.com/hubverse-org/hubPredEvalsData-docker.git /tmp/predevals-docker-dev
cd /tmp/predevals-docker-dev
docker build --platform=linux/amd64 -t hubpredevalsdata-docker:dev .
# Then use hubpredevalsdata-docker:dev in docker run
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
