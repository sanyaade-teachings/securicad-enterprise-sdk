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
from pathlib import Path
from typing import Any, Dict, Optional

# isort: off

sys.path.append(str(Path(__file__).resolve().parent.parent))
from securicad.enterprise.projects import Project
from securicad.enterprise.tunings import Tuning

# isort: on


def verify_tuning_response(
    tuning: Tuning,
    project: Project,
    tuning_type: str,
    op: str,
    filter_metaconcept: Optional[str] = None,
    filter_object_name: Optional[str] = None,
    filter_attackstep: Optional[str] = None,
    filter_defense: Optional[str] = None,
    filter_tags: Optional[Dict[str, Any]] = None,
    tags: Optional[Dict[str, Any]] = None,
    ttc: Optional[str] = None,
    probability: Optional[float] = None,
    consequence: Optional[int] = None,
):
    assert tuning.project.pid == project.pid
    assert tuning.tuning_type == tuning_type
    assert tuning.op == op
    assert tuning.filter_metaconcept == filter_metaconcept
    assert tuning.filter_object_name == filter_object_name
    assert tuning.filter_attackstep == filter_attackstep
    assert tuning.filter_defense == filter_defense
    assert tuning.filter_tags == filter_tags
    assert tuning.tags == tags
    assert tuning.ttc == ttc
    assert tuning.probability == probability
    assert tuning.consequence == consequence


# Attacker entry


def test_attacker_object_name(project):
    tuning = project.create_tuning(
        tuning_type="attacker",
        op="apply",
        filterdict={
            "attackstep": "HighPrivilegeAccess",
            "object_name": "i-1",
        },
    )
    verify_tuning_response(
        tuning,
        project=project,
        tuning_type="attacker",
        op="apply",
        filter_object_name="i-1",
        filter_attackstep="HighPrivilegeAccess",
    )


def test_attacker_object_tag(project):
    tuning = project.create_tuning(
        tuning_type="attacker",
        op="apply",
        filterdict={
            "attackstep": "HighPrivilegeAccess",
            "tags": {"env": "prod"},
        },
    )
    verify_tuning_response(
        tuning,
        project=project,
        tuning_type="attacker",
        op="apply",
        filter_attackstep="HighPrivilegeAccess",
        filter_tags={"env": "prod"},
    )


# TTC all attacksteps


def test_all_attackstep_ttc_all(project):
    tuning = project.create_tuning(
        tuning_type="ttc",
        op="apply",
        filterdict={},
        ttc="Exponential,3",
    )
    verify_tuning_response(
        tuning,
        project=project,
        tuning_type="ttc",
        op="apply",
        ttc="Exponential,3",
    )


def test_all_attackstep_ttc_all_tag(project):
    tuning = project.create_tuning(
        tuning_type="ttc",
        op="apply",
        filterdict={"tags": {"env": "prod"}},
        ttc="Exponential,3",
    )
    verify_tuning_response(
        tuning,
        project=project,
        tuning_type="ttc",
        op="apply",
        filter_tags={"env": "prod"},
        ttc="Exponential,3",
    )


def test_all_attackstep_ttc_class(project):
    tuning = project.create_tuning(
        tuning_type="ttc",
        op="apply",
        filterdict={"metaconcept": "EC2Instance"},
        ttc="Exponential,3",
    )
    verify_tuning_response(
        tuning,
        project=project,
        tuning_type="ttc",
        op="apply",
        filter_metaconcept="EC2Instance",
        ttc="Exponential,3",
    )


def test_all_attackstep_ttc_class_tag(project):
    tuning = project.create_tuning(
        tuning_type="ttc",
        op="apply",
        filterdict={
            "metaconcept": "EC2Instance",
            "tags": {"env": "prod"},
        },
        ttc="Exponential,3",
    )
    verify_tuning_response(
        tuning,
        project=project,
        tuning_type="ttc",
        op="apply",
        filter_metaconcept="EC2Instance",
        filter_tags={"env": "prod"},
        ttc="Exponential,3",
    )


