---
name: dashboard-local-build
description: >
  Guide a developer through building a hub dashboard locally, including
  forecast data (predtimechart), evaluation data (predevals), and the
  rendered site (site-builder). Use when someone needs to build, preview,
  or test a dashboard on their local machine.
allowed-tools: [Bash, Read, Write, Glob, Grep, Agent, AskUserQuestion]
disable-model-invocation: true
---

# Local Dashboard Build

Build a hub dashboard locally using the three-tool pipeline: predtimechart (forecasts), predevals (evaluations), and site-builder (rendered site).

**Use `AskUserQuestion` at every decision point.** Whenever this skill presents options to the user (branch selection, build scope, evals path, local clone location, etc.), use the `AskUserQuestion` tool with well-labelled options rather than printing choices as text. When multiple questions don't depend on each other's answers (e.g. the three dev tool group questions when build scope is "All"), combine them into a single `AskUserQuestion` call using the `questions` array.

**Safety rules:**
- **Never modify source code, config files, or data** in any hub, dashboard, or tool repo. The only files this skill should write are build outputs (`data/ptc/`, `data/evals/`, `_site/` via Bash) and `~/.claude/dashboard-repos.yml` (via Write tool). Do not use the Write tool for anything else.
- **Check for uncommitted changes** before switching branches on any repo. If there are uncommitted changes, warn the user and ask whether to proceed, stash, or abort.
- **Never run `git pull`, `git push`, `git reset`, or `git merge`** on the user's repos without explicit confirmation.
- **All cloning goes to `/tmp/`** unless the user provides a different path.
- **Never save `/tmp/` paths** to `~/.claude/dashboard-repos.yml`. These are ephemeral clone locations that will not persist across sessions.

Read `${CLAUDE_SKILL_DIR}/references/pipeline-commands.md` for the exact command reference.

## Locate repo procedure

Reusable procedure for finding a local path and branch for a given repo. Two variants:

### Known repo (test repos and tool repos)

These repos can have their paths saved in `~/.claude/dashboard-repos.yml` for reuse across runs. The known repos are: `dashboard-test-hub-dashboard`, `dashboard-test-hub`, `hub-dashboard-predtimechart`, `hub-data`, `hubPredEvalsData`, `hubEvals`, `hubPredEvalsData-docker`, `predevals`, `hub-dash-site-builder`.

1. Check `~/.claude/dashboard-repos.yml` for a saved path:
   ```bash
   saved_path=$(yq '."<repo-name>"' ~/.claude/dashboard-repos.yml 2>/dev/null)
   ```

2. Use `AskUserQuestion` to locate the repo:
   - header: short repo name (e.g. "Test dash", "predtimechart")
   - Option 1 (only if saved path exists and the directory is valid): "$saved_path" with description "Previously saved path"
   - Next option: "Clone to /tmp/" with description "Clone hubverse-org/<repo-name> into /tmp/"
   - Last option: "Provide a path" with description "Provide a local path to this repo"

3. If cloning:
   ```bash
   repo_path="/tmp/<repo-name>"
   git clone "https://github.com/hubverse-org/<repo-name>.git" "$repo_path"
   ```

4. **Choose branch.** Get the current branch:
   ```bash
   current=$(git -C "$repo_path" branch --show-current)
   ```

   Use `AskUserQuestion`:
   - header: use the same short repo name as step 2 with " branch" appended (e.g. "Test dash branch", "predtimechart branch")
   - Option 1: `$current` with description "Currently checked out branch"
   - Option 2 (only if a suggested branch was passed in, it differs from `$current`, and it exists on this repo): the suggested branch with description provided by caller
   - Next option: `main` (only if not already listed above) with description "Use the main branch"
   - Last option: "Custom" with description "Provide a different branch name"

   To check if a suggested branch exists:
   ```bash
   git -C "$repo_path" branch -a --list "*<suggested_branch>"
   ```

   If the chosen branch differs from the current, first check for uncommitted changes:
   ```bash
   git -C "$repo_path" status --porcelain
   ```
   If there are uncommitted changes, use `AskUserQuestion`:
   - header: "Uncommitted"
   - Option 1: "Stash and switch" with description "Stash changes, switch branch, restore later"
   - Option 2: "Abort" with description "Stay on the current branch, do not switch"

   If proceeding:
   ```bash
   git -C "$repo_path" fetch origin
   git -C "$repo_path" checkout <branch>
   ```

