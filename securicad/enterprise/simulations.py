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

import time
from typing import TYPE_CHECKING, Any, Optional
from urllib.parse import urljoin

from securicad.model import es_serializer

from securicad.enterprise.deprecation import deprecated

if TYPE_CHECKING:
    from securicad.model import Model

    from securicad.enterprise.client import Client
    from securicad.enterprise.scenarios import Scenario
    from securicad.enterprise.tunings import Tuning


class Simulation:
    def __init__(
        self, client: Client, pid: str, tid: str, simid: str, name: str, progress: int
    ) -> None:
        self.client = client
        self.pid = pid
        self.tid = tid
        self.simid = simid
        self.name = name
        self.progress = progress
        self.result: Optional[dict[str, Any]] = None

    @staticmethod
    def from_dict(client: Client, dict_simulation: dict[str, Any]) -> Simulation:
        return Simulation(
            client=client,
            pid=dict_simulation["pid"],
            tid=str(dict_simulation["basemodel"]),
            simid=dict_simulation["mid"],
            name=dict_simulation["name"],
            progress=dict_simulation["progress"],
        )

    def __update_progress(self) -> None:
        dict_simulation = self.client.simulations._get_dict_simulation_by_simid(
            self.pid, self.simid
        )
        self.progress = dict_simulation["progress"]

    def __wait_for_results(self) -> None:
        if self.progress == 100:
            return
        while True:
            self.__update_progress()
            if self.progress < 0 or self.progress == 100:  # failed or finished
                break
            time.sleep(1)

    def delete(self) -> None:
        data: dict[str, Any] = {"pid": self.pid, "simids": [self.simid]}
        self.client._delete("simulations", data)

    def get_results(self) -> dict[str, Any]:
        self.__wait_for_results()
        data: dict[str, Any] = {"pid": self.pid, "simid": self.simid}
        result: dict[str, Any] = self.client._post("simulation/data", data)
        result["report_url"] = urljoin(
            self.client._base_url,
            f"project/{self.pid}/scenario/{self.tid}/report/{self.simid}",
        )
        self.result = result
        return result

    def get_raw_results(self) -> str:
        def cleanup(result: str) -> str:  # because of our not quite csv format
            lines = result.split("\n")
            if lines[2].startswith('"samplecount=') and lines[3].startswith('"build='):
                return "\n".join(lines[4:])
            return result

        self.__wait_for_results()
        data: dict[str, Any] = {"pid": self.pid, "simid": self.simid}
        result = self.client._post("simulation/raw_data", data)
        self.raw_result = cleanup(result["csv_data"])
        return self.raw_result

    def get_critical_paths(
        self, hvas: Optional[list[str]] = None
    ) -> dict[str, dict[str, Any]]:
        """
        Returns some or all critial paths for this simulation.

        Parameters:
            hvas: A list of strings on the form "<object_id>.<attackstep>", e.g. "1.Compromise".
                  If hvas is None all critical paths are returned.

        Returns:
            A dict of the form data["1.Compromise"] = { critical path }
        """
        if not self.result:
            self.get_results()

        if hvas is None:
            if not self.result:
                raise ValueError(
                    "No result stored, unable to retrieve high value assets, please specify"
                )
            hvas = []
            for risk in self.result["results"]["risks"]:
                hvas.append(risk["attackstep_id"])

        attackpaths: dict[str, dict[str, Any]] = {}
        for hva in hvas:
            data = {"simid": self.simid, "attackstep": hva}
            resp = self.client._post("simulation/attackpath", data)
            attackpaths[hva] = resp["data"]
        return attackpaths


class Simulations:
    def __init__(self, client: Client) -> None:
        self.client = client

    def _get_dict_simulation_by_simid(self, pid: str, simid: str) -> dict[str, Any]:
        data: dict[str, Any] = {"pid": pid, "simids": [simid]}
        dict_simulation: dict[str, Any] = self.client._post("simulations/data", data)[
            simid
        ]
        return dict_simulation

    def _list_simulations(self, scenario: Scenario) -> list[Simulation]:
        dict_scenario = self.client.scenarios._get_dict_scenario_by_tid(
            scenario.pid, scenario.tid
        )
        simulations: list[Simulation] = []
        for dict_simulation in dict_scenario["results"].values():
            simulations.append(
                Simulation.from_dict(
                    client=self.client, dict_simulation=dict_simulation
                )
            )
        return simulations

    @deprecated("Use Scenario.list_simulations()")
    def list_simulations(self, scenario: Scenario) -> list[Simulation]:
        return scenario.list_simulations()

    def _get_simulation_by_simid(self, scenario: Scenario, simid: str) -> Simulation:
        dict_simulation = self._get_dict_simulation_by_simid(scenario.pid, simid)
        return Simulation.from_dict(client=self.client, dict_simulation=dict_simulation)

    @deprecated("Use Scenario.get_simulation_by_simid()")
    def get_simulation_by_simid(self, scenario: Scenario, simid: str) -> Simulation:
        return scenario.get_simulation_by_simid(simid=simid)

    def _get_simulation_by_name(self, scenario: Scenario, name: str) -> Simulation:
        simulations = scenario.list_simulations()
        for simulation in simulations:
            if simulation.name == name:
                return simulation
        for simulation in simulations:
            if simulation.name.lower() == name.lower():
                return simulation
        raise ValueError(f"Invalid simulation {name}")

    @deprecated("Use Scenario.get_simulation_by_name()")
    def get_simulation_by_name(self, scenario: Scenario, name: str) -> Simulation:
        return scenario.get_simulation_by_name(name=name)

    def _create_simulation(
        self,
        scenario: Scenario,
        name: Optional[str] = None,
        model: Optional[Model] = None,
        tunings: Optional[list[Tuning]] = None,
        raw_tunings: Optional[list[dict[str, Any]]] = None,
        filter_results: bool = True,
    ) -> Simulation:
        data: dict[str, Any] = {
            "pid": scenario.pid,
            "tid": scenario.tid,
            "filter_results": filter_results,
        }
        if name is not None:
            data["name"] = name
        if model is not None:
            data["blob"] = es_serializer.serialize_model(model)
        if tunings is not None:
            data["cids"] = [t.tuning_id for t in tunings]
        if raw_tunings is not None:
            data["tunings"] = raw_tunings
        response = self.client._put("simulation", data)
        return self._get_simulation_by_simid(scenario, response["simid"])

    @deprecated("Use Scenario.create_simulation()")
    def create_simulation(
        self,
        scenario: Scenario,
        name: Optional[str] = None,
        model: Optional[Model] = None,
        tunings: Optional[list[Tuning]] = None,
        raw_tunings: Optional[list[dict[str, Any]]] = None,
        filter_results: bool = True,
    ) -> Simulation:
        return scenario.create_simulation(
            name=name,
            model=model,
            tunings=tunings,
            raw_tunings=raw_tunings,
            filter_results=filter_results,
        )
