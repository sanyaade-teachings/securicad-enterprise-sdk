# securiCAD Enterprise SDK

A Python SDK for [foreseeti's securiCAD Enterprise](https://foreseeti.com/securicad-enterprise/)

## Table of contents

- [securiCAD Enterprise SDK](#securicad-enterprise-sdk)
  * [Compatibility](#compatibility)
  * [Getting started](#getting-started)
  * [User management](#user-management)
  * [Certificates](#certificates)
  * [Tunings](#tunings)
  * [Vulnerability data and vulnerabilities](#vulnerability-data-and-vulnerabilities)
  * [Disable attack steps](#disable-attack-steps)
  * [Batch scenario operations](#batch-scenario-operations)
  * [Simulation result data formats](#simulation-result-data-formats)
  * [Exceptions](#exceptions)
  * [License](#license)

## Compatibility

The appropriate version of securiCAD Enterprise SDK will vary depending on your version of securiCAD Enterprise.
To see your version of securiCAD Enterprise you can look at the login screen where it's shown.

securiCAD Enterprise | SDK
---------------------|-----
<= 1.10.3            | 0.2.0
   1.11.0            | 0.3.0
\>= 1.11.1, < 1.12.0 | 0.3.1
\>= 1.12.0           | 0.3.3

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

* [Create an IAM user](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_users_create.html) with this [IAM policy](https://raw.githubusercontent.com/foreseeti/securicad-aws-collector/master/iam_policy.json)
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

## User management

You can create Organizations, Projects and Users via the SDK.
Users have a `Role` in an Organization as well as an `AccessLevel` in a Project.
Read more about user management in Enterprise [here](https://www.foreseeti.com/).

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

To use your `.p12` certificate file with the SDK, you need to extract the `.crt` and `.key` files.
Run the following snippets to extract the required files.
When prompted for the Import Password, use the one provided to you by foreseeti.

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

A tuning has 3 core attributes: type, filter, arguments.
The type is the category of change, the filter is what you want the change applied to, and the arguments are what new values you want.

**Type**

The tuning type is one of 5, the value of this field affects what other arguments are accepted.

- `attacker`, add attack steps to the attacker's entrypoints
- `ttc`, set the TTC distribution function of attack steps
- `probability`, set the probability of defenses
- `consequence`, set the consequence of attack steps
- `tag`, add tags to objects

**Filter**

The filter is how you select which objects the arguments are applied to.
It's a dictionary which, depending on type, accepts different values.
More details in the various type descriptions.

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

securiCAD Enterprise supports vulnerability data from third parties in combination with the AWS data.
Typical examples are vulnerability scanners, static code analysis and dependency managers.
Vulnerability data can be used to simulate the impact of known vulnerabilities in your AWS environment.

If you wish to run the simulation with third party vulnerability data, include the the `vul_files` parameter for `client.parsers.generate_aws_model()`.

```python
model_info = client.parsers.generate_aws_model(
    project, name="My model", cli_files=[aws_data], vul_files=[vul_data]
)
```

The expected `vuln_data` format is explained below.

### Vulnerability data format

securiCAD Enterprise supports any type of vulnerability data by using a generic json format.
The json file should be a list of `findings` that describes each finding from e.g., a vulnerability scanner.

The mandatory fields are `"application"`, `"port"`, `"cvss"` and one of the host identifiers `"host_id"`, `"host_ip"`, `"image_id"`, `"host_tags"`.
The fields `"host_id"`, `"host_ip"` and `"image_id"` are strings and `"host_tags"` is a list of `{"key": <key>, "value": <value>}` objects that matches on host tags.
`"name"`, `"description"`, `"cve"` and `"cwe"` are optional.

See the example below for a practical example of a finding of `CVE-2018-11776` on a specific EC2 instance with instance id `"i-1a2b3c4d5e6f7"`.
If the application is not listening on any port, you can set `"port"` to `0`.
CVSS 2.0, 3.0 and 3.1 vectors are supported.

The optional `"exploit"` parameter takes a string according to the [Exploitability (CVSS v2) or Exploit Code Maturity (CVSS v3) specification](https://www.first.org/cvss/specification-document) that will affect how much effort is required for the Attacker to exploit a vulnerability.
For example: `"exploit": "H"`

```json
{
  "findings": [
    {
      "host_id": "i-1a2b3c4d5e6f7",
      "application": "Apache Struts 2.5.16",
      "port": 80,
      "cve": "CVE-2018-11776",
      "name": "CVE-2018-11776",
      "description": "Apache Struts versions 2.3 to 2.3.34 and 2.5 to 2.5.16 suffer from possible Remote Code Execution when alwaysSelectFullNamespace is true",
      "cvss": [
        {
          "vector": "CVSS:3.0/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"
        }
      ]
    }
  ]
}
```

### Vulnerabilities in the simulation

securiCAD Enterprise uses the [CVSS vector](https://www.first.org/cvss/v3.1/specification-document) of a [CVE](https://cve.mitre.org/about/faqs.html#what_is_cve) to asses the impact of a vulnerability in the context of your AWS environment.
For example, a CVE with `AV:L` is only exploitabe with local access and not via network access.
`AC:H` will require more effort from the attacker compared to `AC:L` and `PR:H` will require the attacker to have high privilege access before being able to exploit the vulnerability in the simulation.
The impact of the vulnerability is decided based on the `C/I/A` part of the vector.

## Disable attack steps

To configure the attack simulation and the capabilities of the attacker use:

```python
from securicad.langspec import TtcDistribution, TtcFunction

# Disable ReadObject on a specific S3Bucket
my_bucket = model.objects(name="my-bucket", asset_type="S3Bucket")[0]
read_object = my_bucket.attack_step("readObject")
read_object.ttc = TtcFunction(distribution=TtcDistribution.INFINITY, arguments=[])

# Disable DeleteObject on all S3Buckets
for bucket in model.objects(asset_type="S3Bucket"):
    read_object = bucket.attack_step("readObject")
    read_object.ttc = TtcFunction(distribution=TtcDistribution.INFINITY, arguments=[])

# Save changes to model in project
model_info.save(model)
```

## Batch scenario operations

Enterprise also supports batch scenario operations through the API.

You can POST json data to `HOST/batch/v1/jobs`.
This endpoint requires a valid JWT token from the corresponding Enterprise instance.

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

## Simulation result data formats

The JSON format of the simulation results from `simulation.get_results()` and the webhooks are described below.
The examples are truncated but provides an example for each object type.

### Overview

The simulation results from the SDK and the webhooks are very similar and their respective overall formats are described first with their mututal objects detailed after.

#### Simulation results

The simulation report format used by securiCAD and the JSON blob that is returned by the SDK.

```json
{
    "simid": "187894052202290",
    "report_url": "https://mydomain.com/project/749432228616411/scenario/265400114917031/report/138174299751445",
    "results": {...},
    "model_data": {...},
    "threat_summary": [...],
    "chokepoints": [...],
    "attacker": {...}
}
```

* `simid`: The simulation id
* `report_url`: Complete URL to the simulation report in the UI
* `attacker`: Information about the Attacker object in the simulation

#### Webhooks

```json
{
    "meta": {...},
    "results": {...},
    "model": {...},
    "threat_summary": [...],
    "chokepoints": [...],
}
```

* `meta`: Metadata from the simulation including report url, project, scenario and simulation data.

### Examples

#### `results`

The `results` object provides the high level values for risk exposure as well as the TTCs for each high value asset in the list `risks`.
`maxrisk` is simply the sum of all `consequence` of the high value asset and `risk` is the "amount" of consequence the attacker is able to compromise.
The `ttcX` values is the TTC for each procentile and the `values` list contains the TTC for each sample (sorted and truncated).

```json
"results": {
    "date": "2021-11-11 10:20:46.099477",
    "confidentiality": 0.52,
    "integrity": 0.51,
    "availability": 0.52,
    "risk": 56.2,
    "maxrisk": 105.0,
    "risks": [
        {
            "metaconcept": "S3Bucket",
            "object_id": "1432",
            "object_name": "customer-records-demo",
            "attackstep": "ReadObject",
            "ttc5": "0",
            "ttc50": "1",
            "ttc95": "3",
            "probability": "1.0",
            "consequence": "7",
            "values": [
                0.02,
                1.58,
                2.68,
                4.1,
                5.55
            ],
            "attackstep_id": "1432.ReadObject"
        },
    ],
},
```
#### `model/model_data`

The `model` or `model_data` object contains a JSON representation of your complete model including every object keyed on its id in `objects` and each association in the list `associations` where `id1` and `id2` are references to object ids.

```json
"model_data": {
    "formatversion": 1,
    "mid": "187894052202290",
    "name": "This is my model",
    "samples": 1000,
    "threshold": 100,
    "metadata": {...},
    "tags": {...},
    "objects": {
        "570623112508326": {
            "name": "Bastion subnet",
            "eid": 1499,
            "metaconcept": "Subnet",
            "tags": {
                "workload": "demo",
                "Name": "Bastion subnet"
            },
            "attacksteps": [...],
            "defenses": [...]
        },
    },
    "associations": [
        {
            "id1": "190813838598594",
            "id2": "167878158543587",
            "link": "SubnetRouteTable",
            "type1": "subnets",
            "type2": "routeTable"
        },
    ],
    "groups": {...},
    "views": [...]
}
```

#### `threat_summary`

The `threat_summary` is a list of top attack steps used by the attacker including suggested mitigations in `defenses`.
Each object in the list contains information about the attack step, which high value assets it affects in `hva_list` as well as metadata such as `mitre` and `stride`.
`object` is a reference to a model id in `model["objects"]`

```json
"threat_summary": [
        {
            "attackstep": "GetRoleCredentials",
            "count": 2,
            "hva_list": [
                "1609.ReadDatabase",
            ],
            "object": "915990772612637",
            "user": "The attacker can get access to the set of permissions that the attached instance profile or role has.",
            "stride": "Information Disclosure",
            "mitre": "T1552.005 Unsecured Credentials: Cloud Instance Metadata API",
            "mitigation": "Follow the standard security advice of granting least privilege and consider using GuardDuty which triggers on this. See https://docs.aws.amazon.com/guardduty/latest/ug/guardduty_finding-types.html#unauthorized11",
            "defense": [
                {
                    "prevention": "IMDSv2",
                    "description": "Require the use of IMDSv2 when requesting instance metadata",
                    "name": "IMDSv2",
                    "disabled": "No session authentication",
                    "mitigation": "Require the use of IMDSv2 when requesting instance metadata. For more information, see https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/configuring-instance-metadata-service.html"
                }
            ]
        },
        {...}
]
```

#### `chokepoints`

This is data used for the chokepoints in the report.
It denotes the objects in the chokepoint visualization with `parentID` and `childID` which is references to an object's `eid` found in `model["objects"]`.
The `targets` list denotes which high value asset it affects.

```json
"chokepoints": [
    {
        "parentID": 734,
        "parentName": "Attacker",
        "childID": 740,
        "targets": [
            "1623",
            "1615"
        ],
        "childName": "Attacker Interface",
        "frequency": 1,
        "type": "default"
    },
    {...}
]
```

#### `meta`

This is metadata about a simulation result returned by the webhook.
The `report_url` is a deep link to the report excluding your IP/domain.
To use the URL externally, prepend your domain name to the url e.g., `https://mydomain.com/project/749432228616411/scenario/265400114917031/report/138174299751445`

```json
"meta": {
    "project": {
        "name": "My project",
        "description": "This is my project",
        "id": "749432228616410"
    },
    "user": "admin",
    "scenario": {
        "name": "Analysing my model",
        "description": "This is a scenario",
        "id": "265400114917030"
    },
    "simulation": {
        "name": "My first simulation",
        "description": "",
        "id": "138174299751450"
    },
    "report_url": [
        "/project/749432228616411/scenario/265400114917031/report/138174299751445"
    ]
}
```

## Exceptions

The SDK raises two types of exceptions depending on what went wrong.
`securicad.enterprise.exceptions.StatusCodeException` or the standard library exception `ValueError`.

`StatusCodeException` is raised when an unexpected status code is received from enterprise.
This can for example be a status code 401 on a failed login attempt.

```python
client = enterprise.client(
    base_url=url, username=username, password=password, organization=org, cacert=cacert
)
```

`ValueError` is raised when trying to get something that doesn't exist, e.g.

```python
model = client.models.get_model_by_name(project=p, name="doesnexist")
```

## License

Copyright © 2020-2022 [Foreseeti AB](https://foreseeti.com)

Licensed under the [Apache License, Version 2.0](https://www.apache.org/licenses/LICENSE-2.0)