def test_all_attackstep_ttc_object(project):
    tuning = project.create_tuning(
        tuning_type="ttc",
        op="apply",
        filterdict={
            "metaconcept": "EC2Instance",
            "object_name": "i-1",
        },
        ttc="Exponential,3",
    )
    verify_tuning_response(
        tuning,
        project=project,
        tuning_type="ttc",
        op="apply",
        filter_metaconcept="EC2Instance",
        filter_object_name="i-1",
        ttc="Exponential,3",
    )


# TTC one attackstep


def test_one_attackstep_ttc(project):
    tuning = project.create_tuning(
        tuning_type="ttc",
        op="apply",
        filterdict={"attackstep": "HighPrivilegeAccess"},
        ttc="Exponential,3",
    )
    verify_tuning_response(
        tuning,
        project=project,
        tuning_type="ttc",
        op="apply",
        filter_attackstep="HighPrivilegeAccess",
        ttc="Exponential,3",
    )


def test_one_attackstep_ttc_tag(project):
    tuning = project.create_tuning(
        tuning_type="ttc",
        op="apply",
        filterdict={
            "attackstep": "HighPrivilegeAccess",
            "tags": {"env": "prod"},
        },
        ttc="Exponential,3",
    )
    verify_tuning_response(
        tuning,
        project=project,
        tuning_type="ttc",
        op="apply",
        filter_attackstep="HighPrivilegeAccess",
        filter_tags={"env": "prod"},
        ttc="Exponential,3",
    )


def test_one_attackstep_ttc_class(project):
    tuning = project.create_tuning(
        tuning_type="ttc",
        op="apply",
        filterdict={
            "metaconcept": "EC2Instance",
            "attackstep": "HighPrivilegeAccess",
        },
        ttc="Exponential,3",
    )
    verify_tuning_response(
        tuning,
        project=project,
        tuning_type="ttc",
        op="apply",
        filter_metaconcept="EC2Instance",
        filter_attackstep="HighPrivilegeAccess",
        ttc="Exponential,3",
    )


def test_one_attackstep_ttc_class_tag(project):
    tuning = project.create_tuning(
        tuning_type="ttc",
        op="apply",
        filterdict={
            "metaconcept": "EC2Instance",
            "attackstep": "HighPrivilegeAccess",
            "tags": {"env": "prod"},
        },
        ttc="Exponential,3",
    )
    verify_tuning_response(
        tuning,
        project=project,
        tuning_type="ttc",
        op="apply",
        filter_metaconcept="EC2Instance",
        filter_attackstep="HighPrivilegeAccess",
        filter_tags={"env": "prod"},
        ttc="Exponential,3",
    )


def test_one_attackstep_ttc_object(project):
    tuning = project.create_tuning(
        tuning_type="ttc",
        op="apply",
        filterdict={
            "object_name": "i-1",
            "attackstep": "HighPrivilegeAccess",
        },
        ttc="Exponential,3",
    )
    verify_tuning_response(
        tuning,
        project=project,
        tuning_type="ttc",
        op="apply",
        filter_object_name="i-1",
        filter_attackstep="HighPrivilegeAccess",
        ttc="Exponential,3",
    )


def test_one_attackstep_ttc_class_object(project):
    tuning = project.create_tuning(
        tuning_type="ttc",
        op="apply",
        filterdict={
            "metaconcept": "EC2Instance",
            "object_name": "i-1",
            "attackstep": "HighPrivilegeAccess",
        },
        ttc="Exponential,3",
    )
    verify_tuning_response(
        tuning,
        project=project,
        tuning_type="ttc",
        op="apply",
        filter_metaconcept="EC2Instance",
        filter_object_name="i-1",
        filter_attackstep="HighPrivilegeAccess",
        ttc="Exponential,3",
    )


# Defense probability


def test_defense_probability_all(project):
    tuning = project.create_tuning(
        tuning_type="probability",
        op="apply",
        filterdict={},
        probability=0.5,
    )
    verify_tuning_response(
        tuning,
        project=project,
        tuning_type="probability",
        op="apply",
        probability=0.5,
    )


