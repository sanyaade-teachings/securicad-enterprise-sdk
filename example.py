import time

import aws_import_cli as aws
from securicad import enterprise

# AWS credentials
accesskey = "AWS ACCESS KEY"
secretkey = "AWS SECRET KEY"
region = "REGION"  # e.g., us-east-1

# Fetch AWS data
_, data = aws.import_cli(region, accesskey, secretkey)

# securiCAD Enterprise credentials
username = "username"
password = "password"

# (Optional) Organization of user
# If you are using the system admin account set org = None
org = "My organization"

# (Optional) CA certificate of securiCAD Enterprise
# If you don't want to verify the certificate set cacert = None
cacert = "/path/to/cacert.pem"

# securiCAD Enterprise URL
url = "https://xx.xx.xxx.x"

# Create an authenticated enterprise client
client = enterprise.client(url=url, username=username, password=password, org=org, cacert=cacert)

# Get project id of project where the model will be added
project_id = client.get_project(name="My project")

# Generate securiCAD model from AWS data
model_id, model = client.add_model(project_id, data, name="my-model")

# securiCAD metadata with all assets and attacksteps
metadata = client.get_metadata()

high_value_assets = [
    {
        "metaconcept": "S3Bucket",
        "attackstep": "ReadObject",
        "consequence": 7,
    }
]

# Set high value assets in securiCAD model
model.set_high_value_assets(high_value_assets=high_value_assets)

# Save changes to model in project
client.save_model(project_id, model)

# Start a new simulation in a new scenario
sim_id, scenario_id = client.start_simulation(project_id, model_id, name="My first simulation")

# Poll for results and return them when simulation is done
results = client.get_results(project_id, scenario_id, sim_id)
