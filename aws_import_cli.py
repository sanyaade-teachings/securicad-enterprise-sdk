# Copyright 2019 Foreseeti AB
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

import os
import sys
import argparse
import configparser
import traceback
import json
import time
import concurrent.futures
from datetime import datetime, timedelta
from threading import Lock
from collections import defaultdict

try:
    import boto3
    from botocore.config import Config
    from botocore.exceptions import ClientError
except ModuleNotFoundError as e:
    sys.exit(f"You need the boto3, botocore.config and botocore.exceptions to run this script: {e}")

config = Config(retries=dict(max_attempts=10))

PARSER_VERSION = 5
PARSER_VERSION_FIELD = "parser_version"
MAX_RETRIES = 4


def serialize_datetime(o):
    if isinstance(o, datetime):
        return o.__str__()


def import_cli(
    region,
    aws_access_key_id,
    aws_secret_access_key,
    include_inspector=False,
    log_func=print,
    threads=None,
    delay=None,
):
    """Imports an AWS environment using the given credentials,
    or searches the system for credentials if none where given"""

    # Initialize session with credentials
    session = boto3.session.Session(
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        region_name=region,
    )

    if region not in session.get_available_regions("ec2"):
        raise ValueError("'{}' is not a valid AWS region".format(region))

    # Client cache
    clients_lock = Lock()
    clients = {}

    def get_client(name):
        """Gets the client with the given name from the cache,
        or creates it if it doesn't exist yet"""
        with clients_lock:
            if name not in clients:
                clients[name] = session.client(name, config=config)
            return clients[name]

    def remove_metadata(obj):
        """Removes 'ResponseMetadata' from the given dictionary"""
        del obj["ResponseMetadata"]
        return obj

    # Create list of tasks to be performed in parallel
    tasks = []

    def paginate(client, func, key, param=None):
        """Call the paginate function on client
        and aggregate the results
        """
        paginator = get_client(client).get_paginator(func)
        caller_func = getattr(paginator, "paginate")
        page_iterator = api_call(caller_func, param)
        pages_data = []
        for page in page_iterator:
            clean_page = remove_metadata(page)
            pages_data.extend(clean_page[key])
        return {key: pages_data}

    def unpaginated(client, func, key=None, param=None):
        """Clients without paginated functions"""
        client = get_client(client)
        client_func = getattr(client, func)
        results = api_call(client_func, param)
        results = remove_metadata(results)
        if key is not None:
            return results[key]
        else:
            return results

    def api_call(func, param=None):
        """Exponential backoff if throttled for each API call"""
        for retry in range(MAX_RETRIES):
            try:
                if param is not None:
                    return func(**param)
                else:
                    return func()
            except ClientError as ex:
                if ex.response["Error"]["Code"] == "Throttling":
                    time.sleep(2 ** retry)
                    continue
                else:
                    raise ex

    def describe_instances():
        log_func("Executing ec2 describe-instances, describe-images")
        reservations = paginate("ec2", "describe_instances", key="Reservations")
        image_ids = defaultdict(list)
        for res in reservations["Reservations"]:
            for instance in res["Instances"]:
                instance["IsWindows"] = False
                image_ids[instance["ImageId"]].append(instance)
        # Determine if images assigned to an instance is on the Windows Platform
        images = unpaginated(
            "ec2", "describe_images", key="Images", param={"ImageIds": list(image_ids.keys())}
        )
        for image in images:
            if image.get("Platform") == "windows":
                for instance in image_ids[image["ImageId"]]:
                    instance["IsWindows"] = True
        return ["instance"], reservations

    tasks.append(describe_instances)

    def describe_network_interfaces():
        log_func("Executing ec2 describe-network-interfaces")
        return (
            ["interface"],
            paginate("ec2", "describe_network_interfaces", key="NetworkInterfaces"),
        )

    tasks.append(describe_network_interfaces)

    def describe_security_groups():
        log_func("Executing ec2 describe-security-groups")
        return (
            ["securitygroup"],
            paginate("ec2", "describe_security_groups", key="SecurityGroups"),
        )

    tasks.append(describe_security_groups)

    def describe_subnet():
        log_func("Executing ec2 describe-subnets")
        return ["subnet"], paginate("ec2", "describe_subnets", key="Subnets")

    tasks.append(describe_subnet)

    def describe_network_acls():
        log_func("Executing ec2 describe-network-acls")
        return ["acl"], paginate("ec2", "describe_network_acls", key="NetworkAcls")

    tasks.append(describe_network_acls)

    def describe_vpcs():
        log_func("Executing ec2 describe-vpcs")
        return ["vpc"], paginate("ec2", "describe_vpcs", key="Vpcs")

    tasks.append(describe_vpcs)

    def describe_vpc_peering_connections():
        log_func("Executing ec2 describe-vpc-peering-connections")
        return (
            ["vpcpeering"],
            paginate("ec2", "describe_vpc_peering_connections", key="VpcPeeringConnections"),
        )

    tasks.append(describe_vpc_peering_connections)

    def describe_internet_gateways():
        log_func("Executing ec2 describe-internet-gateways")
        return (
            ["igw"],
            paginate("ec2", "describe_internet_gateways", key="InternetGateways"),
        )

    tasks.append(describe_internet_gateways)

    def describe_vpn_gateways():
        log_func("Executing ec2 describe-vpn-gateways")
        vgws = unpaginated("ec2", "describe_vpn_gateways")
        return ["vgw"], vgws

    tasks.append(describe_vpn_gateways)

    def describe_nat_gateways():
        log_func("Executing ec2 describe-nat-gateways")
        return ["ngw"], paginate("ec2", "describe_nat_gateways", key="NatGateways")

    tasks.append(describe_nat_gateways)

    def describe_route_tables():
        log_func("Executing ec2 describe-route-tables")
        return (
            ["routetable"],
            paginate("ec2", "describe_route_tables", key="RouteTables"),
        )

    tasks.append(describe_route_tables)

    def describe_volumes():
        log_func("Executing ec2 describe-volumes")
        return ["ebs"], paginate("ec2", "describe_volumes", key="Volumes")

    tasks.append(describe_volumes)

    def elb_describe_load_balancers():
        log_func("Executing elb describe-load-balancers")
        return (
            ["elb"],
            paginate("elb", "describe_load_balancers", key="LoadBalancerDescriptions"),
        )

    tasks.append(elb_describe_load_balancers)

    def elbv2_describe_load_balancers():
        log_func("Executing elbv2 describe-load-balancers")
        data = {}
        data.update(paginate("elbv2", "describe_load_balancers", key="LoadBalancers"))

        log_func("Executing elbv2 describe-target-groups")
        data.update(paginate("elbv2", "describe_target_groups", key="TargetGroups"))

        log_func("Executing elbv2 describe-target-health")
        for group in data["TargetGroups"]:
            targets = unpaginated(
                "elbv2",
                "describe_target_health",
                key="TargetHealthDescriptions",
                param={"TargetGroupArn": group["TargetGroupArn"]},
            )
            group["Targets"] = [x["Target"] for x in targets]

        log_func("Executing elbv2 describe-listeners")
        for lb in data["LoadBalancers"]:
            listeners = paginate(
                "elbv2",
                "describe_listeners",
                key="Listeners",
                param={"LoadBalancerArn": lb["LoadBalancerArn"]},
            )["Listeners"]
            for listener in listeners:
                rules = paginate(
                    "elbv2",
                    "describe_rules",
                    key="Rules",
                    param={"ListenerArn": listener["ListenerArn"]},
                )["Rules"]
                listener["Rules"] = rules
            lb["Listeners"] = listeners
        return ["elbv2"], data

    tasks.append(elbv2_describe_load_balancers)

    def autoscaling_describe_launch_configurations():
        log_func("Executing autoscaling describe-launch-configurations")
        return (
            ["launchconfigs"],
            paginate(
                "autoscaling",
                "describe_launch_configurations",
                key="LaunchConfigurations",
            ),
        )

    tasks.append(autoscaling_describe_launch_configurations)

    def s3api_list_buckets():
        log_func("Executing s3api list-buckets")
        buckets = unpaginated("s3", "list_buckets", key="Buckets")
        s3_buckets = []
        log_func("Executing s3api get-bucket-encryption, get-policy-status, get-bucket-policy")
        for bucket in buckets:
            # Encryption
            try:
                encryption = unpaginated(
                    "s3", "get_bucket_encryption", param={"Bucket": bucket["Name"]}
                )
                bucket["Encryption"] = encryption["ServerSideEncryptionConfiguration"]
            except (KeyError, ClientError) as ex:
                pass
            # Public status
            try:
                public = unpaginated(
                    "s3", "get_bucket_policy_status", param={"Bucket": bucket["Name"]}
                )
                bucket["Public"] = public["PolicyStatus "]["IsPublic"]
            except (KeyError, ClientError) as ex:
                bucket["Public"] = False
            # Encryption
            try:
                policy = unpaginated("s3", "get_bucket_policy", param={"Bucket": bucket["Name"]})
                bucket["Policy"] = json.loads(policy["Policy"])
            except (KeyError, ClientError) as ex:
                pass

            s3_buckets.append(bucket)
        return ["s3buckets"], s3_buckets

    tasks.append(s3api_list_buckets)

    def rds_describe_db_instances():
        log_func("Executing rds describe-db-instances")
        return (
            ["rds", "Instances"],
            paginate("rds", "describe_db_instances", key="DBInstances"),
        )

    tasks.append(rds_describe_db_instances)

    def rds_describe_db_subnet_groups():
        log_func("Executing rds describe-db-subnet-groups")
        return (
            ["rds", "SubnetGroups"],
            paginate("rds", "describe_db_subnet_groups", key="DBSubnetGroups"),
        )

    tasks.append(rds_describe_db_subnet_groups)

    def lambda_list_functions():
        log_func("Executing lambda list-functions")
        return ["lambda"], paginate("lambda", "list_functions", key="Functions")

    tasks.append(lambda_list_functions)

    def iam_list_users():
        iam = get_client("iam")
        log_func("Executing iam list-users")
        users = paginate("iam", "list_users", key="Users")["Users"]
        log_func(
            """Executing iam list-attached-user-policies,
                     list-user-policies, list-groups-for-user, get-user-policy"""
        )
        for user in users:
            user.update(
                paginate(
                    "iam",
                    "list_access_keys",
                    key="AccessKeyMetadata",
                    param={"UserName": user["UserName"]},
                )
            )
            user.update(
                paginate(
                    "iam",
                    "list_attached_user_policies",
                    key="AttachedPolicies",
                    param={"UserName": user["UserName"]},
                )
            )
            policy_names = paginate(
                "iam",
                "list_user_policies",
                key="PolicyNames",
                param={"UserName": user["UserName"]},
            )["PolicyNames"]
            user_policies = []
            for pn in policy_names:
                user_policy = unpaginated(
                    "iam",
                    "get_user_policy",
                    param={"UserName": user["UserName"], "PolicyName": pn},
                )
                user_policies.append(user_policy)
            user["UserPolicies"] = user_policies
            user.update(
                paginate(
                    "iam",
                    "list_groups_for_user",
                    key="Groups",
                    param={"UserName": user["UserName"]},
                )
            )
            user.update(
                paginate(
                    "iam",
                    "list_mfa_devices",
                    key="MFADevices",
                    param={"UserName": user["UserName"]},
                )
            )
            try:
                unpaginated("iam", "get_login_profile", param={"UserName": user["UserName"]})
                user["HasLoginProfile"] = True
            except ClientError as ex:
                if ex.response["Error"]["Code"] == "NoSuchEntity":
                    user["HasLoginProfile"] = False
                else:
                    raise ex
        return ["iam", "Users"], users

    tasks.append(iam_list_users)

    def iam_list_roles():
        log_func("Executing iam list-roles")
        roles = paginate("iam", "list_roles", key="Roles")["Roles"]
        log_func("Executing iam list-attached-role-policies, list-role-policies, get-role-policy")
        for role in roles:
            role.update(
                paginate(
                    "iam",
                    "list_attached_role_policies",
                    key="AttachedPolicies",
                    param={"RoleName": role["RoleName"]},
                )
            )
            policy_names = paginate(
                "iam",
                "list_role_policies",
                key="PolicyNames",
                param={"RoleName": role["RoleName"]},
            )["PolicyNames"]
            role_policies = []
            for pn in policy_names:
                role_policy = unpaginated(
                    "iam",
                    "get_role_policy",
                    param={"RoleName": role["RoleName"], "PolicyName": pn},
                )
                role_policies.append(role_policy)
            role["RolePolicies"] = role_policies
        return ["iam", "Roles"], roles

    tasks.append(iam_list_roles)

    def iam_list_groups():
        log_func("Executing iam list-groups")
        groups = paginate("iam", "list_groups", key="Groups")["Groups"]
        log_func(
            "Executing iam list-attached-group-policies, list-group-policies, get-group-policy"
        )
        for group in groups:
            group.update(
                paginate(
                    "iam",
                    "list_attached_group_policies",
                    key="AttachedPolicies",
                    param={"GroupName": group["GroupName"]},
                )
            )
            policy_names = paginate(
                "iam",
                "list_group_policies",
                key="PolicyNames",
                param={"GroupName": group["GroupName"]},
            )["PolicyNames"]
            group_policies = []
            for pn in policy_names:
                group_policy = unpaginated(
                    "iam",
                    "get_group_policy",
                    param={"GroupName": group["GroupName"], "PolicyName": pn},
                )
                group_policies.append(group_policy)
            group["GroupPolicies"] = group_policies
        return ["iam", "Groups"], groups

    tasks.append(iam_list_groups)

    def iam_list_policies():
        iam = get_client("iam")
        log_func("Executing iam list-policies")
        policies = paginate("iam", "list_policies", key="Policies", param={"OnlyAttached": True})[
            "Policies"
        ]
        iam_policies = []
        log_func("Executing iam get-policy-version")
        for policy in policies:
            policy_statement = unpaginated(
                "iam",
                "get_policy_version",
                param={
                    "PolicyArn": policy["Arn"],
                    "VersionId": policy["DefaultVersionId"],
                },
            )
            policy["Statement"] = policy_statement["PolicyVersion"]["Document"]["Statement"]
            iam_policies.append(policy)
        return ["iam", "Policies"], iam_policies

    tasks.append(iam_list_policies)

    def iam_list_instance_profiles():
        log_func("Executing iam list-instance-profiles")
        return (
            ["iam", "InstanceProfiles"],
            paginate("iam", "list_instance_profiles", key="InstanceProfiles")["InstanceProfiles"],
        )

    tasks.append(iam_list_instance_profiles)

    def kms_list_keys():
        log_func("Executing kms list-keys")
        keys = paginate("kms", "list_keys", key="Keys")["Keys"]
        for key in keys:
            key["Policy"] = unpaginated(
                "kms",
                "get_key_policy",
                key="Policy",
                param={"KeyId": key["KeyId"], "PolicyName": "default"},
            )
        return ["kms"], {"Keys": keys}

    tasks.append(kms_list_keys)

    def inspector_list_findings():
        log_func(
            """Executing inspector list-assessment-runs,
                    describe-assessment-runs, list-findings, describe-findings"""
        )

        # Filter findings to only return findings and runs from the last 30 days
        time_range = {
            "beginDate": datetime.now() - timedelta(days=300),
            "endDate": datetime.now(),
        }
        # List all rungs within the timeframe
        runs = paginate(
            "inspector",
            "list_assessment_runs",
            param={"filter": {"completionTimeRange": time_range}},
            key="assessmentRunArns",
        )["assessmentRunArns"]
        if not runs:
            return ["inspector"], []
        runs_details = unpaginated(
            "inspector", "describe_assessment_runs", param={"assessmentRunArns": runs}
        ).get("assessmentRuns", [])
        run_arn = None
        # Get the latest run with findings in it
        for run in sorted(runs_details, key=lambda x: x["completedAt"], reverse=True):
            count = sum(run.get("findingCounts", {}).values())
            if count > 0:
                run_arn = run["arn"]
                break
        if run_arn is None:
            return ["inspector"], []
        # Get all supported rule packages
        package_arns = []
        all_package_arns = paginate("inspector", "list_rules_packages", key="rulesPackageArns")
        package_arns_details = unpaginated(
            "inspector",
            "describe_rules_packages",
            param={"rulesPackageArns": all_package_arns["rulesPackageArns"]},
        )
        for package in package_arns_details["rulesPackages"]:
            if "Common Vulnerabilities and Exposures" in package["name"]:
                package_arns.append(package["arn"])
            if "Network Reachability" in package["name"]:
                package_arns.append(package["arn"])
        # List all findings within the timeframe and the latest run
        # Filter to only include supported finding types
        findings_filter = {
            "filter": {
                "creationTimeRange": time_range,
                "rulesPackageArns": package_arns,
            },
            "assessmentRunArns": [run_arn],
        }
        findings = paginate(
            "inspector",
            "list_findings",
            param=findings_filter,
            key="findingArns",
        )["findingArns"]

        def divide_chunks(l, n):
            # boto3 can only handle 100 findings at a time
            for i in range(0, len(l), n):
                yield l[i : i + n]

        findings_chunks = list(divide_chunks(findings, 100))
        findings_details = []
        for chunk in findings_chunks:
            # Get details about each finding
            details = unpaginated(
                "inspector",
                "describe_findings",
                key="findings",
                param={"findingArns": chunk},
            )
            findings_details.extend(details)

        return ["inspector"], findings_details

    if include_inspector:
        tasks.append(inspector_list_findings)

    def dynamodb_list_tables():
        log_func("Executing dynamodb list-tables")
        return ["dynamodb"], paginate("dynamodb", "list_tables", key="TableNames")

    tasks.append(dynamodb_list_tables)

    def ecr_describe_repositories():
        log_func("Executing ecr describe-repositories")
        repositories = paginate("ecr", "describe_repositories", key="repositories")["repositories"]
        for repository in repositories:
            try:
                repository["policy"] = json.loads(
                    unpaginated(
                        "ecr",
                        "get_repository_policy",
                        key="policyText",
                        param={"repositoryName": repository["repositoryName"]},
                    )
                )
            except get_client("ecr").exceptions.RepositoryPolicyNotFoundException:
                repository["policy"] = None
            repository["imageIds"] = paginate(
                "ecr",
                "list_images",
                key="imageIds",
                param={"repositoryName": repository["repositoryName"]},
            )["imageIds"]
        return ["ecr"], repositories

    tasks.append(ecr_describe_repositories)

    def ecs_list_clusters():
        def fake_paginate(client, func, key, param, n, items):
            pages_data = []
            head = None
            tail = items
            while len(tail) > 0:
                head = tail[:n]
                tail = tail[n:]
                param[key] = head
                pages_data.extend(unpaginated(client, func, key=key, param=param))
            return pages_data

        def list_clusters():
            arns = paginate("ecs", "list_clusters", key="clusterArns")["clusterArns"]
            return fake_paginate(
                "ecs",
                "describe_clusters",
                key="clusters",
                param={"include": ["ATTACHMENTS", "SETTINGS", "STATISTICS", "TAGS"]},
                n=100,
                items=arns,
            )

        def list_cluster_services(cluster_arn):
            def list_service_tasks(service_name):
                return paginate(
                    "ecs",
                    "list_tasks",
                    key="taskArns",
                    param={"cluster": cluster_arn, "serviceName": service_name},
                )["taskArns"]

            arns = paginate(
                "ecs", "list_services", key="serviceArns", param={"cluster": cluster_arn}
            )["serviceArns"]
            services = fake_paginate(
                "ecs",
                "describe_services",
                key="services",
                param={"cluster": cluster_arn, "include": ["TAGS"]},
                n=10,
                items=arns,
            )
            for service in services:
                service["tasks"] = list_service_tasks(service["serviceName"])
            return services

        def list_cluster_container_instances(cluster_arn):
            def list_container_instance_tasks(container_instance_arn):
                return paginate(
                    "ecs",
                    "list_tasks",
                    key="taskArns",
                    param={
                        "cluster": cluster_arn,
                        "containerInstance": container_instance_arn,
                    },
                )["taskArns"]

            arns = paginate(
                "ecs",
                "list_container_instances",
                key="containerInstanceArns",
                param={"cluster": cluster_arn},
            )["containerInstanceArns"]
            container_instances = fake_paginate(
                "ecs",
                "describe_container_instances",
                key="containerInstances",
                param={"cluster": cluster_arn, "include": ["TAGS"]},
                n=100,
                items=arns,
            )
            for container_instance in container_instances:
                container_instance["tasks"] = list_container_instance_tasks(
                    container_instance["containerInstanceArn"]
                )
            return container_instances

        def list_cluster_tasks(cluster_arn):
            arns = paginate("ecs", "list_tasks", key="taskArns", param={"cluster": cluster_arn})[
                "taskArns"
            ]
            return fake_paginate(
                "ecs",
                "describe_tasks",
                key="tasks",
                param={"cluster": cluster_arn, "include": ["TAGS"]},
                n=100,
                items=arns,
            )

        log_func("Executing ecs list-clusters")
        clusters = list_clusters()
        for cluster in clusters:
            cluster_arn = cluster["clusterArn"]
            cluster["services"] = list_cluster_services(cluster_arn)
            cluster["containerInstances"] = list_cluster_container_instances(cluster_arn)
            cluster["tasks"] = list_cluster_tasks(cluster_arn)
        return ["ecs"], clusters

    tasks.append(ecs_list_clusters)

    # Output dictionary
    output = {}
    # Create a thread pool executor to execute tasks asynchronously
    no_threads = threads if threads is not None else len(tasks)
    with concurrent.futures.ThreadPoolExecutor(max_workers=no_threads) as executor:
        # Submit the tasks to the thread pool executor
        future_to_result = [executor.submit(task) for task in tasks]

        # Iterate over the tasks as they finish
        for future in concurrent.futures.as_completed(future_to_result):
            if delay is not None:
                time.sleep(delay)
            names, result = future.result()

            # Add results of task to the output dictionary
            if len(names) == 1:
                output[names[0]] = result
            elif len(names) == 2:
                if names[0] not in output:
                    output[names[0]] = {}
                output[names[0]][names[1]] = result

    output[PARSER_VERSION_FIELD] = PARSER_VERSION
    log_func("Parsing done")
    return True, output