def test_defense_probability_all_tag(project):
    tuning = project.create_tuning(
        tuning_type="probability",
        op="apply",
        filterdict={"tags": {"env": "prod"}},
        probability=0.5,
    )
    verify_tuning_response(
        tuning,
        project=project,
        tuning_type="probability",
        op="apply",
        filter_tags={"env": "prod"},
        probability=0.5,
    )


def test_defense_probability_tag_one_defense(project):
    tuning = project.create_tuning(
        tuning_type="probability",
        op="apply",
        filterdict={
            "defense": "Patched",
            "tags": {"env": "prod"},
        },
        probability=0.5,
    )
    verify_tuning_response(
        tuning,
        project=project,
        tuning_type="probability",
        op="apply",
        filter_defense="Patched",
        filter_tags={"env": "prod"},
        probability=0.5,
    )


def test_defense_probability_class_all_defense(project):
    tuning = project.create_tuning(
        tuning_type="probability",
        op="apply",
        filterdict={"metaconcept": "EC2Instance"},
        probability=0.5,
    )
    verify_tuning_response(
        tuning,
        project=project,
        tuning_type="probability",
        op="apply",
        filter_metaconcept="EC2Instance",
        probability=0.5,
    )


def test_defense_probability_class_one_defense(project):
    tuning = project.create_tuning(
        tuning_type="probability",
        op="apply",
        filterdict={
            "metaconcept": "EC2Instance",
            "defense": "Patched",
        },
        probability=0.5,
    )
    verify_tuning_response(
        tuning,
        project=project,
        tuning_type="probability",
        op="apply",
        filter_metaconcept="EC2Instance",
        filter_defense="Patched",
        probability=0.5,
    )


def test_defense_probability_class_tag_all_defense(project):
    tuning = project.create_tuning(
        tuning_type="probability",
        op="apply",
        filterdict={
            "metaconcept": "EC2Instance",
            "tags": {"env": "prod"},
        },
        probability=0.5,
    )
    verify_tuning_response(
        tuning,
        project=project,
        tuning_type="probability",
        op="apply",
        filter_metaconcept="EC2Instance",
        filter_tags={"env": "prod"},
        probability=0.5,
    )


def test_defense_probability_class_tag_one_defense(project):
    tuning = project.create_tuning(
        tuning_type="probability",
        op="apply",
        filterdict={
            "metaconcept": "EC2Instance",
            "defense": "Patched",
            "tags": {"env": "prod"},
        },
        probability=0.5,
    )
    verify_tuning_response(
        tuning,
        project=project,
        tuning_type="probability",
        op="apply",
        filter_metaconcept="EC2Instance",
        filter_defense="Patched",
        filter_tags={"env": "prod"},
        probability=0.5,
    )


def test_defense_probability_object_all_defense(project):
    tuning = project.create_tuning(
        tuning_type="probability",
        op="apply",
        filterdict={"object_name": "i-1"},
        probability=0.5,
    )
    verify_tuning_response(
        tuning,
        project=project,
        tuning_type="probability",
        op="apply",
        filter_object_name="i-1",
        probability=0.5,
    )


def test_defense_probability_object_one_defense(project):
    tuning = project.create_tuning(
        tuning_type="probability",
        op="apply",
        filterdict={
            "defense": "Patched",
            "object_name": "i-1",
        },
        probability=0.5,
    )
    verify_tuning_response(
        tuning,
        project=project,
        tuning_type="probability",
        op="apply",
        filter_object_name="i-1",
        filter_defense="Patched",
        probability=0.5,
    )


def test_defense_probability_class_object_all_defense(project):
    tuning = project.create_tuning(
        tuning_type="probability",
        op="apply",
        filterdict={
            "metaconcept": "EC2Instance",
            "object_name": "i-1",
        },
        probability=0.5,
    )
    verify_tuning_response(
        tuning,
        project=project,
        tuning_type="probability",
        op="apply",
        filter_metaconcept="EC2Instance",
        filter_object_name="i-1",
        probability=0.5,
    )


