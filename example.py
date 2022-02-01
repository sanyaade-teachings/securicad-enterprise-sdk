import securicad.aws_collector as aws_collector

import securicad.enterprise as enterprise

# Fetch AWS data
config_data = aws_collector.get_config_data(
    access_key="ACCESS KEY",
    secret_key="SECRET KEY",
    region="REGION",  # e.g., "us-east-1"
)
aws_data = aws_collector.collect(config=config_data)

# securiCAD Enterprise credentials
username = "username"
password = "password"

# (Optional) Organization of user
# If you are using the system admin account set org = None
org = "My organization"

# (Optional) CA certificate of securiCAD Enterprise
# If you don't want to verify the certificate set cacert = False
cacert = "/path/to/cacert.pem"

# securiCAD Enterprise URL
url = "https://xx.xx.xx.xx"

# Create an authenticated enterprise client
client = enterprise.client(
    base_url=url, username=username, password=password, organization=org, cacert=cacert
)

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
