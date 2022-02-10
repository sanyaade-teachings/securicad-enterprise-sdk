# This file showcases how you can use securicad enterprise SDK to initialize scenarios and segmentate them based on model object tags:
# C:<integer> I:<integer> A:<integer> scenario_groups["group1", ... , "groupn"]
# Begin by configuring your enterprise credentials at /examples/conf.ini
from __future__ import annotations

import argparse
import logging
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional

import scenario_parser
from auth import setup
from utils import init_logging

from securicad.enterprise.client import Client
from securicad.enterprise.metadata import RiskType
from securicad.enterprise.models import ModelInfo
from securicad.enterprise.projects import Project

if TYPE_CHECKING:
    from securicad.model import Model
    from securicad.model.object import Object


log = logging.getLogger("scenario-scheduler")


def apply_cia_tunings(es_client: Client, project: Project, model_info: ModelInfo):
    """Uses the CIA tags of the model's objects and sets the corresponding language attack steps as high value assets
    \n Keyword arguments:
    \t es_client - An enterprise client
    \t project - The project object where the model lies
    \t model_info - A ModelInfo instance containing the model info
    """
    groups: Dict[str, List[Object]] = defaultdict(list)
    obj: Object
    log.info("Segmentating scenario groups")
    for obj in model_info.get_model().objects():
        scenario_groups: List[str] = obj.meta["tags"].get("scenarioGroups", [])  # type: ignore
        for group in scenario_groups:
            groups[group].append(obj)
    language_meta = es_client.metadata.get_metadata()
    log.info("creating tunings")
    for group, objects in groups.items():
        tunings = []
        for metalist in language_meta:
            applies_to: List[Object] = [
                x for x in objects if x.asset_type == metalist["name"]
            ]
            if not applies_to:
                continue
            attackstep: Dict[str, Any]
            for attackstep in metalist["attacksteps"]:
                risk_types: List[RiskType] = attackstep["risktype"]
                is_confidentiality = (
                    True if RiskType.CONFIDENTIALITY in risk_types else False
                )
                is_integrity = True if RiskType.INTEGRITY in risk_types else False
                is_availability = True if RiskType.AVAILABILITY in risk_types else False
                if not risk_types:
                    continue
                for obj in applies_to:
                    c_val: int = int(obj.meta["tags"].get("C", 0))  # type: ignore
                    i_val: int = int(obj.meta["tags"].get("I", 0))  # type: ignore
                    a_val: int = int(obj.meta["tags"].get("A", 0))  # type: ignore
                    tuning = {
                        "tuning_type": "consequence",
                        "op": "apply",
                        "filterdict": {
                            "metaconcept": f"{metalist['name']}",
                            "attackstep": f"{attackstep['name']}",
                            "object_name": f"{obj.name}",  # type: ignore
                        },
                        "consequence": max(
                            c_val if is_confidentiality else 0,
                            i_val if is_integrity else 0,
                            a_val if is_availability else 0,
                        ),
                    }
                    tuning_obj = project.create_tuning(**tuning)  # type: ignore
                    tunings.append(tuning_obj)  # type: ignore
        scenario_name = f"{group}-CIA-tags"
        simulation_name = datetime.now().strftime("T%H:%M:%S")
        model: Model = model_info.get_model()
        try:
            log.info(f"Accessing scenario {scenario_name}")
            scenario = project.get_scenario_by_name(name=scenario_name)
            log.info(f"Starting simulation {simulation_name}")
            scenario.create_simulation(
                name=simulation_name, model=model, tunings=tunings
            )
        except ValueError:
            log.info(
                f"Creating scenario {scenario_name} and starting Initial Simulation"
            )
            scenario = es_client.scenarios.create_scenario(
                project=project,
                model_info=model_info,
                name=scenario_name,
                tunings=tunings,
            )