def test_defense_probability_class_object_one_defense(project):
    tuning = project.create_tuning(
        tuning_type="probability",
        op="apply",
        filterdict={
            "metaconcept": "EC2Instance",
            "defense": "Patched",
            "object_name": "i-1",
        },
        probability=0.5,
    )
    verify_tuning_response(
        tuning,
        project=project,
        tuning_type="probability",
        op="apply",
        filter_metaconcept="EC2Instance",
        filter_object_name="i-1",
        filter_defense="Patched",
        probability=0.5,
    )


# Set tags


def test_tag_all(project):
    tuning = project.create_tuning(
        tuning_type="tag",
        op="apply",
        filterdict={},
        tags={"a": "b"},
    )
    verify_tuning_response(
        tuning,
        project=project,
        tuning_type="tag",
        op="apply",
        tags={"a": "b"},
    )


def test_tag_all_tag(project):
    tuning = project.create_tuning(
        tuning_type="tag",
        op="apply",
        filterdict={"tags": {"env": "prod"}},
        tags={"a": "b"},
    )
    verify_tuning_response(
        tuning,
        project=project,
        tuning_type="tag",
        op="apply",
        filter_tags={"env": "prod"},
        tags={"a": "b"},
    )


def test_tag_class(project):
    tuning = project.create_tuning(
        tuning_type="tag",
        op="apply",
        filterdict={"metaconcept": "EC2Instance"},
        tags={"a": "b"},
    )
    verify_tuning_response(
        tuning,
        project=project,
        tuning_type="tag",
        op="apply",
        filter_metaconcept="EC2Instance",
        tags={"a": "b"},
    )


def test_tag_class_tag(project):
    tuning = project.create_tuning(
        tuning_type="tag",
        op="apply",
        filterdict={
            "metaconcept": "EC2Instance",
            "tags": {"env": "prod"},
        },
        tags={"a": "b"},
    )
    verify_tuning_response(
        tuning,
        project=project,
        tuning_type="tag",
        op="apply",
        filter_metaconcept="EC2Instance",
        filter_tags={"env": "prod"},
        tags={"a": "b"},
    )


def test_tag_object(project):
    tuning = project.create_tuning(
        tuning_type="tag",
        op="apply",
        filterdict={"object_name": "i-1"},
        tags={"a": "b"},
    )
    verify_tuning_response(
        tuning,
        project=project,
        tuning_type="tag",
        op="apply",
        filter_object_name="i-1",
        tags={"a": "b"},
    )


def test_tag_object_class(project):
    tuning = project.create_tuning(
        tuning_type="tag",
        op="apply",
        filterdict={"metaconcept": "EC2Instance", "object_name": "i-1"},
        tags={"a": "b"},
    )
    verify_tuning_response(
        tuning,
        project=project,
        tuning_type="tag",
        op="apply",
        filter_metaconcept="EC2Instance",
        filter_object_name="i-1",
        tags={"a": "b"},
    )


def _get_filterdict_object(metaconcept, object_name, tags):
    filterdict = {}
    if metaconcept is not None:
        filterdict["metaconcept"] = metaconcept
    if object_name is not None:
        filterdict["object_name"] = object_name
    if tags is not None:
        filterdict["tags"] = tags
    return filterdict


def _get_filterdict_attackstep(metaconcept, object_name, attackstep, tags):
    filterdict = _get_filterdict_object(metaconcept, object_name, tags)
    if attackstep is not None:
        filterdict["attackstep"] = attackstep
    return filterdict


def _get_filterdict_defense(metaconcept, object_name, defense, tags):
    filterdict = _get_filterdict_object(metaconcept, object_name, tags)
    if defense is not None:
        filterdict["defense"] = defense
    return filterdict


