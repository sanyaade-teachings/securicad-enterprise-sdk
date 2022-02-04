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

import json
from enum import Enum, auto
from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    from securicad.enterprise.client import Client


class RiskType(Enum):
    AVAILABILITY = auto()
    CONFIDENTIALITY = auto()
    INTEGRITY = auto()


class RiskTypeJsonEncoder(json.JSONEncoder):
    def default(self, o: Any) -> Any:
        if isinstance(o, RiskType):
            return o.name
        return super().default(o)


class Metadata:
    def __init__(self, client: Client) -> None:
        self.client = client

    def get_metadata(self) -> list[dict[str, Any]]:
        def parse_risktype(attackstep: dict[str, Any]) -> list[RiskType]:
            if "riskType" not in attackstep:
                return []
            retr: list[RiskType] = []
            if "Availability" in attackstep["riskType"]:
                retr.append(RiskType.AVAILABILITY)
            if "Confidentiality" in attackstep["riskType"]:
                retr.append(RiskType.CONFIDENTIALITY)
            if "Integrity" in attackstep["riskType"]:
                retr.append(RiskType.INTEGRITY)
            return retr

        metadata = self.client._get("metadata")
        metalist: list[dict[str, Any]] = []
        for asset, data in metadata["assets"].items():
            attacksteps: list[dict[str, Any]] = []
            for attackstep in data["attacksteps"]:
                attacksteps.append(
                    {
                        "name": attackstep["name"],
                        "description": attackstep["description"],
                        "risktype": parse_risktype(attackstep),
                        "metaInfo": attackstep.get("metaInfo", {}),
                    }
                )
            metalist.append(
                {
                    "name": asset,
                    "description": data["description"],
                    "attacksteps": attacksteps,
                    "metaInfo": data.get("metaInfo", {}),
                }
            )
        return sorted(metalist, key=lambda asset: cast(str, asset["name"]))