def read_config_entry(config_path, config_section, entry):
    if entry not in config_section:
        sys.exit("{} has no entry '{}'".format(config_path, entry))
    config_entry = config_section[entry]
    if not config_entry or not config_entry.strip():
        sys.exit("{} has no value for entry '{}'".format(config_path, entry))
    return config_entry.strip()


def read_config(config_path):
    config = configparser.ConfigParser()
    try:
        config.read_file(open(config_path))
    except FileNotFoundError as err:
        sys.exit(str(err))
    if "Credentials" not in config:
        sys.exit("{} has no section [Credentials]".format(config_path))
    access_key = read_config_entry(config_path, config["Credentials"], "AccessKey")
    secret_key = read_config_entry(config_path, config["Credentials"], "SecretKey")
    region = read_config_entry(config_path, config["Credentials"], "Region")
    return access_key, secret_key, region


def get_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--access-key", help="AWS Access Key")
    parser.add_argument("-s", "--secret-key", help="AWS Secret Key")
    parser.add_argument("-r", "--region", help="Region")
    parser.add_argument("-ins", "--inspector", help="Include Amazon Inspector", action="store_true")
    parser.add_argument("-t", "--threads", help="Number of concurrent threads", type=int)
    parser.add_argument("-d", "--delay", help="Seconds of delay before a new API call", type=float)
    parser.add_argument("-i", "--input", help="Input config file")
    parser.add_argument("-o", "--output", help="Output JSON file")
    return parser


