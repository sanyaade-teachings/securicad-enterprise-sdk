from securicad import aws_collector, enterprise

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
model_info = client.parsers.generate_aws_model(
    project, name="My model", cli_files=[aws_data]
)
model = model_info.get_model()

# securiCAD metadata with all assets and attacksteps
metadata = client.metadata.get_metadata()

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
model_info.save(model)

# Start a new simulation in a new scenario
scenario = client.scenarios.create_scenario(project, model_info, name="My scenario")
simulation = client.simulations.get_simulation_by_name(
    scenario, name="Initial simulation"
)

# Poll for results and return them when simulation is done
results = simulation.get_results()
