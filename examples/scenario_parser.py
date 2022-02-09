# Validates a scenario tunings file used in scenario_scheduler
# You can use azure/default_tunings.json as a template
from __future__ import annotations

import json
import os
from typing import Any, Optional

import jsonschema
from jsonschema.exceptions import ValidationError

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCHEMA_PATH = os.path.join(BASE_DIR, "scenario_parser_schema.json")


def validate_input(data: bytes) -> dict[str, Any]:
    instance = json.loads(data.decode("utf-8"))
    try:
        with open(SCHEMA_PATH, "rb") as f:
            schema = json.load(f)
            jsonschema.validate(instance=instance, schema=schema)  # type: ignore
    except ValidationError as e:
        raise ValueError(e.message) from None
    return instance


def parse(data: bytes, metadata: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    return validate_input(data)
