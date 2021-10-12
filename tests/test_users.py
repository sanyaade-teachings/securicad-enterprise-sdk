# Copyright 2020-2021 Foreseeti AB <https://foreseeti.com>
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

import sys
from pathlib import Path

import pytest

import utils

# isort: off

sys.path.append(str(Path(__file__).resolve().parent.parent))
from securicad.enterprise.users import Role
from securicad.enterprise.exceptions import StatusCodeException

# isort: on


def test_whoami(data):
    def assert_whoami(client, user_data, org):
        user = client.users.whoami()
        utils.assert_user_data(user, user_data, org)

    def assert_whoami_fails(client):
        with pytest.raises(StatusCodeException) as e:
            client.users.whoami()
        utils.assert_status_code_exception(
            exception=e.value,
            status_code=401,
            method="GET",
            url=utils.get_url("whoami"),
            data={"msg": "Missing Authorization Header"},
        )

    for user_data in data["users"].values():
        client = utils.get_client(user_data["username"], user_data["password"])
        assert_whoami(client, user_data, None)
        client.logout()

    for org_data in data["organizations"].values():
        for user_data in org_data["users"].values():
            client = utils.get_client_org(
                user_data["username"], user_data["password"], org_data["name"]
            )
            assert_whoami(client, user_data, org_data["name"])
            client.logout()

    client = utils.get_client_sysadmin()
    client.logout()
    assert_whoami_fails(client)


def test_change_password(data):
    def assert_password_correct(username, password, org):
        client = utils.get_client_org(username, password, org)

    def assert_password_incorrect(username, password, org):
        with pytest.raises(StatusCodeException) as e:
            utils.get_client_org(username, password, org)
        utils.assert_status_code_exception(
            exception=e.value,
            status_code=401,
            method="POST",
            url=utils.get_url("auth/login"),
            data={"error": "Invalid login"},
        )

    def assert_change_password(client, username, old_password, new_password, org):
        assert_password_correct(username, old_password, org)
        assert_password_incorrect(username, new_password, org)
        utils.assert_access_token(client)
        old_token = client._get_access_token()

        client.users.change_password(old_password, new_password)

        assert_password_incorrect(username, old_password, org)
        assert_password_correct(username, new_password, org)
        utils.assert_access_token(client)
        new_token = client._get_access_token()

        assert old_token != new_token

    def assert_change_password_invalid(client, old_password, new_password):
        with pytest.raises(StatusCodeException) as e:
            client.users.change_password(old_password, new_password)
        utils.assert_status_code_exception(
            exception=e.value,
            status_code=400,
            method="POST",
            url=utils.get_url("changepwd"),
            data={"error": "Unable to update password: Old password does not match."},
        )

    def assert_change_password_fails(client, old_password, new_password):
        with pytest.raises(StatusCodeException) as e:
            client.users.change_password(old_password, new_password)
        utils.assert_status_code_exception(
            exception=e.value,
            status_code=401,
            method="POST",
            url=utils.get_url("changepwd"),
            data={"msg": "Missing Authorization Header"},
        )

    for user_data in data["users"].values():
        client = utils.get_client(user_data["username"], user_data["password"])
        assert_change_password(
            client, user_data["username"], user_data["password"], "password", None
        )
        assert_change_password(
            client, user_data["username"], "password", user_data["password"], None
        )
        assert_change_password_invalid(client, "password", user_data["password"])
        client.logout()

    for org_data in data["organizations"].values():
        for user_data in org_data["users"].values():
            client = utils.get_client_org(
                user_data["username"], user_data["password"], org_data["name"]
            )
            assert_change_password(
                client,
                user_data["username"],
                user_data["password"],
                "password",
                org_data["name"],
            )
            assert_change_password(
                client,
                user_data["username"],
                "password",
                user_data["password"],
                org_data["name"],
            )
            assert_change_password_invalid(client, "password", user_data["password"])
            client.logout()

    client = utils.get_client_sysadmin()
    client.logout()
    assert_change_password_fails(client, "old_password", "new_password")


def verify_user_exists(users, username, firstname, lastname, organization=None):
    for user in users:
        if user.username != username:
            continue
        assert user.organization == organization
        assert user.firstname == firstname
        assert user.lastname == lastname
        return True
    return False