5. **Save path.** Skip this step if the resolved path is under `/tmp/` (ephemeral paths must never be saved). Otherwise, if the resolved path is new or changed, use `AskUserQuestion`:
   - header: "Save path"
   - Option 1: "Yes (Recommended)" with description "Save this path to ~/.claude/dashboard-repos.yml for future runs"
   - Option 2: "No" with description "Don't save, ask again next time"

### Ad-hoc repo (user-specified dashboard or hub)

For repos not in the known set. No path saving.

1. Use `AskUserQuestion`:
   - header: short label (e.g. "Dashboard", "Hub repo")
   - Option 1: "Provide a local path" with description "Provide the path to an existing local clone"
   - Option 2: "Provide a GitHub URL" with description "Provide the GitHub URL to clone into /tmp/"

2. If cloning:
   ```bash
   repo_path="/tmp/$(basename <repo-url> .git)"
   git clone "<repo-url>" "$repo_path"
   ```

3. **Choose branch** using the same pattern as the known repo variant (current, suggested if provided, main, custom).

---

## 1. Orient

Resolve a local dashboard repo path (`$dash`) and hub repo path (`$hub`), each on the correct branch.

### Detect starting context

1. Check if `site-config.yml` exists in the current directory. If yes, this is a **dashboard repo**.
2. If not, check if `hub-config/tasks.json` exists. If yes, this is a **hub repo**.
3. If neither, use `AskUserQuestion`:
   - header: "Repo context"
   - Option 1: "Use test repos" with description "Use the test dashboard (hubverse-org/dashboard-test-hub-dashboard) and test hub (hubverse-org/dashboard-test-hub)"
   - Option 2: "Provide a path" with description "Provide a local path to a dashboard or hub repo"

   If the user provides a path, re-detect from that path (check for `site-config.yml` or `hub-config/tasks.json`).

### Resolve the dashboard

**If in a dashboard repo**: set `$dash` to the current directory.

**If in a hub repo**: use the **ad-hoc repo** procedure (header: "Dashboard") to get `$dash`. The hub does not contain information about which dashboard belongs to it.

**If using test repos**: use the **known repo** procedure for `dashboard-test-hub-dashboard` (header: "Test dash") to get `$dash`.

### Resolve the hub

**If in a hub repo**: set `$hub` to the current directory.

**If using test repos**: use the **known repo** procedure for `dashboard-test-hub` (header: "Test hub") to get `$hub`. Pass the dashboard branch as the suggested branch with description "Match the dashboard branch (paired branches for cross-repo testing)".

**Otherwise**: extract the hub slug from the dashboard config:
```bash
hub_slug=$(yq '.hub' "$dash/site-config.yml" | tr -d '"' | sed 's|/$||')
hub_repo_name=$(basename "$hub_slug")
```

If this is a known repo (i.e. `dashboard-test-hub`), use the **known repo** procedure. Otherwise, use the **ad-hoc repo** procedure (header: "Hub repo") with GitHub URL `https://github.com/${hub_slug}.git`. For the ad-hoc variant, if `$dash` is not in `/tmp`, prepend an option for `$(dirname "$dash")/$hub_repo_name` with description "Sibling directory to the dashboard repo".

In both cases, pass the dashboard branch as the suggested branch with description "Match the dashboard branch (paired branches for cross-repo testing)".

### Build options

Use `AskUserQuestion` to determine what to build:
- header: "Build scope"
- Option 1: "All (Recommended)" with description "Run forecasts, evals, and site render"
- Option 2: "Forecasts only" with description "Run only the predtimechart step, skip evals and site render"
- Option 3: "Evals only" with description "Run only the predevals step, skip forecasts and site render"
- Option 4: "Site only" with description "Re-render the site using existing data from a previous full build"

The selected scope controls which steps (4, 5, 6) are executed:
- **All**: Steps 4, 5, 6
- **Forecasts only**: Step 4 only
- **Evals only**: Step 5 only
- **Site only**: Step 6 only. Before running, verify the expected data exists. Check which configs the dashboard has (`predtimechart-config.yml`, `predevals-config.yml`) and confirm that the corresponding data directories (`data/ptc/`, `data/evals/`) are populated. If any expected data is missing, warn the user and use `AskUserQuestion` to ask whether to switch to "All" to generate the missing data first, or proceed with only the data that exists.

