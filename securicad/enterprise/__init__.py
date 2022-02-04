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

from typing import Any

from securicad.enterprise.client import Client as Client
from securicad.enterprise.models import ModelInfo as ModelInfo
from securicad.enterprise.organizations import Organization as Organization
from securicad.enterprise.projects import AccessLevel as AccessLevel
from securicad.enterprise.projects import Project as Project
from securicad.enterprise.scenarios import Scenario as Scenario
from securicad.enterprise.simulations import Simulation as Simulation
from securicad.enterprise.tunings import Tuning as Tuning
from securicad.enterprise.users import Role as Role
from securicad.enterprise.users import User as User

__version__ = "1.1.0"


def client(*args: Any, **kwargs: Any) -> Client:
    return Client(*args, **kwargs)