def main():
    args = get_parser().parse_args().__dict__

    # Strip arguments and replace blank arguments with None
    for k in args:
        if args[k] and type(args[k]) is str:
            if args[k].strip():
                args[k] = args[k].strip()
            else:
                args[k] = None

    if args["input"]:
        # Read credentials from input file
        access_key, secret_key, region = read_config(args["input"])
    else:
        # Read credentials from command line arguments
        access_key = args["access_key"] if "access_key" in args else None
        secret_key = args["secret_key"] if "secret_key" in args else None
        region = args["region"] if "region" in args else None
    inspector = args.get("inspector", False)
    threads = args.get("threads", None)
    delay = args.get("delay", None)

    try:
        res, output = import_cli(
            region, access_key, secret_key, inspector, threads=threads, delay=delay
        )
        if not res:
            sys.exit(output)

        if args["output"]:
            output_file = args["output"]
        else:
            output_file = "aws.json"

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(output, f, default=serialize_datetime)

        print("Output written to", output_file)
    except ClientError as ex:
        errdata = ex.response["Error"]
        code = errdata["Code"]
        if code in [
            "InvalidClientTokenId",
            "AuthFailure    ",
            "UnrecognizedClientException",
        ]:
            print("Provided credentials were not accepted by AWS")
        elif code == "UnauthorizedOperation":
            print("Your credentials does not give you the required access")
        else:
            print("Unknown AWS error {}".format(ex))
    except Exception as ex:
        errpath = os.path.abspath("error.log")
        print("An error occured, log has been written at {}".format(errpath))
        with open(errpath, "w") as writer:
            traceback.print_exc(file=writer)


if __name__ == "__main__":
    main()