### Dev versions

Use `AskUserQuestion`:
- header: "Dev versions"
- Option 1: "Released versions (Recommended)" with description "Use the latest published release of all tools"
- Option 2: "Test dev versions" with description "Use a local repo checkout for one or more pipeline tools"

If the user chooses dev versions, only present tools relevant to the selected build scope. Use `AskUserQuestion` with `multiSelect: true`:

**If forecasts are being built**:
- header: "Forecast tools"
- Option 1: "hub-dashboard-predtimechart" with description "Python forecast data generator (pip install from local repo)"
- Option 2: "hubdata" with description "Python hub data access library (dependency of predtimechart)"
- Option 3: "None" with description "Use released versions for forecast tools"

**If evals are being built**:
- header: "Eval tools"
- Option 1: "hubPredEvalsData" with description "R package for evaluation scores"
- Option 2: "hubEvals" with description "R scoring functions (dependency of hubPredEvalsData)"
- Option 3: "hubPredEvalsData-docker" with description "Docker wrapper for the R evals pipeline (Dockerfile, scripts)"
- Option 4: "None" with description "Use released versions for eval tools"

**If site is being built**:
- header: "Site tools"
- Option 1: "hub-dash-site-builder" with description "Docker site renderer (Quarto templates, render.sh)"
- Option 2: "predevals" with description "JavaScript eval visualization module (loaded by site-builder from CDN)"
- Option 3: "None" with description "Use released versions for site tools"

#### Locating tool repos

For each selected tool, use the **known repo** procedure to get a local path and branch.

#### Dependency relationships

Inform the user of these relationships so they can decide whether downstream tools also need dev versions:

- **hubEvals** is a dependency of **hubPredEvalsData**. A dev hubEvals may require rebuilding the predevals Docker image. (Exact rebuild mechanism TBD.)
- **hubdata** is a dependency of **hub-dashboard-predtimechart**. Install into the same venv before predtimechart.
- **hubPredEvalsData** is packaged into **hubPredEvalsData-docker**. A dev hubPredEvalsData requires rebuilding the Docker image. The dev Docker path in Step 2 handles this.
- **predevals** (JS) is loaded by **hub-dash-site-builder** from CDN. A dev predevals requires building the JS bundle locally and modifying render.sh to use the local dist, so hub-dash-site-builder also needs a dev build.

Use `AskUserQuestion` to confirm whether the user wants to also locate any implied downstream tools that weren't already selected.

## 2. Check prerequisites

Run each check and report results before proceeding:

```bash
# Docker
docker info > /dev/null 2>&1 && echo "Docker: OK" || echo "Docker: NOT RUNNING"

# uv (needed for predtimechart)
uv --version 2>/dev/null && echo "uv: OK" || echo "uv: NOT FOUND (install: https://docs.astral.sh/uv/)"

# gh CLI
gh auth status 2>/dev/null && echo "gh: OK" || echo "gh: NOT AUTHENTICATED"

# yq
yq --version 2>/dev/null && echo "yq: OK" || echo "yq: NOT FOUND"
```

If any required tool is missing, explain how to install it and stop. Docker is required for evals and site steps but not for forecasts.

## 3. Setup

Create the output directories:
```bash
mkdir -p "$dash/data/ptc/"{targets,forecasts}
mkdir -p "$dash/data/evals"
```

## 4. Step 1: Generate forecasts (predtimechart)

**Skip condition**: No `predtimechart-config.yml` in the dashboard repo.

### Install predtimechart

```bash
uv venv --seed "$dash/.venv"
source "$dash/.venv/bin/activate"
```

For the **released version** (default):
```bash
latest=$(gh api -X GET "repos/hubverse-org/hub-dashboard-predtimechart/releases/latest" --jq ".tag_name")
uv run pip install --quiet --upgrade pip
uv run pip install --quiet "git+https://github.com/hubverse-org/hub-dashboard-predtimechart@$latest"
```

For a **dev version**, install from the local repo. If hubdata was also selected as dev, install it first:
```bash
uv run pip install --quiet "$hubdata_path"  # only if hubdata is dev
uv run pip install --quiet "$predtimechart_path"
```

### Generate data

