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

from typing import TYPE_CHECKING

from securicad.enterprise.util import parsers

if TYPE_CHECKING:
    from securicad.enterprise.client import Client


class Util:
    def __init__(self, client: Client) -> None:
        self.client = client

    generate_azure_model = staticmethod(parsers.generate_azure_model)
    generate_aws_model = staticmethod(parsers.generate_aws_model)
