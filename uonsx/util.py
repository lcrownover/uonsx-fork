from __future__ import annotations

import json
import re
from pprint import pformat
from typing import Union, List
import ipaddress

from colorama import Fore
from columnar import columnar

from uonsx.error import NSXInvalidPathError, NSXObjectHasDependenciesError


def format_table(headers: list[str], data: list[list[str]]) -> str:
    table = columnar(data, headers, no_borders=True)
    return table


def strfmt(json_data: str):
    return pformat(json.loads(json_data), indent=4)


def colorize(msg: str, color: str = ""):
    valid_colors = {
        "blue": Fore.BLUE,
        "red": Fore.RED,
        "green": Fore.GREEN,
        "yellow": Fore.YELLOW,
    }
    c = valid_colors.get(color)
    if c:
        return c + msg + Fore.RESET
    return msg


def valid_path(path: str) -> bool:
    if path.startswith("/infra/domains"):
        return True
    return False


def expand_csl(csl: str) -> list[str]:
    """
    Returns a cleansed list of strings from a comma-separated list
    """
    return [i.strip() for i in csl.split(",")]


def cleanse_display_name(display_name: str) -> str:
    return re.sub(r"[ \\|\'\":;,\.\?\[\]\{\}\^\%\$\#\@\!\&\>\<\/*]", "-", display_name)


def format_dependency_list(err: NSXObjectHasDependenciesError) -> str:
    dependency_list = sorted(
        [i.strip() for i in str(err).split("[")[1].split("]")[0].split(",")]
    )
    return "\n".join(dependency_list)


def get_policy_id_from_path(path: str) -> str:
    """Returns the id of a policy when given a valid NSX object path"""
    if not "security-policies" in path:
        raise NSXInvalidPathError(f"Path '{path}' does not contain policy information")
    return [e.strip() for e in path.split("/") if e.strip()][4]


def get_rule_id_from_path(path: str) -> str:
    """Returns the id of a rule when given a valid NSX object path"""
    if not "security-policies" in path:
        raise NSXInvalidPathError(f"Path '{path}' does not contain policy information")
    if not "rules" in path:
        raise NSXInvalidPathError(f"Path '{path}' does not contain rules information")
    return [e.strip() for e in path.split("/") if e.strip()][6]


class IPParser:
    @classmethod
    def parse(cls, ip_object: str):
        if ":" in ip_object:
            if "/" in ip_object:
                return IP6Network(ip_object)
            return IP6Address(ip_object)
        if "/" in ip_object:
            return IPNetwork(ip_object)
        return IPAddress(ip_object)



class IPAddress:
    def __init__(self, ip: str):
        self._ip = self._parse(ip)

    def __repr__(self):
        return self._ip

    def _parse(self, ip: str):
        return ipaddress.ip_address(ip)

class IP6Address:
    def __init__(self, ip6address: str):
        self._ip6address = self._parse(ip6address)

    def _parse(self, ip6address: str):
        return ip6address

class IP6Network:
    def __init__(self, ip6network: str):
        self._ip6network = self._parse(ip6network)

    def _parse(self, ip6network: str):
        return ip6network


class IPNetwork:
    def __init__(self, ipnetwork: str):
        self._ipnetwork = self._parse(ipnetwork)

    def _parse(self, ipnetwork: str):
        return ipnetwork

class IPSet:
    def __init__(self, ip_objects: List[Union[IPAddress, IPNetwork, IP6Address, IP6Network]]):
        self._objects = ip_objects

    def _parse(self, ipaddress: str):
        return ipaddress