```bash
ptc_generate_target_json_files \
  "$hub" \
  "$dash/predtimechart-config.yml" \
  "$dash/data/ptc/targets"

ptc_generate_json_files \
  "$hub" \
  "$dash/predtimechart-config.yml" \
  "$dash/data/ptc/predtimechart-options.json" \
  "$dash/data/ptc/forecasts"
```

### Verify outputs

Run the checks below. If any counts are zero, investigate the error output from the previous commands before proceeding.

```bash
echo "Target files: $(ls $dash/data/ptc/targets/*.json 2>/dev/null | wc -l)"
echo "Forecast files: $(ls $dash/data/ptc/forecasts/*.json 2>/dev/null | wc -l)"
echo "Options file: $(ls $dash/data/ptc/predtimechart-options.json 2>/dev/null && echo 'exists' || echo 'MISSING')"
```

Collect tool versions for the final build report (see `references/build-info-schema.md` for commands). For dev installs, also note the install source (local path vs release tag).
```bash
echo "Python: $(python3 --version 2>&1)"
echo "predtimechart: $("$dash/.venv/bin/pip" show hub-dashboard-predtimechart 2>/dev/null | grep '^Version:' | cut -d' ' -f2)"
echo "hubdata: $("$dash/.venv/bin/pip" show hubdata 2>/dev/null | grep '^Version:' | cut -d' ' -f2)"
```

## 5. Step 2: Generate evaluations (predevals)

**Skip conditions** (explain to the user if skipping):
- No `predevals-config.yml` in the dashboard repo
- No `target-data/oracle-output.csv` in the hub

### Choose path

Check if R is available: `Rscript --version 2>/dev/null`

**If the user selected `hubPredEvalsData-docker` as a dev tool**, skip this question and go directly to the **Dev Docker path**. A dev docker repo checkout means building a fresh image from that checkout.

**Otherwise**, use `AskUserQuestion`:
- header: "Evals path"
- Option 1: "Docker (Recommended)" with description "Use the published Docker image, no R required"
- Option 2 (only if R is available): "Native R" with description "Install the R package directly, faster iteration"
- Option 3 (only if the user selected other dev evals tools like `hubPredEvalsData` or `hubEvals` but not `hubPredEvalsData-docker`): "Dev Docker" with description "Build a Docker image from local hubPredEvalsData-docker repo"

### Docker path

```bash
docker pull --platform=linux/amd64 ghcr.io/hubverse-org/hubpredevalsdata-docker:latest

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

### Native R path

The native R path uses the same `create-predevals-data.R` entrypoint script from `hubPredEvalsData-docker`, run directly with Rscript instead of inside Docker. This script handles reading the oracle CSV (with proper type parsing), calling `generate_eval_data`, and generating `predevals-options.json`.

#### Extract the script

For **released versions**, extract the script from the published Docker image (already pulled in the Docker prerequisite check or pull it now):
```bash
docker pull --platform=linux/amd64 ghcr.io/hubverse-org/hubpredevalsdata-docker:latest
predevals_script="$dash/create-predevals-data.R"
docker run --rm --platform=linux/amd64 --entrypoint cat \
  ghcr.io/hubverse-org/hubpredevalsdata-docker:latest \
  /usr/local/bin/create-predevals-data.R > "$predevals_script"
```

For a **dev version**, use the script from the local `hubPredEvalsData-docker` repo if the user selected it:
```bash
predevals_script="$hubPredEvalsData_docker_path/scripts/create-predevals-data.R"
```

If the user did not select `hubPredEvalsData-docker` as dev, fall back to extracting from the Docker image as above.

#### Install R dependencies

For **released versions**, install from r-universe and GitHub:
```r
install.packages("hubEvals", repos = c("https://hubverse-org.r-universe.dev", "https://cloud.r-project.org"))
remotes::install_github("hubverse-org/hubPredEvalsData", upgrade = "never")
```

For a **dev version**, install from local repos. If hubEvals was also selected as dev, install it first:
```r
remotes::install_local("<hubEvals_path>", upgrade = "always")  # only if hubEvals is dev
remotes::install_local("<hubPredEvalsData_path>", upgrade = "always")
```

#### Run the script

```bash
Rscript "$predevals_script" \
  -h "$hub" \
  -c "$dash/predevals-config.yml" \
  -d "$hub/target-data/oracle-output.csv" \
  -o "$dash/data/evals"
