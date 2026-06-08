from collections import defaultdict
from functools import reduce
from pathlib import Path

import pyarrow.dataset as ds
import yaml
from hubdata import HubConnection


#
# model_file_submissions()
#

def model_file_submissions(hub_ds: ds.FileSystemDataset, is_key_model_id: bool) -> dict[str, list[str]]:
    """
    A utility that returns a dict mapping each `model_id` to a list of its `round_id`s based on hub_ds. Note that
    round_ids are typically in 'YYYY-MM-DD' format. Files are obtained via `hub_ds.files`.

    :param hub_ds: a `FileSystemDataset` as returned by `HubConnection.get_dataset()`. Also supports
        `UnionDataset` (e.g. hubs with mixed CSV/parquet output).
    :param is_key_model_id: True if the returned dict's keys should be `model_id`s, and False if keys should be
        `round_id`s
    :return: a dict that maps *either* model_id -> round_ids (if is_key_model_id) else round_id -> model_ids
    """
    submissions_dict = defaultdict(list)
    for model_file in _dataset_files(hub_ds):
        # '/path/to/repos/flu-metrocast/model-output/ACCIDDA-InfluPaint/2026-01-31-ACCIDDA-InfluPaint.csv'
        model_file_p = Path(model_file)
        model_id = model_file_p.parts[-2]  # 'ACCIDDA-InfluPaint'
        round_id = model_file_p.stem.removesuffix(f"-{model_id}")  # '2026-01-31'
        if is_key_model_id:
            submissions_dict[model_id].append(round_id)
        else:
            submissions_dict[round_id].append(model_id)
    return submissions_dict


def _dataset_files(hub_ds: ds.Dataset) -> list[str]:
    """Returns all file paths from a dataset, handling both FileSystemDataset and UnionDataset."""
    if hasattr(hub_ds, 'files'):
        return hub_ds.files
    files = []
    for child in hub_ds.children:
        files.extend(_dataset_files(child))
    return files


#
# team_abbr_to_model_abbrs()
#

def team_abbr_to_model_abbrs(hub_conn: HubConnection) -> dict[str, list[str]]:
    """
    Terminology note: "model_abbr" is equivalent to "model_id".

    :return: returns a dict that maps `model-metadata/` dir `team_abbr`s to a list of each team's `model_abbr`s
    """
    team_dict = defaultdict(list)
    for model_metadata_file in (list((Path(hub_conn.hub_path) / 'model-metadata').glob('*.yml')) +
                                list((Path(hub_conn.hub_path) / 'model-metadata').glob('*.yaml'))):
        with open(model_metadata_file) as fp:
            model_metadata = yaml.safe_load(fp)
            team_abbr = model_metadata['team_abbr']
            model_abbr = model_metadata['model_abbr']
            team_dict[team_abbr].append(model_abbr)
    return team_dict


#
# model_id_to_team_abbr()
#

def model_id_to_team_abbr(hub_conn: HubConnection) -> dict[str, str]:
    """
    :return: a dict mapping each full model_id (e.g. 'UMass-gbqr') to its team_abbr (e.g. 'UMass')
    """
    return {f"{team}-{model_abbr}": team
            for team, model_abbrs in team_abbr_to_model_abbrs(hub_conn).items()
            for model_abbr in model_abbrs}


#
# task_id_to_values()
#

def task_id_to_values(hub_conn: HubConnection) -> dict[str, set]:
    """
    :return: a dict that maps each task_id in `hub_conn`'s `tasks` to a set of its joined `required` and `optional`
        values
    """
    # merge dicts from all rounds
    return reduce(lambda x, y: x | y, [_task_id_to_values_round(the_round) for the_round in hub_conn.tasks['rounds']])


def _task_id_to_values_round(the_round: dict) -> dict[str, set]:
    task_id_dict = defaultdict(set)
    for model_task in the_round['model_tasks']:
        for task_id_key, task_id_value in model_task['task_ids'].items():
            required = task_id_value['required']
            optional = task_id_value['optional']
            task_id_dict[task_id_key].update((required if required else []) + (optional if optional else []))
    return task_id_dict


#
# rounds()
#

def rounds(hub_conn: HubConnection) -> set:
    """
    :return: a list of rounds in `hub_conn`'s `tasks`
    """
    the_rounds = set()
    for the_round in hub_conn.tasks['rounds']:
        round_id = the_round['round_id']
        if the_round['round_id_from_variable']:
            the_rounds.update(_task_id_to_values_round(the_round)[round_id])
        else:
            the_rounds.add(round_id)
    return the_rounds
