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

from securicad.enterprise.deprecation import deprecated

if TYPE_CHECKING:
    from securicad.enterprise.client import Client
    from securicad.enterprise.models import ModelInfo
    from securicad.enterprise.projects import Project


class Parsers:
    def __init__(self, client: Client) -> None:
        self.client = client

    def list_parsers(self) -> list[dict[str, Any]]:
        parsers: list[dict[str, Any]] = self.client._get("parsers")
        return parsers

    @deprecated("Use Util.generate_aws_model instead")
    def generate_aws_model(
        self,
        project: Project,
        name: str,
        cli_files: Optional[list[dict[str, Any]]] = None,
        vul_files: Optional[list[dict[str, Any]]] = None,
    ) -> ModelInfo:
        return self.client.util.generate_aws_model(
            project=project, name=name, cli_files=cli_files, vul_files=vul_files
        )

    @deprecated("Use Util.generate_azure_model instead")
    def generate_azure_model(
        self,
        project: Project,
        name: str,
        az_active_directory_files: Optional[list[dict[str, Any]]] = None,
        application_insight_files: Optional[list[dict[str, Any]]] = None,
    ) -> ModelInfo:
        return self.client.util.generate_azure_model(
            project=project,
            name=name,
            az_active_directory_files=az_active_directory_files,
            application_insight_files=application_insight_files,
        )