```

#### Clean up extracted script

If the script was extracted from the Docker image (not from a dev repo), remove it after the run:
```bash
rm -f "$dash/create-predevals-data.R"
```

### Dev Docker path

The `hubPredEvalsData-docker` repo provides dev Docker images for ephemeral testing. These use an empty R package library so packages resolve fresh from r-universe/CRAN, with no `GITHUB_PAT` needed.

#### Build the dev images

Build from the `hubPredEvalsData-docker` repo checkout (`$hubPredEvalsData_docker_path`):

```bash
docker build --platform linux/amd64 \
  -f "$hubPredEvalsData_docker_path/docker/base.Dockerfile" \
  -t hubpredevalsdata-base \
  "$hubPredEvalsData_docker_path"

docker build --platform linux/amd64 \
  -f "$hubPredEvalsData_docker_path/docker/dev.Dockerfile" \
  -t hubpredevalsdata-dev \
  "$hubPredEvalsData_docker_path"
```

The base image (system deps + R + renv) is cached and rarely needs rebuilding. The dev image adds project files on top and builds in seconds.

#### Start a dev container

Start a named container for the testing session. Mount the dashboard and hub repos for running the pipeline:

```bash
docker run -d --platform linux/amd64 --name dev-evals \
  -v "$dash":/project \
  -v "$hub":/hub \
  hubpredevalsdata-dev sleep infinity
```

If any dev R packages need to be installed from local checkouts, also mount those repos:
```bash
docker run -d --platform linux/amd64 --name dev-evals \
  -v "$dash":/project \
  -v "$hub":/hub \
  -v "$hubEvals_path":/dev/hubEvals \
  -v "$hubPredEvalsData_path":/dev/hubPredEvalsData \
  hubpredevalsdata-dev sleep infinity
```

#### Install packages

Install released packages from r-universe/CRAN (~2 min with pre-built binaries):
```bash
docker exec dev-evals Rscript scripts/update.R
```

If dev R packages were selected, layer them on top of the released packages:
```bash
docker exec dev-evals Rscript -e 'renv::install("/dev/hubEvals", lock = TRUE)'
docker exec dev-evals Rscript -e 'renv::install("/dev/hubPredEvalsData", lock = TRUE)'
```

Alternatively, install a dev package from a GitHub branch or PR:
```bash
docker exec dev-evals Rscript -e 'renv::install("hubverse-org/hubEvals@feature-branch", lock = TRUE)'
docker exec dev-evals Rscript -e 'renv::install("hubverse-org/hubPredEvalsData#42", lock = TRUE)'
```

#### Run the pipeline

```bash
docker exec dev-evals \
  create-predevals-data.R \
    -h "/hub" \
    -c "predevals-config.yml" \
    -d "/hub/target-data/oracle-output.csv" \
    -o "data/evals"
```

#### Clean up

Stop and remove the container when done. The container's R library is destroyed, leaving no artifacts on the host:
```bash
docker stop dev-evals && docker rm dev-evals
```

### Verify outputs

Run the checks below. If any counts are zero or the options file is missing, investigate the error output before proceeding.

```bash
echo "Score directories: $(find $dash/data/evals/scores -type d | wc -l)"
echo "Score files: $(find $dash/data/evals/scores -name 'scores.csv' | wc -l)"
echo "Options file: $(ls $dash/data/evals/predevals-options.json 2>/dev/null && echo 'exists' || echo 'MISSING')"
```

Collect tool versions for the final build report. If the **Docker** path was used:
```bash
echo "predevals image: $(docker inspect ghcr.io/hubverse-org/hubpredevalsdata-docker:latest --format='{{index .RepoDigests 0}}' 2>/dev/null)"
```

If the **Native R** path was used:
```bash
Rscript -e 'message("R version: ", getRversion()); hub_pkgs <- grep("^hub|^Hub", installed.packages()[,"Package"], value = TRUE); for (pkg in hub_pkgs) { desc <- packageDescription(pkg); message(pkg, " ", desc$Version, " (", if (!is.null(desc$Repository)) desc$Repository else if (!is.null(desc$RemoteType)) paste0(desc$RemoteType, ": ", desc$RemoteRepo, "@", substr(desc$RemoteSha, 1, 7)) else if (!is.null(desc$Built)) "local" else "unknown", ")") }'
```

If exiting early due to an error during the evals step, skip ahead to the build report (section 7) and report what was collected so far.

## 6. Step 3: Build site (site-builder)

### Build with local data (default)

```bash
docker pull --platform=linux/amd64 ghcr.io/hubverse-org/hub-dash-site-builder:latest
```

Construct the `render.sh` flags based on which data steps completed:

If **both** forecasts and evals data exist:
```bash
docker run --rm \
  --platform=linux/amd64 \
  -v "$dash":"/site" \
  ghcr.io/hubverse-org/hub-dash-site-builder:latest \
  render.sh \
  -p "data/ptc" -e "data/evals" \
  -o "_site"
