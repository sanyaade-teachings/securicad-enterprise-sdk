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
