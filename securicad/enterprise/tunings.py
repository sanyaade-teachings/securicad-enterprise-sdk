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

if TYPE_CHECKING:
    from securicad.enterprise.client import Client
    from securicad.enterprise.projects import Project


class Tuning:
    def __init__(
        self,
        client: Client,
        project: Project,
        tuning_id: str,
        tuning_type: str,
        op: str,
        filter_metaconcept: Optional[str] = None,
        filter_object_name: Optional[str] = None,
        filter_attackstep: Optional[str] = None,
        filter_defense: Optional[str] = None,
        filter_tags: Optional[dict[str, Any]] = None,
        tags: Optional[dict[str, Any]] = None,
        ttc: Optional[str] = None,
        probability: Optional[float] = None,
        consequence: Optional[int] = None,
    ) -> None:
        self.client = client
        self.project = project
        self.tuning_id = tuning_id
        self.tuning_type = tuning_type
        self.op = op
        self.filter_metaconcept = filter_metaconcept
        self.filter_object_name = filter_object_name
        self.filter_attackstep = filter_attackstep
        self.filter_defense = filter_defense
        self.filter_tags = filter_tags
        self.tags = tags
        self.ttc = ttc
        self.probability = probability
        self.consequence = consequence

    @staticmethod
    def from_dict(
        client: Client, project: Project, dict_tuning: dict[str, Any]
    ) -> Tuning:
        return Tuning(
            client=client,
            project=project,
            tuning_id=dict_tuning["cid"],
            tuning_type=dict_tuning["config"]["type"],
            op=dict_tuning["config"]["op"],
            filter_metaconcept=dict_tuning["config"]["filter"].get("metaconcept"),
            filter_object_name=dict_tuning["config"]["filter"].get("object_name"),
            filter_attackstep=dict_tuning["config"]["filter"].get("attackstep"),
            filter_defense=dict_tuning["config"]["filter"].get("defense"),
            filter_tags=dict_tuning["config"]["filter"].get("tags"),
            tags=dict_tuning["config"].get("tags"),
            ttc=dict_tuning["config"].get("ttc"),
            probability=dict_tuning["config"].get("probability"),
            consequence=dict_tuning["config"].get("consequence"),
        )

    def delete(self) -> None:
        self.client._delete(
            "tunings", {"pid": self.project.pid, "cids": [self.tuning_id]}
        )


class Tunings:
    def __init__(self, client: Client) -> None:
        self.client = client

    @deprecated("Use Project.list_tunings()")
    def list_tunings(self, project: Project) -> list[Tuning]:
        return project.list_tunings()

    def _list_tunings(self, project: Project) -> list[Tuning]:
        dict_tunings = self.client._post("tunings", {"pid": project.pid})
        retr: list[Tuning] = []
        for tuning_id, dict_tuning in dict_tunings["configs"].items():
            retr.append(
                Tuning.from_dict(
                    self.client,
                    project,
                    {"pid": project.pid, "cid": tuning_id, "config": dict_tuning},
                )
            )
        return retr

    @deprecated("Use Project.create_tuning()")
    def create_tuning(
        self,
        project: Project,
        tuning_type: str,
        filterdict: dict[str, Any],
        op: str = "apply",
        tags: Optional[dict[str, Any]] = None,
        ttc: Optional[str] = None,
        probability: Optional[float] = None,
        consequence: Optional[int] = None,
    ) -> Tuning:
        return project.create_tuning(
            tuning_type=tuning_type,
            filterdict=filterdict,
            op=op,
            tags=tags,
            ttc=ttc,
            probability=probability,
            consequence=consequence,
        )

    def _create_tuning(
        self,
        project: Project,
        tuning_type: str,
        filterdict: dict[str, Any],
        op: str = "apply",
        tags: Optional[dict[str, Any]] = None,
        ttc: Optional[str] = None,
        probability: Optional[float] = None,
        consequence: Optional[int] = None,
    ) -> Tuning:
        def get_tuning() -> dict[str, Any]:
            tuning: dict[str, Any] = {
                "type": tuning_type,
                "op": op,
                "filter": filterdict,
            }
            if tuning_type == "tag" and op == "apply":
                tuning["tags"] = tags
            elif tuning_type == "ttc" and op == "apply":
                tuning["ttc"] = ttc
            elif tuning_type == "probability" and op == "apply":
                tuning["probability"] = probability
            elif tuning_type == "consequence" and op == "apply":
                tuning["consequence"] = consequence
            return tuning

        if tuning_type not in ["attacker", "tag", "ttc", "probability", "consequence"]:
            raise ValueError(f"Unknown tuning_type {tuning_type}")
        if op not in ["apply", "clear"]:
            raise ValueError(f"Unknown op {op}")
        data = {"pid": project.pid, "tunings": [get_tuning()]}
        dict_tuning = self.client._put("tunings", data)[0]
        return Tuning.from_dict(
            client=self.client, project=project, dict_tuning=dict_tuning
        )
