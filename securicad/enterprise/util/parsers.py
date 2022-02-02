# Copyright 2020-2022 Foreseeti AB <https://foreseeti.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import annotations

import io
import json
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from securicad.enterprise.client import Client
    from securicad.enterprise.models import ModelInfo
    from securicad.enterprise.projects import Project


def generate_aws_model(
    project: Project,
    name: str,
    cli_files: Optional[list[dict[str, Any]]] = None,
    vul_files: Optional[list[dict[str, Any]]] = None,
) -> ModelInfo:
    """Generates a model from AWS data.

    :param project: The :class:`Project` to add the generated model to.
    :param name: The name of the generated model.
    :param cli_files: (optional) A list of CLI data created with ``securicad-aws-collector``.
    :param vul_files: (optional) A list of vulnerability data.
    :return: A :class:`ModelInfo` object representing the generated model.
    """

    def get_file_io(dict_file: dict[str, Any]) -> io.BytesIO:
        file_str = json.dumps(dict_file, allow_nan=False, indent=2)
        file_bytes = file_str.encode("utf-8")
        return io.BytesIO(file_bytes)

    def get_file(
        sub_parser: str, name: str, dict_file: dict[str, Any]
    ) -> dict[str, Any]:
        return {
            "sub_parser": sub_parser,
            "name": name,
            "file": get_file_io(dict_file),
        }

    def get_files() -> list[dict[str, Any]]:
        files: list[dict[str, Any]] = []
        if cli_files is not None:
            for cli_file in cli_files:
                files.append(get_file("aws-cli-parser", "aws.json", cli_file))
        if vul_files is not None:
            for vul_file in vul_files:
                files.append(get_file("aws-vul-parser", "vul.json", vul_file))
        return files

    return project.generate_model(parser="aws-parser", name=name, files=get_files())


def generate_azure_model(
    project: Project,
    name: str,
    az_active_directory_files: Optional[list[dict[str, Any]]] = None,
    application_insight_files: Optional[list[dict[str, Any]]] = None,
) -> ModelInfo:
    """Generates a model from Azure data.

    :param project: The :class:`Project` to add the generated model to.
    :param name: The name of the generated model.
    :param az_active_directory_files: (optional) A list of azure environment data created with ``securicad-azure-collector``.
    :param application_insight_files: (optional) A list of application insights data created with ``securicad-azure-collector``.
    :return: A :class:`ModelInfo` object representing the generated model.
    """

    def get_file_io(dict_file: dict[str, Any]) -> io.BytesIO:
        file_str = json.dumps(dict_file, allow_nan=False, indent=2)
        file_bytes = file_str.encode("utf-8")
        return io.BytesIO(file_bytes)

    def get_file(
        sub_parser: str, name: str, dict_file: dict[str, Any]
    ) -> dict[str, Any]:
        return {
            "sub_parser": sub_parser,
            "name": name,
            "file": get_file_io(dict_file),
        }

    def get_files() -> list[dict[str, Any]]:
        files: list[dict[str, Any]] = []
        if az_active_directory_files is not None:
            for aad_file in az_active_directory_files:
                files.append(
                    get_file("azure-active-directory-parser", "azure_ad.json", aad_file)
                )
        if application_insight_files is not None:
            for insight_file in application_insight_files:
                files.append(
                    get_file(
                        "azure-application-insights-parser",
                        "insights.json",
                        insight_file,
                    )
                )
        return files

    return project.generate_model(parser="azure-parser", name=name, files=get_files())
