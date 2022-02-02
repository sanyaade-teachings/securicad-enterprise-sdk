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

from enum import IntEnum, unique
from typing import TYPE_CHECKING, Any, BinaryIO, Optional

if TYPE_CHECKING:
    from securicad.model import Model

    from securicad.enterprise.client import Client
    from securicad.enterprise.models import ModelInfo
    from securicad.enterprise.organizations import Organization
    from securicad.enterprise.scenarios import Scenario
    from securicad.enterprise.tunings import Tuning
    from securicad.enterprise.users import User


@unique
class AccessLevel(IntEnum):
    GUEST = 100
    USER = 180
    OWNER = 250
    ADMIN = 255

    @staticmethod
    def from_int(level: int) -> AccessLevel:
        for access_level in AccessLevel:
            if level == access_level:
                return access_level
        raise ValueError(f"Invalid access level {level}")


class Project:
    def __init__(
        self,
        client: Client,
        pid: str,
        name: str,
        description: str,
        access_level: AccessLevel,
    ) -> None:
        self.client = client
        self.pid = pid
        self.name = name
        self.description = description
        self.access_level = access_level

    @staticmethod
    def from_dict(client: Client, dict_project: dict[str, Any]) -> Project:
        return Project(
            client=client,
            pid=dict_project["pid"],
            name=dict_project["name"],
            description=dict_project["description"],
            access_level=AccessLevel.from_int(dict_project["accesslevel"]),
        )

    def update(
        self, *, name: Optional[str] = None, description: Optional[str] = None
    ) -> None:
        data: dict[str, Any] = {
            "pid": self.pid,
            "name": self.name if name is None else name,
            "description": self.description if description is None else description,
        }
        dict_project = self.client._post("project", data)
        self.name = dict_project["name"]
        self.description = dict_project["description"]

    def delete(self) -> None:
        self.client._delete("project", {"pid": self.pid})

    def list_users(self) -> list[User]:
        dict_project = self.client.projects._get_dict_project_by_pid(self.pid)
        users: list[User] = []
        for dict_user in dict_project["users"]:
            users.append(self.client.users.get_user_by_uid(dict_user["uid"]))
        return users

    def add_user(self, user: User, access_level: Optional[AccessLevel] = None) -> None:
        data: dict[str, Any] = {"pid": self.pid, "uid": user.uid}
        if access_level is not None:
            data["accesslevel"] = int(access_level)
        self.client._put("project/user", data)

    def remove_user(self, user: User) -> None:
        data: dict[str, Any] = {"pid": self.pid, "uid": user.uid}
        self.client._delete("project/user", data)

    def get_access_level(self, user: User) -> Optional[AccessLevel]:
        dict_project = self.client.projects._get_dict_project_by_pid(self.pid)
        for dict_user in dict_project["users"]:
            if dict_user["uid"] == user.uid:
                return AccessLevel.from_int(dict_user["accesslevel"])
        return None

    def set_access_level(self, user: User, access_level: AccessLevel) -> None:
        data: dict[str, Any] = {
            "pid": self.pid,
            "uid": user.uid,
            "accesslevel": int(access_level),
        }
        self.client._post("project/user", data)

    ##
    # Models

    def list_models(self) -> list[ModelInfo]:
        return self.client.models._list_models(project=self)

    def get_model_by_mid(self, mid: str) -> ModelInfo:
        return self.client.models._get_model_by_mid(project=self, mid=mid)

    def get_model_by_name(self, name: str) -> ModelInfo:
        return self.client.models._get_model_by_name(project=self, name=name)

    def import_models(self, model_infos: list[ModelInfo]) -> None:
        mids = [model_info.mid for model_info in model_infos]
        data: dict[str, Any] = {"pid": self.pid, "mids": mids}
        self.client._post("models/import", data)

    def save_as(self, model: Model, name: str) -> ModelInfo:
        return self.client.models._save_as(project=self, model=model, name=name)

    def upload_scad_model(
        self, filename: str, file_io: BinaryIO, description: Optional[str] = None
    ) -> ModelInfo:
        return self.client.models._upload_scad_model(
            project=self, filename=filename, file_io=file_io, description=description
        )

    def generate_model(
        self, parser: str, name: str, files: list[dict[str, Any]]
    ) -> ModelInfo:
        return self.client.models._generate_model(
            project=self, parser=parser, name=name, files=files
        )

    ##
    # Scenarios

    def list_scenarios(self) -> list[Scenario]:
        return self.client.scenarios._list_scenarios(project=self)

    def get_scenario_by_tid(self, tid: str) -> Scenario:
        return self.client.scenarios._get_scenario_by_tid(project=self, tid=tid)

    def get_scenario_by_name(self, name: str) -> Scenario:
        return self.client.scenarios._get_scenario_by_name(project=self, name=name)

    def create_scenario(
        self,
        model_info: ModelInfo,
        name: str,
        description: Optional[str] = None,
        tunings: Optional[list[Tuning]] = None,
        raw_tunings: Optional[list[dict[str, Any]]] = None,
        filter_results: bool = True,
    ) -> Scenario:
        return self.client.scenarios._create_scenario(
            project=self,
            model_info=model_info,
            name=name,
            description=description,
            tunings=tunings,
            raw_tunings=raw_tunings,
            filter_results=filter_results,
        )

    ##
    # Tunings

    def list_tunings(self) -> list[Tuning]:
        return self.client.tunings._list_tunings(project=self)

    def create_tuning(
        self,
        tuning_type: str,
        filterdict: dict[str, Any],
        op: str = "apply",
        tags: Optional[dict[str, Any]] = None,
        ttc: Optional[str] = None,
        probability: Optional[float] = None,
        consequence: Optional[int] = None,
    ) -> Tuning:
        return self.client.tunings._create_tuning(
            project=self,
            tuning_type=tuning_type,
            filterdict=filterdict,
            op=op,
            tags=tags,
            ttc=ttc,
            probability=probability,
            consequence=consequence,
        )


class Projects:
    def __init__(self, client: Client) -> None:
        self.client = client

    def _list_dict_projects(self) -> list[dict[str, Any]]:
        dict_projects: list[dict[str, Any]] = self.client._post("projects")
        return dict_projects

    def _get_dict_project_by_pid(self, pid: str) -> dict[str, Any]:
        dict_project: dict[str, Any] = self.client._post("project/data", {"pid": pid})
        return dict_project

    def list_projects(self) -> list[Project]:
        dict_projects = self._list_dict_projects()
        projects: list[Project] = []
        for dict_project in dict_projects:
            projects.append(
                Project.from_dict(client=self.client, dict_project=dict_project)
            )
        return projects

    def get_project_by_pid(self, pid: str) -> Project:
        dict_project = self._get_dict_project_by_pid(pid)
        return Project.from_dict(client=self.client, dict_project=dict_project)

    def get_project_by_name(self, name: str) -> Project:
        projects = self.list_projects()
        for project in projects:
            if project.name == name:
                return project
        for project in projects:
            if project.name.lower() == name.lower():
                return project
        raise ValueError(f"Invalid project {name}")

    def create_project(
        self,
        name: str,
        description: Optional[str] = None,
        organization: Optional[Organization] = None,
    ) -> Project:
        data: dict[str, Any] = {
            "name": name,
            "description": "" if description is None else description,
        }
        if organization is not None:
            data["organization"] = organization.tag
        dict_project = self.client._put("project", data)
        return self.get_project_by_pid(dict_project["pid"])
