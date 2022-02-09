# Initialises an enterprise client instance through credentials configures in conf.ini
# call setup() from any script you wish to create and make sure get_configpath points to your conf.ini file
from __future__ import annotations

import configparser
import logging
import sys
from pathlib import Path
from typing import Optional, Tuple

from utils import init_logging

from securicad.enterprise.client import Client

log = logging.getLogger("auth")


def get_configpath() -> str:
    return str(Path(__file__).resolve().parent.joinpath("", "conf.ini"))


def get_credentials() -> Tuple[Optional[str], Optional[str], Optional[str]]:
    config = configparser.ConfigParser()
    config.read(get_configpath())
    if "AUTH" not in config:
        return None, None, None
    return (
        config["AUTH"].get("username"),
        config["AUTH"].get("password"),
        config["AUTH"].get("organization"),
    )


def get_urls() -> Tuple[str, str]:
    config = configparser.ConfigParser()
    config.read(get_configpath())
    if "URL" not in config:
        sys.exit("Missing securiCAD Enterprise URL in conf.ini file")
    return (
        config["URL"].get("authserviceurl"),
        config["URL"].get("serviceurl"),
    )


def get_certs() -> Tuple[Optional[str], Optional[str], Optional[str]]:
    config = configparser.ConfigParser()
    config.read(get_configpath())
    if "CERT" not in config:
        return (
            None,
            None,
            None,
        )
    return (
        config["CERT"].get("cacert"),
        config["CERT"].get("clientcert"),
        config["CERT"].get("clientcertkey"),
    )


def setup() -> Client:
    """Initializes an enterprise client instance from configurations values in examples/conf.ini"""
    init_logging(log=log)
    creds = get_credentials()
    urls = get_urls()
    certs = get_certs()

    username = creds[0]
    password = creds[1]
    org = creds[2]
    cacert = False if certs[0] in ["", None] else certs[0]
    url = urls[1][:-13]
    log.info(f"Connecting to securiCAD Enterprise")
    es_client = Client(
        base_url=url,
        username=username,
        password=password,
        organization=org,
        cacert=cacert,
    )
    return es_client