def test_list_users_sysadmin(client):
    users = client.users.list_users()
    assert len(users) == 8
    users = sorted(users, key=lambda u: u.username)
    assert verify_user_exists(
        users, username="admin", firstname="admin", lastname="admin"
    )
    assert verify_user_exists(
        users,
        username="org1_admin",
        firstname="org1",
        lastname="admin",
        organization="org1",
    )
    assert verify_user_exists(
        users, username="org1_pc", firstname="org1", lastname="pc", organization="org1"
    )
    assert verify_user_exists(
        users,
        username="org1_user",
        firstname="org1",
        lastname="user",
        organization="org1",
    )
    assert verify_user_exists(
        users,
        username="org2_admin",
        firstname="org2",
        lastname="admin",
        organization="org2",
    )
    assert verify_user_exists(
        users, username="org2_pc", firstname="org2", lastname="pc", organization="org2"
    )
    assert verify_user_exists(
        users,
        username="org2_user",
        firstname="org2",
        lastname="user",
        organization="org2",
    )


def test_list_users_orgadmin(data):
    org1 = data["organizations"]["org1"]
    admin = [
        userdata
        for name, userdata in org1["users"].items()
        if userdata["role"] == Role.ADMIN
    ][0]
    client = utils.get_client_org(
        admin["username"], admin["password"], organization="org1"
    )

    users = client.users.list_users()
    assert len(users) == 3
    assert verify_user_exists(
        users,
        username="org1_admin",
        firstname="org1",
        lastname="admin",
        organization="org1",
    )
    assert verify_user_exists(
        users, username="org1_pc", firstname="org1", lastname="pc", organization="org1"
    )
    assert verify_user_exists(
        users,
        username="org1_user",
        firstname="org1",
        lastname="user",
        organization="org1",
    )


def test_get_user_by_uid(client):
    users = client.users.list_users()
    org1_admin = [u for u in users if u.username == "org1_admin"][0]
    fetched = client.users.get_user_by_uid(org1_admin.uid)
    assert fetched.uid == org1_admin.uid
    assert fetched.username == org1_admin.username
    assert fetched.firstname == org1_admin.firstname
    assert fetched.lastname == org1_admin.lastname
    assert fetched.role == org1_admin.role


def test_get_user_by_username(client):
    users = client.users.list_users()
    org1_admin = [u for u in users if u.username == "org1_admin"][0]
    fetched = client.users.get_user_by_username(org1_admin.username)
    assert fetched.uid == org1_admin.uid
    assert fetched.username == org1_admin.username
    assert fetched.firstname == org1_admin.firstname
    assert fetched.lastname == org1_admin.lastname
    assert fetched.role == org1_admin.role


def test_create_user(client):
    prevcount = len(client.users.list_users())
    org2 = client.organizations.get_organization_by_name(name="org2")
    client.users.create_user(
        username="a",
        firstname="b",
        lastname="c",
        password="pazzw00t",
        organization=org2,
        role=Role.ADMIN,
    )
    assert len(client.users.list_users()) == prevcount + 1


def test_user_update(client):
    users = client.users.list_users()
    org1_admin = [u for u in users if u.username == "org1_admin"][0]
    # keep old values
    oldfirstname = org1_admin.firstname
    oldlastname = org1_admin.lastname

    org1_admin.update(username="abc", firstname="def", lastname="ghi")
    newlist = client.users.list_users()
    abc = [u for u in newlist if u.username == "abc"]
    assert len(abc) == 1
    org1_admin.update(
        username="org1_admin", firstname=oldfirstname, lastname=oldlastname
    )


def test_user_delete(client):
    prevcount = len(client.users.list_users())
    org2 = client.organizations.get_organization_by_name(name="org2")
    user = client.users.create_user(
        username="a2",
        firstname="b2",
        lastname="c2",
        password="pazzw00t",
        organization=org2,
        role=Role.ADMIN,
    )
    user.delete()
    assert len(client.users.list_users()) == prevcount


def test_user_set_role(client):
    users = client.users.list_users()
    org1_pc = [u for u in users if u.username == "org1_pc"][0]
    assert org1_pc.role == Role.PROJECT_CREATOR
    # set
    org1_pc.set_role(Role.USER)
    # verify
    users2 = client.users.list_users()
    org1_pc2 = [u for u in users2 if u.username == "org1_pc"][0]
    assert org1_pc2.role == Role.USER
    # reset
    org1_pc.set_role(Role.PROJECT_CREATOR)
