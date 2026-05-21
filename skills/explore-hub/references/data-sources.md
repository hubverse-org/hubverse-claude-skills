# Data Sources

Python examples for accessing hub data. Scripts use `uv run python3` (dependencies declared in `pyproject.toml`).

## 1. `hub-config/tasks.json`

Full docs: https://docs.hubverse.io/en/latest/user-guide/tasks.html

Access via `HubConnection.tasks`, or use helper functions in `scripts/util.py`.

```python
import json
from hubdata import connect_hub


hub = '/path/to/repos/covid19-forecast-hub'
hub_connection = connect_hub(hub)
print(json.dumps(hub_connection.tasks, indent=4))
```

## 2. `model-metadata/` directory

Full docs: https://docs.hubverse.io/en/latest/user-guide/model-metadata.html

Files are named `{team_abbr}-{model_abbr}.yml`. Schema is defined in `hub-config/model-metadata-schema.json`.
Use `scripts.util.team_abbr_to_model_abbrs()` for team/model membership:

```python
from hubdata import connect_hub
import scripts.util


hub = '/path/to/repos/covid19-forecast-hub'
hub_connection = connect_hub(hub)

# What teams participate in the hub?
list(scripts.util.team_abbr_to_model_abbrs(hub_connection).keys())
# ['UMass', 'MOBS', 'JHU_CSSE', 'OHT_JHU', 'NEU_ISI', 'Google_SAI', 'CMU', 'CADPH', 'CEPH', 'UM', 'UGA_flucast', 'Metaculus', 'CFA_Pyrenew', 'CFA', 'CovidHub']

# Which models does the team 'UMass' manage?
scripts.util.team_abbr_to_model_abbrs(hub_connection)['UMass']
# ['gbqr', 'ar6_pooled']
```

## 3. `model-output/` directory

Full docs: https://docs.hubverse.io/en/latest/user-guide/model-output.html

Subdirectories are named for each model (e.g., `model-output/CovidHub-ensemble`). Files within are named
`{round_id}-{model_id}.csv` (or `.parquet`), e.g., `2026-04-04-CovidHub-ensemble.csv`.

### 3a. Submission information (from file names)

The presence of a file asserts that `model_id` submitted for `round_id`. Use `scripts.util.model_file_submissions()`:

```python
from hubdata import connect_hub
import scripts.util


hub = '/path/to/repos/covid19-forecast-hub'
hub_connection = connect_hub(hub)
hub_ds = hub_connection.get_dataset()

# Which round_ids did 'CovidHub-ensemble' submit for?
model_id_to_round_ids = scripts.util.model_file_submissions(hub_ds, is_key_model_id=True)
model_id_to_round_ids['CovidHub-ensemble']
# ['2024-11-23', '2024-11-30', ..., '2026-04-04']

# Which model_ids submitted on 2025-11-22?
round_id_to_model_ids = scripts.util.model_file_submissions(hub_ds, is_key_model_id=False)
round_id_to_model_ids['2025-11-22']
# ['CFA-EpiAutoGP', 'CFA_Pyrenew-PyrenewHEW_COVID', ..., 'UMass-gbqr']

```

### 3b. Forecast data (from file contents)

Access via `HubConnection.get_dataset()`, which returns a pyarrow `Dataset`
(docs: https://hubverse-org.github.io/hub-data/usage.html). Use Polars for grouping, sorting, etc.

```python
import polars as pl
import pyarrow.compute as pc
from hubdata import connect_hub


hub = '/path/to/repos/covid19-forecast-hub'
hub_connection = connect_hub(hub)
hub_ds = hub_connection.get_dataset()

pa_table = hub_connection.to_table(
    columns=['target_end_date', 'value', 'output_type', 'output_type_id', 'reference_date'],
    filter=(pc.field('location') == 'US') & (pc.field('target') == 'wk inc covid hosp'))

df = (
    pl.from_arrow(pa_table)
    .group_by(pl.col('target_end_date'))
    .agg(pl.col('value').count())
    .sort('target_end_date')
)
```

## 4. Constraining by task IDs

Task ID variables (columns in model output files) and their allowed values come from `hub-config/tasks.json`. Use `scripts.util.task_id_to_values()`:

```python
from hubdata import connect_hub
import scripts.util


hub = '/path/to/repos/covid19-forecast-hub'
hub_connection = connect_hub(hub)
task_id_to_vals = scripts.util.task_id_to_values(hub_connection)

# What task IDs are in the hub?
list(task_id_to_vals.keys())
# ['reference_date', 'location', 'horizon', 'target_end_date', 'target']

# What locations are allowed?
task_id_to_vals['location']
# {'40', '32', '35', '50', '31', '41', '53', '30', '33', '44', '54', 'US', ...}

```

## 5. Working with rounds

Use `scripts.util.rounds()` to access all rounds. Use `datetime.date.fromisoformat()` for date comparisons.

```python
from hubdata import connect_hub

import scripts.util


# "What rounds are available in this hub?"
hub = '/path/to/repos/covid19-forecast-hub'
hub_connection = connect_hub(hub)
all_rounds = scripts.util.rounds(hub_connection)

sorted(list(all_rounds))
# ['2024-11-16', '2024-11-23', ..., '2026-05-30']

# "What rounds have been submitted for so for?"
hub_ds = hub_connection.get_dataset()
round_id_to_model_ids = scripts.util.model_file_submissions(hub_ds, is_key_model_id=False)
submitted_rounds = list(round_id_to_model_ids.keys())
sorted(list(submitted_rounds))
# ['2024-11-23', '2024-11-30', ..., '2026-04-11']

```
