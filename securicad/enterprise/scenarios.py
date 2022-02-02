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

from typing import TYPE_CHECKING, Any, Optional

from securicad.enterprise.deprecation import deprecated
from securicad.enterprise.simulations import Simulation

if TYPE_CHECKING:
    from securicad.model import Model

    from securicad.enterprise.client import Client
    from securicad.enterprise.models import ModelInfo
    from securicad.enterprise.projects import Project
    from securicad.enterprise.tunings import Tuning


class Scenario:
    def __init__(
        self, client: Client, pid: str, tid: str, name: str, description: str
    ) -> None:
        self.client = client
        self.pid = pid
        self.tid = tid
        self.name = name
        self.description = description

    @staticmethod
    def from_dict(client: Client, dict_scenario: dict[str, Any]) -> Scenario:
        return Scenario(
            client=client,
            pid=dict_scenario["pid"],
            tid=dict_scenario["tid"],
            name=dict_scenario["name"],
            description=dict_scenario["description"],
        )

    def update(
        self, *, name: Optional[str] = None, description: Optional[str] = None
    ) -> None:
        data: dict[str, Any] = {
            "pid": self.pid,
            "tid": self.tid,
            "name": self.name if name is None else name,
            "description": self.description if description is None else description,
        }
        response = self.client._post("scenario", data)
        self.name = response["name"]
        self.description = response["description"]

    def delete(self) -> None:
        data: dict[str, Any] = {"pid": self.pid, "tids": [self.tid]}
        self.client._delete("scenarios", data)

    def list_simulations(self) -> list[Simulation]:
        return self.client.simulations._list_simulations(scenario=self)

    def get_simulation_by_simid(self, simid: str) -> Simulation:
        return self.client.simulations._get_simulation_by_simid(
            scenario=self, simid=simid
        )

    def get_simulation_by_name(self, name: str) -> Simulation:
        return self.client.simulations._get_simulation_by_name(scenario=self, name=name)

    def create_simulation(
        self,
        name: Optional[str] = None,
        model: Optional[Model] = None,
        tunings: Optional[list[Tuning]] = None,
        raw_tunings: Optional[list[dict[str, Any]]] = None,
        filter_results: bool = True,
    ) -> Simulation:
        return self.client.simulations._create_simulation(
            scenario=self,
            name=name,
            model=model,
            tunings=tunings,
            raw_tunings=raw_tunings,
            filter_results=filter_results,
        )


class Scenarios:
    def __init__(self, client: Client) -> None:
        self.client = client

    def _list_dict_scenarios(self, pid: str) -> dict[str, dict[str, Any]]:
        dict_scenarios: dict[str, dict[str, Any]] = self.client._post(
            "scenarios", {"pid": pid}
        )
        return dict_scenarios

    def _get_dict_scenario_by_tid(self, pid: str, tid: str) -> dict[str, Any]:
        data: dict[str, Any] = {"pid": pid, "tid": tid}
        dict_scenario: dict[str, Any] = self.client._post("scenario/data", data)
        return dict_scenario

    @deprecated("Use Project.list_scenarios()")
    def list_scenarios(self, project: Project) -> list[Scenario]:
        return project.list_scenarios()

    def _list_scenarios(self, project: Project) -> list[Scenario]:
        dict_scenarios = self._list_dict_scenarios(project.pid)
        scenarios: list[Scenario] = []
        for dict_scenario in dict_scenarios.values():
            scenarios.append(
                Scenario.from_dict(client=self.client, dict_scenario=dict_scenario)
            )
        return scenarios

    @deprecated("Use Project.get_scenario_by_tid()")
    def get_scenario_by_tid(self, project: Project, tid: str) -> Scenario:
        return project.get_scenario_by_tid(tid=tid)

    def _get_scenario_by_tid(self, project: Project, tid: str) -> Scenario:
        dict_scenario = self._get_dict_scenario_by_tid(project.pid, tid)
        return Scenario.from_dict(client=self.client, dict_scenario=dict_scenario)

    @deprecated("Use Project.get_scenario_by_name()")
    def get_scenario_by_name(self, project: Project, name: str) -> Scenario:
        return project.get_scenario_by_name(name=name)

    def _get_scenario_by_name(self, project: Project, name: str) -> Scenario:
        scenarios = project.list_scenarios()
        for scenario in scenarios:
            if scenario.name == name:
                return scenario
        for scenario in scenarios:
            if scenario.name.lower() == name.lower():
                return scenario
        raise ValueError(f"Invalid scenario {name}")

    @deprecated("Use Project.create_scenario()")
    def create_scenario(
        self,
        project: Project,
        model_info: ModelInfo,
        name: str,
        description: Optional[str] = None,
        tunings: Optional[list[Tuning]] = None,
        raw_tunings: Optional[list[dict[str, Any]]] = None,
        filter_results: bool = True,
    ) -> Scenario:
        return project.create_scenario(
            model_info=model_info,
            name=name,
            description=description,
            tunings=tunings,
            raw_tunings=raw_tunings,
            filter_results=filter_results,
        )

    def _create_scenario(
        self,
        project: Project,
        model_info: ModelInfo,
        name: str,
        description: Optional[str] = None,
        tunings: Optional[list[Tuning]] = None,
        raw_tunings: Optional[list[dict[str, Any]]] = None,
        filter_results: bool = True,
    ) -> Scenario:
        data: dict[str, Any] = {
            "pid": project.pid,
            "mid": model_info.mid,
            "name": name,
            "description": "" if description is None else description,
            "filter_results": filter_results,
        }
        if tunings is not None:
            data["cids"] = [t.tuning_id for t in tunings]
        if raw_tunings is not None:
            data["tunings"] = raw_tunings
        dict_scenario = self.client._put("scenario", data)
        return Scenario.from_dict(client=self.client, dict_scenario=dict_scenario)
