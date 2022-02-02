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

import sys
import uuid
from pathlib import Path

import pytest
import utils

# isort: off

sys.path.append(str(Path(__file__).resolve().parent.parent))
from securicad.enterprise.exceptions import StatusCodeException

# isort: on
def test_list_create_scenario(project, model_info):
    assert project.list_scenarios() == []
    name = str(uuid.uuid4())
    description = str(uuid.uuid4())
    scenario = project.create_scenario(
        name=name,
        model_info=model_info,
        description=description,
        tunings=[],
    )
    fetched = project.list_scenarios()
    assert len(fetched) == 1, fetched
    fetched_scenario = fetched[0]
    assert scenario.name == name
    assert scenario.description == description
    assert fetched_scenario.name == name
    assert fetched_scenario.description == description


def test_get_scenario_by_tid(project, model_info):
    name = str(uuid.uuid4())
    description = str(uuid.uuid4())
    scenario = project.create_scenario(
        name=name,
        model_info=model_info,
        description=description,
        tunings=[],
    )
    fetched = project.get_scenario_by_tid(tid=scenario.tid)
    assert scenario.tid == fetched.tid
    assert fetched.name == name
    assert fetched.description == description


def test_get_scenario_by_name(project, model_info):
    name = str(uuid.uuid4())
    description = str(uuid.uuid4())
    scenario = project.create_scenario(
        name=name,
        model_info=model_info,
        description=description,
        tunings=[],
    )
    fetched = project.get_scenario_by_name(name=name)
    assert scenario.tid == fetched.tid
    assert fetched.name == name
    assert fetched.description == description


def test_scenario_update(project, model_info):
    name = str(uuid.uuid4())
    description = str(uuid.uuid4())
    scenario = project.create_scenario(
        name=name,
        model_info=model_info,
        description=description,
        tunings=[],
    )
    new_name = str(uuid.uuid4())
    new_description = str(uuid.uuid4())
    scenario.update(name=new_name, description=new_description)
    fetched = project.get_scenario_by_name(name=new_name)
    assert scenario.tid == fetched.tid
    assert fetched.name == new_name
    assert fetched.description == new_description


def test_delete_scenario(project, model_info):
    assert project.list_scenarios() == []
    name = str(uuid.uuid4())
    description = str(uuid.uuid4())
    scenario = project.create_scenario(
        name=name,
        model_info=model_info,
        description=description,
        tunings=[],
    )
    fetched = project.list_scenarios()
    fetched_scenario = fetched[0]
    scenario.delete()
    assert project.list_scenarios() == []
    with pytest.raises(StatusCodeException) as ex:
        fetched_scenario.delete()
    utils.assert_status_code_exception(
        exception=ex.value,
        status_code=404,
        method="DELETE",
        url=utils.get_url("scenarios"),
        data={"error": f"Scenario {fetched_scenario.tid} not found"},
    )


def test_scenario_list_simulations(project, model_info):
    assert project.list_scenarios() == []
    name = str(uuid.uuid4())
    description = str(uuid.uuid4())
    scenario = project.create_scenario(
        name=name,
        model_info=model_info,
        description=description,
        tunings=[],
    )
    fetched = scenario.list_simulations()
    assert len(fetched) == 1, fetched
    fetched_simulation = fetched[0]
    assert fetched_simulation.name == "Initial simulation"