```

If **only forecasts** data exists:
```bash
docker run --rm \
  --platform=linux/amd64 \
  -v "$dash":"/site" \
  ghcr.io/hubverse-org/hub-dash-site-builder:latest \
  render.sh \
  -p "data/ptc" \
  -o "_site"
```

If **only evals** data exists:
```bash
docker run --rm \
  --platform=linux/amd64 \
  -v "$dash":"/site" \
  ghcr.io/hubverse-org/hub-dash-site-builder:latest \
  render.sh \
  -e "data/evals" \
  -o "_site"
```

### Build with remote data (public repos only)

If the dashboard has data already published to `ptc/data` and `predevals/data` branches:
```bash
docker run --rm \
  --platform=linux/amd64 \
  -v "$dash":"/site" \
  ghcr.io/hubverse-org/hub-dash-site-builder:latest \
  render.sh \
  -u "<owner>" -r "<repo>" \
  -o "_site"
```

### Dev site-builder

If also using a dev `predevals` (JS), the site-builder repo needs modification (patching the JS import, adding the bundle, updating `_quarto.yml`). If the repo is not already in `/tmp/`, make a temporary copy:

```bash
if [[ "$site_builder_path" != /tmp/* ]]; then
  tmp_site_builder="/tmp/hub-dash-site-builder-build"
  cp -r "$site_builder_path" "$tmp_site_builder"
else
  tmp_site_builder="$site_builder_path"
fi
```

Use `$tmp_site_builder` as the working directory for all subsequent steps in this section. If dev `predevals` is not selected, `$tmp_site_builder` can just be `$site_builder_path` (no copy needed since no modifications are made).

#### Build dev predevals bundle

If using a dev `predevals` (JS), build the JS bundle first:
```bash
cd "$predevals_path"
npm install
npm run build
```

Then patch the site-builder copy:

1. Copy the bundle into the static resources:
   ```bash
   cp "$predevals_path/dist/predevals.bundle.js" "$tmp_site_builder/static/resources/predevals.bundle.js"
   ```

2. Update `predevals_interface.js` to import from the local bundle instead of the CDN:
   ```bash
   sed -i '' 's|import App from "https://cdn.jsdelivr.net/gh/hubverse-org/predevals@v1/dist/predevals.bundle.js"|import App from "./predevals.bundle.js"|' \
     "$tmp_site_builder/static/resources/predevals_interface.js"
   ```

3. Add the bundle to `_quarto.yml` resources so Quarto copies it to the output site:
   ```bash
   sed -i '' '/resources\/predevals_interface.js/a\
     - resources/predevals.bundle.js' "$tmp_site_builder/static/_quarto.yml"
   ```

#### Build the image

```bash
cd "$tmp_site_builder"
docker build --platform=linux/amd64 -t hub-dash-site-builder:dev .
```

If a temporary copy was created, clean it up after the build:
```bash
[[ "$tmp_site_builder" != "$site_builder_path" ]] && rm -rf "$tmp_site_builder"
```

Use `hub-dash-site-builder:dev` instead of the published image in the `docker run` command.

### Verify outputs

Check that expected pages exist. `index.html` and `forecast.html` should always be present. If predevals data was generated, `eval.html` should also exist.

```bash
echo "Site directory: $(ls -d $dash/_site 2>/dev/null && echo 'exists' || echo 'MISSING')"
echo "Pages: $(ls $dash/_site/*.html 2>/dev/null)"
```

Collect tool versions for the final build report:
```bash
echo "site-builder image: $(docker inspect ghcr.io/hubverse-org/hub-dash-site-builder:latest --format='{{index .RepoDigests 0}}' 2>/dev/null)"
```

## 7. Build report

After all steps complete (or if a step fails), present a single consolidated report to the user covering everything that was built. Include:

**Repos:**
```bash
echo "Dashboard: $(git -C "$dash" branch --show-current)@$(git -C "$dash" rev-parse --short HEAD) ($dash)"
echo "Hub: $(git -C "$hub" branch --show-current)@$(git -C "$hub" rev-parse --short HEAD) ($hub)"
```

**Results per step** (only for steps that were executed):
- Forecasts: target file count, forecast file count, options file status, data path
- Evals: score directory count, score file count, options file status, data path
- Site: list of HTML pages generated, site path

**Tool versions** collected during each step (Python version, package versions, Docker image digests, R package versions as applicable). For dev installs, include the source (local repo path and branch).

**Status**: whether each step succeeded or failed. If a step failed, include the key error message.

This report gives the user a complete picture of the build in one place, making it easy to verify correctness and reproduce issues.

## 8. Preview

```bash
uv run python3 -m http.server 8080 -d "$dash/_site"
```

Tell the user to open http://localhost:8080 in their browser.

## 9. Teardown

When the user is done previewing, or before the conversation ends, run teardown. Use `AskUserQuestion`:
- header: "Teardown"
- Option 1: "Clean up everything (Recommended)" with description "Stop preview server, remove .venv and build artifacts (data/ptc, data/evals, _site)"
- Option 2: "Keep build artifacts" with description "Stop preview server and remove .venv, but keep generated data and site"
- Option 3: "Keep everything" with description "Only stop the preview server, keep .venv and all outputs"

### Stop the preview server

```bash
pid=$(lsof -ti:8080 2>/dev/null)
if [ -n "$pid" ]; then
  kill "$pid" && echo "Preview server stopped" || echo "Failed to stop server"
else
  echo "No server running on port 8080"
fi
```

### Remove the virtual environment

```bash
rm -rf "$dash/.venv"
```

### Remove build artifacts

```bash
rm -rf "$dash/data/ptc" "$dash/data/evals" "$dash/_site"
```

Report what was cleaned up to the user.

## 10. Troubleshooting

If a step fails, check the error output and match against these patterns:

- **"no matching manifest for linux/amd64"**: The Docker command is missing the `--platform=linux/amd64` flag. All commands in this workflow already include it, so this should only appear if a command was modified.
- **"unable to find column 'date'"**: The hub uses the new time-series target data standard. Remove `target_data_file_name` from `predtimechart-config.yml`. When this field is set, predtimechart expects old-format columns (`date`/`value`); when absent, it uses the standard columns (`target_end_date`/`observation`).
- **"invalid ptc_config_file"**: The `predtimechart-config.yml` has a validation error. Read the file, check that `rounds_idx` matches the hub's `tasks.json` structure, and report the mismatch to the user.
- **Schema validation errors in predevals**: Read `predevals-config.yml` and check that `schema_version` points to a valid, published schema URL. Run `curl -sI <schema_url>` to verify the URL resolves. If it returns 404, the schema version may be ahead of the published release.
- **"docker-credential-desktop: executable file not found in $PATH"**: Docker Desktop's credential helper is not on the shell PATH. Prepend it: `export PATH="/Applications/Docker.app/Contents/Resources/bin:$PATH"` before running `docker pull` or `docker run`. This is common when running from non-login shells or automated tools.
- **"the input device is not a TTY"**: The `docker run` command includes `-it` but is running in a non-interactive context. Remove the `-it` flag (use `--rm` alone). All `docker run` commands in this workflow use `--rm` without `-it` for this reason.
- **"command not found: python"**: On macOS, the `python` command may not exist. Use `uv run python3` instead, since `uv` is already a prerequisite.
- **"docker: Cannot connect to the Docker daemon"**: Docker Desktop is not running. Tell the user to start Docker Desktop and wait for it to be ready, then retry.
- **"No module named" or "command not found: ptc_generate"**: The virtual environment was not activated or the install failed. Re-run the venv activation (`source "$dash/.venv/bin/activate"`) and verify the install with `uv run pip show hub-dashboard-predtimechart`.
- **Reusing cached Docker images**: After the first `docker pull`, images are cached locally. Subsequent runs skip downloading unchanged layers. To force a fresh pull, run `docker pull` again. To check cached images: `docker images | grep hubverse`.
