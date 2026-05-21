---
name: explore-hub
description: Answer questions about a locally-cloned hubverse hub - who submitted forecasts, which models cover which targets and locations, submission history, and forecast data analysis. Requires a path to the hub as the first argument.
argument-hint: "<hub-path> <question>"
allowed-tools: Read Glob Write WebFetch Bash(uv sync *) Bash(uv run *)
metadata:
  skill-author: Reichlab, UMass, Amherst, MA
---

# Explore Hub

## Core Workflow

1. **Establish the hub path** - from `$ARGUMENTS[0]`. If it doesn't exist or isn't a valid hub, stop and tell the user.

2. **Parse the question** - if no question was provided, greet the user, confirm the hub, and prompt them for a question. Otherwise, identify intent and any constraints (targets, locations, models, date ranges, seasons, rounds). Use judgment to generalize for any question type.

3. **State assumptions before writing any code** - identify every parameter that isn't fully specified (e.g., "recent", "this season", an unspecified location or target). Present them as a blockquote with a bold **Assumptions** header and one bullet per assumption, e.g.:
   > **Assumptions**
   > - "Recent" means the last 4 rounds
   > - Season is 2025–2026 (August 1, 2025 – July 31, 2026)

   Do not wait for confirmation; proceed with those assumptions.
   - **Season convention**: unless the user specifies otherwise, seasons run August 1 – July 31; the current season began the most recent August 1.
   - **Rounds convention**: a round's `round_id` is determined by `round_id_from_variable` in `hub-config/tasks.json` — if `true`, the round_id is the value of the task ID variable named `round_id`; if `false`, it's the literal `round_id` string. Round IDs are almost always ISO dates (`yyyy-mm-dd`).

4. **Choose the data source** - use the first source in this list that can answer the question:
   - `hub-config/tasks.json` - for valid targets, locations, task ID values, hub configuration
   - `model-metadata/` - for team/model membership and model attributes
   - `model-output/` file names - for submission history (who submitted when)
   - `model-output/` file contents - for forecast values (most expensive; filter aggressively)

5. **Retrieve data** - read files directly or run Python via `uv run`. See @references/data-sources.md for code examples and conventions.

6. **Answer in plain English** - present results directly as counts, lists, or comparisons. Never dump raw script output or data structures at the user.


7. **Reproducible scripts** - at the start of the session, let the user know they can ask for a standalone script (Python or R) to reproduce any result. When they request one:
   - **Python**: use [`hub-data`](https://github.com/hubverse-org/hub-data) only — no skill-internal utilities
   - **R**: use [`hubData`](https://github.com/hubverse-org/hubData) only
   - The script must be fully self-contained: no references to `/tmp/explore_hub_query.py`, `util.py`, or any other skill internals
   - Parameterize the hub path so the user can adapt it to their environment

## Resources

- Documentation: Full documentation is at https://docs.hubverse.io/en/latest/ .
- Python hub-data library: The https://github.com/hubverse-org/hub-data library (documentation at https://hubverse-org.github.io/hub-data/ ) provides functionality to access a hub's data via Python. It's required by @scripts/util.py , which supports this skill.
- Running Python: We use https://docs.astral.sh/uv/ to run Python scripts. When you load this skill, note the directory containing this SKILL.md file - call it `SKILL_DIR`. (You can confirm it from the absolute path of any `@`-referenced file you read.) Run `uv sync --project $SKILL_DIR` once to set up the environment, then use `uv run --project $SKILL_DIR python3` to execute scripts. **Never run Python inline via heredoc (`uv run python3 - << 'EOF'`).** Always write the script to `/tmp/explore_hub_query.py` using the `Write` tool, then run `uv run --project $SKILL_DIR python3 /tmp/explore_hub_query.py`. **Important:** Before calling `Write`, first run `rm -f /tmp/explore_hub_query.py` via Bash to ensure the file doesn't exist - `Write` fails on existing files that haven't been read in the current session.