def test_clear_attacker(project):
    for metaconcept in (None, "EC2Instance"):
        for object_name in (None, "i-1"):
            for attackstep in (None, "HighPrivilegeAccess"):
                for tags in (None, {"env": "prod"}):
                    tuning = project.create_tuning(
                        tuning_type="attacker",
                        op="clear",
                        filterdict=_get_filterdict_attackstep(
                            metaconcept, object_name, attackstep, tags
                        ),
                    )
                    verify_tuning_response(
                        tuning,
                        project=project,
                        tuning_type="attacker",
                        op="clear",
                        filter_metaconcept=metaconcept,
                        filter_object_name=object_name,
                        filter_attackstep=attackstep,
                        filter_tags=tags,
                    )


def test_clear_ttc(project):
    for metaconcept in (None, "EC2Instance"):
        for object_name in (None, "i-1"):
            for attackstep in (None, "HighPrivilegeAccess"):
                for tags in (None, {"env": "prod"}):
                    tuning = project.create_tuning(
                        tuning_type="ttc",
                        op="clear",
                        filterdict=_get_filterdict_attackstep(
                            metaconcept, object_name, attackstep, tags
                        ),
                    )
                    verify_tuning_response(
                        tuning,
                        project=project,
                        tuning_type="ttc",
                        op="clear",
                        filter_metaconcept=metaconcept,
                        filter_object_name=object_name,
                        filter_attackstep=attackstep,
                        filter_tags=tags,
                    )


def test_clear_probability(project):
    for metaconcept in (None, "EC2Instance"):
        for object_name in (None, "i-1"):
            for defense in (None, "Patched"):
                for tags in (None, {"env": "prod"}):
                    tuning = project.create_tuning(
                        tuning_type="probability",
                        op="clear",
                        filterdict=_get_filterdict_defense(
                            metaconcept, object_name, defense, tags
                        ),
                    )
                    verify_tuning_response(
                        tuning,
                        project=project,
                        tuning_type="probability",
                        op="clear",
                        filter_metaconcept=metaconcept,
                        filter_object_name=object_name,
                        filter_defense=defense,
                        filter_tags=tags,
                    )


def test_clear_consequence(project):
    for metaconcept in (None, "EC2Instance"):
        for object_name in (None, "i-1"):
            for attackstep in (None, "HighPrivilegeAccess"):
                for tags in (None, {"env": "prod"}):
                    tuning = project.create_tuning(
                        tuning_type="consequence",
                        op="clear",
                        filterdict=_get_filterdict_attackstep(
                            metaconcept, object_name, attackstep, tags
                        ),
                    )
                    verify_tuning_response(
                        tuning,
                        project=project,
                        tuning_type="consequence",
                        op="clear",
                        filter_metaconcept=metaconcept,
                        filter_object_name=object_name,
                        filter_attackstep=attackstep,
                        filter_tags=tags,
                    )


def test_clear_tag(project):
    for metaconcept in (None, "EC2Instance"):
        for object_name in (None, "i-1"):
            for tags in (None, {"env": "prod"}):
                tuning = project.create_tuning(
                    tuning_type="tag",
                    op="clear",
                    filterdict=_get_filterdict_object(metaconcept, object_name, tags),
                )
                verify_tuning_response(
                    tuning,
                    project=project,
                    tuning_type="tag",
                    op="clear",
                    filter_metaconcept=metaconcept,
                    filter_object_name=object_name,
                    filter_tags=tags,
                )


def test_delete(project):
    tuning = project.create_tuning(
        tuning_type="tag",
        op="apply",
        filterdict={"metaconcept": "EC2Instance", "object_name": "i-1"},
        tags={"a": "b"},
    )
    tuning.delete()
    assert project.list_tunings() == []


def test_list(project):
    assert project.list_tunings() == []
    tuning = project.create_tuning(
        tuning_type="tag",
        op="apply",
        filterdict={"metaconcept": "EC2Instance", "object_name": "i-1"},
        tags={"a": "b"},
    )
    curr_tunings = project.list_tunings()
    assert len(curr_tunings) == 1, curr_tunings
