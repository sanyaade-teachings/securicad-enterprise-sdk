# securiCAD Enterprise SDK

A Python SDK for [foreseeti's securiCAD Enterprise](https://foreseeti.com/securicad-enterprise/)

## Compatibility

The appropriate version of securiCAD Enterprise SDK will vary depending on your version of securiCAD Enterprise. To see your version of securiCAD Enterprise you can look at the login screen where it's shown.

securiCAD Enterprise | SDK
---------------------|-----
<= 1.10.3 | 0.2.0
   1.11.0| 0.3.0
\>= 1.11.1 |0.3.1

## Getting started

### Download and setup the SDK

Install `securicad-enterprise` with pip:

```shell
pip install securicad-enterprise
```

or clone this repository from GitHub:

```shell
git clone https://github.com/foreseeti/securicad-enterprise-sdk.git
```

### (AWS) Get the required AWS credentials

To use the Enterprise SDK for AWS-based environments, the SDK requires AWS credentials to be able to fetch the data.
The easiest way is to create an IAM User with the required permissions and generate access keys for that IAM User:

* [Create an IAM user](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_users_create.html) with this [IAM policy](https://vanguard.securicad.com/iam_policy.json)
* [Generate access keys](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_access-keys.html) for the IAM user

### Run your first AWS simulation

The following snippet runs a simulation on an AWS environment where the high value assets are all S3 Buckets and fetches the results.
Please note, never store your credentials in source code, this is just an example.

To collect the AWS data, we use the [securiCAD AWS Collector](https://github.com/foreseeti/securicad-aws-collector).

<!-- embedme example.py -->

```python
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

```

If you wish to run the SDK with a local file, replace the `# Fetch AWS data` section in the above example with:

```python
with open('data.json', mode='r', encoding='utf-8') as json_file:
    aws_data = json.load(json_file)
```

## High value assets

Any object and attack step in the model can be set as a high value asset but it requires knowledge about the underlying model and concepts which can be fetched by using `client.metadata.get_metadata()`.
Use `model.set_high_value_assets()` with the `high_value_assets` parameter and set your high value assets by specifying the object type `metaconcept`, object identifier `id` and target `attackstep` as a list of dicts:

```python
high_value_assets = [
    {
        "metaconcept": "EC2Instance",
        "attackstep": "HighPrivilegeAccess",
        "consequence": 7,
    },
    {
        "metaconcept": "DynamoDBTable",
        "attackstep": "AuthenticatedRead",
        "id": {
            "type": "name",
            "value": "VanguardTable",
        },
    },
    {
        "metaconcept": "S3Bucket",
        "attackstep": "AuthenticatedWrite",
        "id": {
            "type": "tag",
            "key": "arn",
            "value": "arn:aws:s3:::my_corporate_bucket/",
        },
    },
]

# Set high value assets in securiCAD model
model.set_high_value_assets(high_value_assets=high_value_assets)
```

`id` is used to match objects in the model with the high value assets.
The supported `type` are currently `name` and `tag`.
Omitting the `id` parameters will set all assets of that type as a high value asset.
Omitting `consequence` will automatically set it to `10`.

## User management

You can create Organizations, Projects and Users via the SDK. Users have a `Role` in an Organization as well as an `AccessLevel` in a Project. Read more about user management in Enterprise [here](https://www.foreseeti.com/).

```python
from securicad.enterprise import AccessLevel, Role

# Create new organization
org = client.organizations.create_organization(name="My org")

# Create new project
project = client.projects.create_project(name="My project", organization=org)

# Create a new user with the User-level Role
user = client.users.create_user(
    username="MyUser",
    password="Password",
    firstname="John",
    lastname="Doe",
    role=Role.USER
    organization=org,
)

# Add the user to the new project
project.add_user(user=user, access_level=AccessLevel.USER)
```

## Certificates
If you have installed securiCAD Enterprise with a client certificate or have received one from foreseeti to access a managed instance your script will need to use the certificate to communicate with the instance.

### Managed instance
To use your `.p12` certificate file with the SDK, you need to extract the `.crt` and `.key` files. Run the following snippets to extract the required files. When prompted for the Import Password, use the one provided to you by foreseeti.

`openssl pkcs12 -in cert.p12 -nocerts -out cert.key -nodes`

`openssl pkcs12 -in cert.p12 -clcerts -nokeys -out cert.crt`

To run the SDK with the extracted files, update your `client` to the following:

```python
client_cert = ("cert.crt", "cert.key")

# Create an authenticated enterprise client
client = enterprise.client(
    url, settings.username, settings.password, client_cert=client_cert
)
```

### On-premise installation
For on-premise installations you can use the ca certificate directly as described in `example.py`

## Tunings

You can modify models in specific ways with the tunings api.

A tuning has 3 core attributes: type, filter, arguments. The type is the category of change, the filter is what you want the change applied to, and the arguments are what new values you want.

**Type**

The tuning type is one of 5, the value of this field affects what other arguments are accepted.

- `attacker`, add attack steps to the attacker's entrypoints
- `ttc`, set the TTC distribution function of attack steps
- `probability`, set the probability of defenses
- `consequence`, set the consequence of attack steps
- `tag`, add tags to objects

**Filter**

The filter is how you select which objects the arguments are applied to. It's a dictionary which, depending on type, accepts different values. More details in the various type descriptions.

### `attacker`: Adding attack steps to the attacker's entrypoints

To add an attack step to the attacker's entrypoints, you can create a tuning like this:

```python
tuning = client.tunings.create_tuning(
    project,
    tuning_type="attacker",
    filterdict={"attackstep": "HighPrivilegeAccess", "object_name": "Prod srv 1"},
)
```

This will add the attack step `HighPrivilegeAccess` of objects named `Prod srv 1` to the attacker's entrypoints.

The filter accepts these arguments:

- `metaconcept`: the class of the objects to connect the attacker to.
- `object_name`: the name of the objects to connect the attacker to.
- `attackstep`: the name of the attack step to connect the attacker to.
- `tags`: tags that must be present on the objects to connect the attacker to.

### `ttc`: Setting the Time-To-Compromise distribution function of attack steps

To set the Time-To-Compromise distribution function of a specific attack step of a specific object, you can create a tuning like this:

```python
tuning = client.tunings.create_tuning(
    project,
    tuning_type="ttc",
    filterdict={"object_name": "Prod srv 1", "attackstep": "HighPrivilegeAccess"},
    ttc="Exponential,3",
)
```

or all objects of a class

```python
tuning = client.tunings.create_tuning(
    project,
    tuning_type="ttc",
    filterdict={"metaconcept": "EC2Instance", "attackstep": "HighPrivilegeAccess"},
    ttc="Exponential,3",
)
```

The filter will accept these arguments:

- `metaconcept`: the class of the objects to set TTC for.
- `object_name`: the name of the objects to set TTC for.
- `attackstep`: the name of the attack step to set TTC for.
- `tags`: tags that must be present on the objects to set TTC for.

The tuning takes these arguments:

- `ttc`: A string representation of the TTC distribution function.

### `probability`: Setting the probability of defenses

To enable all defenses in the model you can create a tuning like this:

```python
tuning = client.tunings.create_tuning(
    project,
    tuning_type="probability",
    filterdict={},
    probability=1.0,
)
```

Or to set patched on all `EC2Instance` objects:

```python
tuning = client.tunings.create_tuning(
    project,
    tuning_type="probability",
    filterdict={"metaconcept": "EC2Instance", "defense": "Patched"},
    probability=0.5,
)
```

The filter will accept these arguments:

- `metaconcept`: the class of the objects to set the probability for.
- `object_name`: the name of the objects to set the probability for.
- `defense`: the name of the defense to set the probability for.
- `tags`: tags that must be present on the objects to set the probability for.

The tuning takes these arguments:

- `probability`: Probability of the defense being enabled.

### `consequence`: Setting the consequence of attack steps

To set the consequence of any EC2Instance object in prod being reached:

```python
tuning = client.tunings.create_tuning(
    project,
    tuning_type="consequence",
    filterdict={"metaconcept": "EC2Instance", "defense": "Patched", "tags": {"env": "prod"}},
    consequence=2,
)
```

The filter will accept these arguments:

- `metaconcept`: the class of the objects to set the consequence for.
- `object_name`: the name of the objects to set the consequence for.
- `attackstep`: the name of the attack step to set the consequence for.
- `tags`: tags that must be present on the objects to set the consequence for.

The tuning takes these arguments:

- `consequence`: Consequence value of attack step(s) being reached. An integer in the range [1,10].

### `tag`: Adding tags to objects

To add tags to all `EC2Instance` objects:

```python
tuning = client.tunings.create_tuning(
    project,
    tuning_type="tag",
    filterdict={"metaconcept": "EC2Instance"},
    tags={"c/i/a": "1/2/3"},
)
```

The filter will accept these arguments:

- `metaconcept`: the class of the objects to add tags to.
- `object_name`: the name of the objects to add tags to.
- `tags`: tags that must be present on the objects to add tags to.

The tuning takes these arguments:

- `tags`: A dictionary of zero or more key-value pairs.

## Vulnerability data and vulnerabilities
securiCAD Enterprise supports vulnerability data from third parties in combination with the AWS data. Typical examples are vulnerability scanners, static code analysis and dependency managers. Vulnerability data can be used to simulate the impact of known vulnerabilities in your AWS environment.

If you wish to run the simulation with third party vulnerability data, include the the `vul_files` parameter for `client.parsers.generate_aws_model()`.
```python
model_info = client.parsers.generate_aws_model(
    project, name="My model", cli_files=[aws_data], vul_files=[vul_data]
)

```
The expected `vuln_data` format is explained below.

### Vulnerability data format
securiCAD Enterprise supports any type of vulnerability data by using a generic json format. The json file should be a list of `findings` that describes each finding from e.g., a vulnerability scanner. All fields are mandatory and validated, but some can be left empty. See the example below for a practical example of a finding of `CVE-2018-11776` on a specific EC2 instance. `"cve"`, `"cvss"` and `"id"` (instance-id) are always mandatory. If the application is not listening on any port, you can set `"port"` to `0`.

```json
{
    "findings": [
        {
            "id": "i-1a2b3c4d5e6f7",
            "ip": "",
            "dns": "",
            "application": "Apache Struts 2.5.16",
            "port": 80,
            "name": "CVE-2018-11776",
            "description": "Apache Struts versions 2.3 to 2.3.34 and 2.5 to 2.5.16 suffer from possible Remote Code Execution when alwaysSelectFullNamespace is true",
            "cve": "CVE-2018-11776",
            "cwe": "",
            "cvss": [
                {
                    "version": "3.0",
                    "score": 8.1,
                    "vector": "CVSS:3.0/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"
                }
            ]
        }
    ]
}

```

### Vulnerabilities in the simulation
securiCAD Enterprise uses the [CVSS vector](https://www.first.org/cvss/v3.1/specification-document) of a [CVE](https://cve.mitre.org/about/faqs.html#what_is_cve) to asses the impact of a vulnerability in the context of your AWS environment. For example, a CVE with `AV:L` is only exploitabe with local access and not via network access. `AC:H` will require more effort from the attacker compared to `AC:L` and `PR:H` will require the attacker to have high privilege access before being able to exploit the vulnerability in the simulation. The impact of the vulnerability is decided based on the `C/I/A` part of the vector.

`CVSS:2.0` vectors are automatically converted to `CVSS:3` by the tool and if multiple versions are available, the tool will always select the latest one.

## Disable attack steps

To configure the attack simulation and the capabilities of the attacker use `Model.disable_attackstep(metaconcept, attackstep, name)`:

```python
# Disable ReadObject on a specific S3Bucket
model.disable_attackstep("S3Bucket", "ReadObject", "my-bucket")

# Disable DeleteObject on all S3Buckets
model.disable_attackstep("S3Bucket", "ReadObject")

# Save changes to model in project
model_info.save(model)
```

## Batch scenario operations

Enterprise also supports batch scenario operations through the API.

You can POST json data to `HOST/batch/v1/jobs`. This endpoint requires a valid JWT token from the corresponding Enterprise instance.

Here's a brief example of input data, using output json data from the securicad-aws-collector.

```python

base64_encoded_aws_collector_data = base64.b64encode(json.dumps(aws_data).encode("utf-8")).decode("utf-8")

test_data = {
    "name": "model_of_test_env",
    "parser": "aws-parser",
    "project_id": project.pid,
    "files": [
        {
            "sub_parser": "aws-cli-parser",
            "name": "aws_cli.json",
            "content": base64_encoded_aws_collector_data,
        },
    ],
    "scenarios": [
        {
            "name": "myscenario",
            "tunings": [ # These tunings are the same tunings as described above
                {
                    "type": "consequence",
                    "op": "apply",
                    "filter": {
                        "metaconcept": "EC2Instance",
                        "attackstep": "HighPrivilegeAccess",
                    },
                    "consequence": 7,
                },
                {
                    "type": "attacker",
                    "op": "apply",
                    "filter": {
                        "object_name": "instance1",
                        "attackstep": "HighPrivilegeAccess",
                    },
                },
            ],
        },
    ],
}

batch_url = f"https://enterpriseinstance.foo/batch/v1"
resp = client._session.post(f"{batch_url}/jobs", json=test_data)
tag = resp.json()["response"]["tag"]
# you can poll "{batch_url}/poll/{tag}" to get job status

```

## Examples

Below are a few examples of how you can use `boto3` to automatically collect name or ids for your high value assets.

### Get EC2 instance ids

Get all EC2 instance ids where the instance is running and has the tag `owner` with value `erik`.

```python
import boto3

session = boto3.Session()
ec2 = session.resource('ec2')

# List all running EC2 instances with the owner-tag erik
instances = ec2.instances.filter(
    Filters=[
        {"Name": "tag:owner", "Values": ["erik"]},
        {'Name': 'instance-state-name', 'Values': ['running']}
    ]
)
# Get the instance-id of each filtered instance
instance_ids = [instance.id for instance in instances]
```

### Get RDS instance identifiers

Get all RDS instances and their identifiers.

```python
import boto3

session = boto3.Session()
rds = session.client('rds')

# Get all RDS instance identifers with a paginator
dbinstances = []
paginator = rds.get_paginator('describe_db_instances').paginate()
for page in paginator:
    for db in page.get('DBInstances'):
        dbinstances.append(db['DBInstanceIdentifier'])
```

### Get S3 buckets

Get all S3 buckets where the bucket name contains the string `erik`.

```python
import boto3

session = boto3.Session()
s3 = session.resource('s3')

# Get all s3 buckets where `erik` is in the bucket name
buckets = []
for bucket in s3.buckets.all():
    if 'erik' in bucket.name:
        buckets.append(bucket.name)
```

## License

Copyright © 2020-2021 [Foreseeti AB](https://foreseeti.com)

Licensed under the [Apache License, Version 2.0](https://www.apache.org/licenses/LICENSE-2.0)
