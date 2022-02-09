# This file showcases how you can use securicad enterprise SDK to upload and simulate your azure environment
# by data files from the securicad-azure-collector or .sCAD models from azure-resource-parser
from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from securicad.enterprise.client import Client
from securicad.enterprise.models import ModelInfo
from securicad.enterprise.projects import Project
from securicad.enterprise.util import Util

# isort: off
sys.path.append(str(Path(__file__).resolve().parent.parent))
from auth import setup
from utils import init_logging

# isort: on

log = logging.getLogger("azure-upload")


def upload_scad(project: Project, scad: Path) -> None:
    """Uploads an .scad file to enterprise to a specified project.
    \n Keyword arguments:
    \t project - The enterprise project object to upload the file to. \n
    \t scad - The full path to the .sCAD file to be uploaded.
    """
    try:
        filename = scad.as_posix().split("/")[-1]
    except IndexError:
        filename = datetime.now().strftime("%D-%T") + ".sCAD"
    with open(file=scad, mode="rb") as file_io:
        log.info(f"Uploading model {filename}")
        res: ModelInfo = project.upload_scad_model(filename=filename, file_io=file_io)
        if not res.is_valid:  # type: ignore
            sys.exit(
                f"Uploaded model {res.name} is not valid, reasons: \n {res.validation_issues}"  # type: ignore
            )
    log.info(f"Uploaded model {res.name} with mid: {res.mid}")  # type: ignore


def upload_json(
    project: Project, es_client: Client, environment: Path, app_insights: Optional[Path]
) -> None:
    """Uploads the active_directory.json and application_insights.json file provided by the collector to enterprise
    and parses a model to the specified project. \n
    Keyword arguments: \n
    \tproject - The enterprise project object to upload the file to. \n
    \tes_client - A Client object, connected to an enterprise instance. \n
    \tenvironment - The full path to the active_directory.json file to be uploaded. \n
    \tapp_insights - (Optional) The full path to the application_insights.json file to be uploaded. \n
    \t
    """
    ad_filename = environment.as_posix().split("/")[-1]
    insights_filename = app_insights.as_posix().split("/")[-1] if app_insights else ""
    active_directory_data: List[Dict[str, Any]] = []
    application_insights_data: List[Dict[str, Any]] = []
    try:
        with open(str(environment), mode="rb") as f:
            active_directory_data.append(json.load(f))
    except FileNotFoundError as e:
        log.error(f"{e}")
        sys.exit(f"Cannot parse without a valid active_directory.json. Exiting")
    if app_insights:
        try:
            with open(str(app_insights), mode="rb") as f:
                application_insights_data.append(json.load(f))
        except FileNotFoundError as e:
            log.error(f"{e}")
    # Make the data enterprise compatible
    if application_insights_data:
        log.info(
            f"Generating model from environment file {ad_filename} and application insights file {insights_filename}"
        )
    else:
        log.info(f"Generating model from {ad_filename}")
    res: Util = es_client.util.generate_azure_model(  # type: ignore
        project=project,
        name=ad_filename,
        az_active_directory_files=active_directory_data,
        application_insight_files=application_insights_data,
    )
    if not res.is_valid:  # type: ignore
        sys.exit(
            f"Uploaded model {res.name} is not valid, reasons: \n {res.validation_issues}"  # type: ignore
        )

    log.info(f"Uploaded model {res.name} with mid: {res.mid}")  # type: ignore


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-s",
        "--scad",
        action="store",
        default=None,
        type=Path,
        required=False,
        help="securicad .scad model file path",
        metavar="FILE",
        dest="scad_file",
    )
    parser.add_argument(
        "-e",
        "--environment",
        action="store",
        default=None,
        type=Path,
        required=False,
        help="active_directory.json file path",
        metavar="FILE",
        dest="ad_file",
    )
    parser.add_argument(
        "-i",
        "--insights",
        action="store",
        default=None,
        type=Path,
        required=False,
        help="application_insights.json file path",
        metavar="FILE",
        dest="ai_file",
    )
    parser.add_argument(
        "-p",
        "--project",
        action="store",
        default="Default",
        type=str,
        required=False,
        help="Project name that the model will be uploaded to. Will use project Default if not provided",
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
    project = args.project if args.project else "Default"
    es_client = setup()

    try:
        log.info(f"Entering project {project}")
        project_obj: Project = es_client.projects.get_project_by_name(project)
    except ValueError as e:
        log.error(f"invalid project name {project}")
        sys.exit(e)

    if args.scad_file:
        # try:
        scad = Path(args.scad_file)
        if scad.suffix != ".sCAD":
            log.error(
                f"Invalid file type {args.scad_file}. input file needs to be a .sCAD file"
            )
            return
        upload_scad(
            project=project_obj,
            scad=args.scad_file,
        )
    elif args.ad_file:
        upload_json(
            project=project_obj,
            es_client=es_client,
            environment=args.ad_file,
            app_insights=args.ai_file,
        )
    else:
        sys.exit(
            "Need to provide either a .sCAD file or an active_directory.json (together with optional application_insights.json file). Run the program with -h for more info"
        )


if __name__ == "__main__":
    main()
