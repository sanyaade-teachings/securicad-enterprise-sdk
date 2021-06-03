# Copyright 2020-2021 Foreseeti AB <https://foreseeti.com>
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

import sys
import uuid
from pathlib import Path

import pytest

import utils

# isort: off

sys.path.append(str(Path(__file__).resolve().parent.parent))
from securicad.enterprise.exceptions import StatusCodeException

# isort: on


def test_list_simulations(client, scenario):
    fetched = client.simulations.list_simulations(scenario=scenario)
    assert len(fetched) == 1
    simulation = fetched[0]
    assert simulation.name == "Initial simulation"


def test_get_simulation_by_simid(client, scenario):
    simulation = scenario.list_simulations()[0]
    sim2 = client.simulations.get_simulation_by_simid(
        scenario=scenario, simid=simulation.simid
    )
    assert sim2.name == simulation.name
    assert sim2.simid == simulation.simid


def test_get_simulation_by_name(client, scenario):
    simulation = scenario.list_simulations()[0]
    sim2 = client.simulations.get_simulation_by_name(
        scenario=scenario, name=simulation.name
    )
    assert sim2.name == simulation.name
    assert sim2.simid == simulation.simid


def test_create_simulation(client, scenario, model):
    name = str(uuid.uuid4())
    simulation = client.simulations.create_simulation(
        scenario=scenario, name=name, model=model
    )
    assert simulation.name == name
    assert len(scenario.list_simulations()) == 2


def test_delete_simulation(client, scenario, model):
    assert len(scenario.list_simulations()) == 1
    name = str(uuid.uuid4())
    simulation = client.simulations.create_simulation(
        scenario=scenario, name=name, model=model
    )
    assert len(scenario.list_simulations()) == 2
    simulation.delete()
    assert len(scenario.list_simulations()) == 1


def test_simulation_get_results(client, scenario):
    sim = client.simulations.get_simulation_by_name(
        scenario=scenario, name="Initial simulation"
    )
    results = sim.get_results()
    assert results