def apply_tunings_file(tunings_file: Path, project: Project, model_info: ModelInfo):
    """Applies a tunings file on the entire model (no group segmentation)
    \n Keyword arugments:
    \t tunings_file - a Path object pointing to the tunings file
    \t project - The project object where the model lies
    \t model_info - A ModelInfo instance containing the model info
    """
    log.info("validating tunings file")
    with open(tunings_file, mode="rb") as f:
        data = f.read()
    tunings = scenario_parser.parse(data)
    log.info(f"Applying scenarios based on tunings file")
    for entry in tunings["scenarios"]:
        scenario_name = entry["name"]
        tuning_objects = entry["tunings"]
        tunings = []
        for tuning in tuning_objects:
            try:
                tuning_obj = project.create_tuning(**tuning)
                tunings.append(tuning_obj)  # type: ignore
            except (TypeError, ValueError) as e:
                log.error(f"{tuning} is not a valid tuning. {e}")
        simulation_name = datetime.now().strftime("T%H:%M:%S")
        model: Model = model_info.get_model()
        try:
            log.info(f"Accessing scenario {scenario_name}")
            scenario = project.get_scenario_by_name(name=scenario_name)
            log.info(f"Starting simulation {simulation_name}")
            scenario.create_simulation(
                name=simulation_name, model=model, tunings=tunings
            )
        except ValueError:
            log.info(
                f"Creating scenario {scenario_name} and starting Initial Simulation"
            )
            scenario = project.create_scenario(
                model_info=model_info, name=scenario_name, tunings=tunings
            )


def get_model(model: str, project: Project, mid: Optional[str]) -> Optional[ModelInfo]:
    """Gets a Model object from the enterprise client
    \n Keyword arguments:
    \t es_client - An enterprise Client instance
    \t model - the name of the model
    \t project - A project instance where the model should reside
    \n Returns:
    \t A ModelInfo object instance or None
    """
    if mid:
        return project.get_model_by_mid(mid=mid)
    model_infos = [x for x in project.list_models() if x.name == model]  # type: ignore
    return model_infos[-1] if model_infos else None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-m",
        "--model",
        action="store",
        default=None,
        type=str,
        required=False,
        help="securicad model name",
        metavar="STRING",
        dest="model",
    )
    parser.add_argument(
        "--mid",
        action="store",
        default=None,
        type=str,
        required=False,
        help="securicad model mid, used for faster lookup of model",
        metavar="STRING",
        dest="mid",
    )
    parser.add_argument(
        "-t",
        "--tunings",
        action="store",
        default=None,
        type=Path,
        required=False,
        help="json file containing tuning objects",
        metavar="FILE",
        dest="tunings",
    )
    parser.add_argument(
        "-p",
        "--project",
        action="store",
        default=None,
        type=str,
        required=True,
        help="Project name that the model will be uploaded to. Will use date as default if not provided",
        metavar="STRING",
        dest="project",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store",
        required=False,
        type=bool,
        default=True,
        help="Detailed logging messages",
        dest="verbose",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store",
        required=False,
        type=bool,
        default=False,
        help="Only critical output messages",
        dest="quiet",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    verbose = args.verbose
    quiet = args.quiet
    init_logging(log=log, quiet=quiet, verbose=verbose)
    project = args.project
    model_name = args.model
    mid = args.mid
    if not any([model_name, mid]):
        sys.exit(
            "Need either a model name or mid. Run program with --help for more information."
        )

    es_client = setup()
    try:
        log.info(f"Entering project {project}")
        project_obj: Project = es_client.projects.get_project_by_name(project)
    except ValueError as e:
        log.error(f"invalid project name {project}")
        sys.exit(e)

    log.info(f"Getting model {model_name if model_name else mid}")
    model = get_model(model=model_name, project=project_obj, mid=mid)
    if not model:
        log.error(f"Couldn't find a model with name {model_name} in project {project}")
        sys.exit()

    apply_cia_tunings(es_client=es_client, project=project_obj, model_info=model)
    if args.tunings:
        apply_tunings_file(
            tunings_file=args.tunings,
            project=project_obj,
            model_info=model,
        )


if __name__ == "__main__":
    main()
