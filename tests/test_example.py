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

import random
import sys
from pathlib import Path
from urllib.parse import urljoin

import conftest
import pytest
import utils

# isort: off

sys.path.append(str(Path(__file__).resolve().parent.parent))
import securicad.aws_collector as aws_collector
import securicad.enterprise as enterprise

# isort: on


def test_example():
    def get_org_name(client: enterprise.Client) -> str:
        orgs = client.organizations.list_organizations()
        while True:
            org_name = f"org-{random.randint(1000, 9999)}"
            for org in orgs:
                if org.name.lower() == org_name.lower():
                    break
            else:
                return org_name

    # Fetch AWS data
    config_data = aws_collector.get_config_data(
        access_key=conftest.AWS_IMPORT_CONFIG["accounts"][0]["access_key"],
        secret_key=conftest.AWS_IMPORT_CONFIG["accounts"][0]["secret_key"],
        region=conftest.AWS_IMPORT_CONFIG["accounts"][0]["regions"][0],
    )
    aws_data = aws_collector.collect(config=config_data)

    # securiCAD Enterprise credentials
    username = conftest.ADMIN_USERNAME
    password = conftest.ADMIN_PASSWORD

    # (Optional) Organization of user
    # If you are using the system admin account set org = None
    org = None

    # (Optional) CA certificate of securiCAD Enterprise
    # If you don't want to verify the certificate set cacert = False
    cacert = False

    # securiCAD Enterprise URL
    base_url = conftest.BASE_URL
    backend_url = conftest.BACKEND_URL

    # Create an authenticated enterprise client
    client = enterprise.client(
        base_url=base_url,
        backend_url=backend_url,
        username=username,
        password=password,
        organization=org,
        cacert=cacert,
    )

    # Create organization and project
    org = client.organizations.create_organization(get_org_name(client))
    client.projects.create_project("My project", organization=org)

    # Get the project where the model will be added
    project = client.projects.get_project_by_name("My project")

    # Generate securiCAD model from AWS data
    model_info = client.util.generate_aws_model(
        project=project, name="My model", cli_files=[aws_data]
    )
    model = model_info.get_model()

    # securiCAD metadata with all assets and attacksteps
    metadata = client.metadata.get_metadata()

    # Set high value assets in securiCAD model
    for obj in model.objects(asset_type="S3Bucket"):
        obj.attack_step("readObject").meta["consequence"] = 7

    # Save changes to model in project
    model_info.save(model)

    # Start a new simulation in a new scenario
    scenario = project.create_scenario(model_info, name="My scenario")
    simulation = scenario.get_simulation_by_name(name="Initial simulation")

    # Poll for results and return them when simulation is done
    results = simulation.get_results()

    assert results["report_url"] == urljoin(
        conftest.BASE_URL,
        f"project/{project.pid}/scenario/{scenario.tid}/report/{simulation.simid}",
    )
    org.delete()
