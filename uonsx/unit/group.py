from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from uonsx.unit.virtualmachine import NSXVirtualMachine

import json
from pprint import pformat
from typing import Union

from typing_extensions import Literal
from uonsx.error import (NSXExpressionIPAddressNotFoundError,
                         NSXExpressionsTooComplicatedError, NSXGenericError)
from uonsx.manager.expression import NSXExpressionManager
from uonsx.unit.expression import NSXExpression
from uonsx.unit.virtualmachine import NSXVirtualMachine
from uonsx.util import format_table


class NSXGroup:
    """
    Wrapper for an NSX Security Group

    example:
    {
        "expression": [
          {
            "member_type": "VirtualMachine",
            "value": "webvm",
            "key": "Tag",
            "operator": "EQUALS",
            "resource_type": "Condition"
          }
        ],
        "description": "web group",
        "display_name": "web group",
        "_revision":0
    }
    """
    def __init__(self, data: dict):
        self.data = data
        from uonsx.manager.group import NSXGroupManager

        self._group_mgr = NSXGroupManager.get_instance()
        self._expression_mgr = NSXExpressionManager.get_instance()
        self.http = self._group_mgr.http
        self.debug = self._group_mgr.debug

    def __str__(self):
        return f"NSXGroup(name='{self.name()}'...)"

    def __bool__(self):
        return True if self.data else False

    def name(self) -> str:
        return self.data["display_name"]

    def description(self) -> str:
        return self.data.get("description", "")

    def expression(self) -> dict:
        return self.data.get("expression", "")

    def expression_list(self) -> list[NSXExpression]:
        return [NSXExpression(e) for e in self.expression()]

    def id(self) -> str:
        return self.data.get("id", self.name())

    def path(self) -> str:
        return self.data["path"]

    def tags(self) -> list[dict]:
        return self.data.get("tags", "")

    def dump(self):
        return self.data

    def to_json(self):
        return json.dumps(self.dump())

    def pformat(self):
        return pformat(self.data)

    def has_ip_address(self, ip_address: str) -> bool:
        if ip_address in self.ip_addresses():
            return True
        return False

    def has_owner(self) -> bool:
        for tag in self.tags():
            if tag["scope"] == "owner":
                return True
        return False

    def owner(self) -> str:
        for tag in self.tags():
            if tag["scope"] == "owner":
                return tag["tag"]
        return ""

    def _add_expression(
        self, expression: NSXExpression, operator: Literal["AND", "OR"]
    ):
        if operator == "AND":
            op = self._expression_mgr.AND
        else:
            op = self._expression_mgr.OR
        self.data["expression"].append(op.dump())
        self.data["expression"].append(expression.dump())

    def _multiple_expressions_and_no_ip_address_expression(self) -> bool:
        """
        Returns True (bad) if group contains multiple expressions and none of them
        are IPAddressExpression
        """
        expr_l = self.expression_list()
        if len(expr_l) == 1:
            return False
        missing = True
        for e in expr_l:
            if e.type() == "IPAddressExpression":
                missing = False
        return missing

    def _get_ipaddress_expression(self) -> Union[NSXExpression, None]:
        l = [e for e in self.expression_list() if e._is_ipaddressexpression()]
        if not l:
            return None
        return l[0]

    def _set_ipaddress_expression(self, expression: NSXExpression) -> None:
        """Replaces the existing ipaddress expression with the one we provide"""
        if not expression._is_ipaddressexpression():
            raise NSXGenericError("Invalid expression type for setting ipaddress")
        new_expression_list = []
        for expr in self.expression_list():
            if expr._is_ipaddressexpression():
                # Expression is an IPAddressExpression,
                # which means we need to append our modified version
                # instead of what's there
                if not expression.ip_addresses():
                    # If the new expression has an empty list of addresses
                    # it means that the user removed the last IP address
                    # so we should remove the Expression, as well as the previous
                    # conjunction
                    if new_expression_list: # just in case there is no conjunction
                        new_expression_list.pop()
                else:
                    # This is what happens most of the time,
                    # we just append the new expression in place of the old one
                    new_expression_list.append(expression)
            else:
                # If it's not an IPAddressExpression, just append it
                new_expression_list.append(expr)
        self.data["expression"] = [e.dump() for e in new_expression_list]

    def virtual_machines(self) -> list[NSXVirtualMachine]:
        """
        Returns a list of virtual machines that are members of the group
        """
        endpoint = (
            f"/policy/api/v1/infra/domains/{self.http.domain_id}/groups/{self.id()}/members/virtual-machines"
        )
        return [NSXVirtualMachine(vm) for vm in self.http.request(method="GET", endpoint=endpoint)["results"] if vm]

    def ip_addresses(self) -> list[str]:
        """
        Returns a list of IP Addresses for the group
        """
        endpoint = (
            f"/policy/api/v1/infra/domains/{self.http.domain_id}/groups/{self.id()}/members/ip-addresses"
        )
        return [ipaddr for ipaddr in self.http.request(method="GET", endpoint=endpoint)["results"] if ipaddr]


    def add_ipaddress(self, ipaddress: Union[list[str], str]) -> None:
        """
        Adds an IPAddress/CIDR to existing ip_addresses.
        Creates new expression logic if ip_addresses doesn't exist.
        Fails if complicated expressions are already configured.
        """
        if isinstance(ipaddress, str):
            ipaddress = [ipaddress]

        if self._multiple_expressions_and_no_ip_address_expression():
            raise NSXExpressionsTooComplicatedError(self.name())

        ipaddr_expr = self._get_ipaddress_expression()
        # if no expressions already exist, we add a new one and return early
        if not ipaddr_expr:
            ipaddr_expr = self._expression_mgr.new_ipaddress_expression(ipaddress)
            self._add_expression(ipaddr_expr, "OR")
            self.save()
            return
        # otherwise we add it to the existing expression
        for ipaddr in ipaddress:
            ipaddr_expr.add_ip_address(ipaddr)
        self._set_ipaddress_expression(ipaddr_expr)
        self.save()

    def remove_ipaddress(self, ipaddress: Union[list[str], str]) -> None:
        """
        Removes an IPAddress/CIDR from existing ip_addresses.
        """
        if isinstance(ipaddress, str):
            ipaddress = [ipaddress]

        ipaddr_expr = self._get_ipaddress_expression()
        if not ipaddr_expr:
            raise NSXGenericError("IPAddressExpression not present on group")
        for ipaddr in ipaddress:
            ipaddr_expr.remove_ip_address(ipaddr)
        self._set_ipaddress_expression(ipaddr_expr)
        self.save()

    def clear_ipaddresses(self) -> None:
        """
        Removes all IPAddresses/CIDRs from existing ip_addresses.
        """
        ipaddr_expr = self._get_ipaddress_expression()
        if not ipaddr_expr:
            return
        ipaddr_expr.clear_ipaddresses()
        self._set_ipaddress_expression(ipaddr_expr)
        self.save()

    def add_tag(self, key: str, value: str) -> None:
        """
        Adds a tag to the Group.
        """
        from uonsx.unit.tag import NSXTag
        tag = NSXTag(name=value, scope=key)
        if self.tags():
            self.data["tags"].append(tag.dump())
        else:
            self.data["tags"] = [tag.dump()]
        self.save()

    def remove_tag(self, key: str, value: str) -> None:
        """
        Removes a tag from the Group.
        """
        from uonsx.unit.tag import NSXTag
        from uonsx.error import NSXTagNotFoundError,NSXGroupHasNoTagsError
        tag = NSXTag(name=value, scope=key)
        if not self.tags():
            raise NSXGroupHasNoTagsError(self.name())
        for tag in self.tags():
            if tag["scope"] == key and tag["tag"] == value:
                self.data["tags"].remove(tag)
                self.save()
                return
        raise NSXTagNotFoundError(key, value)

    def save(self) -> bool:
        """
        Save object changes to NSX
        """
        self.debug.print(1, f"saving group: {self.name()}")
        self.debug.print(3, self.pformat())
        endpoint = (
            f"/policy/api/v1/infra/domains/{self.http.domain_id}/groups/{self.id()}"
        )
        return bool(
            self.http.request(method="PATCH", endpoint=endpoint, data=self.dump())
        )

    def check_native(self) -> bool:
        """
        Returns True if all of the following are True:
        - No IP address contains a "/"
        - Number of VMs == Number of IP addresses
        - Each IP address maps to a VM in the group
        """
        group_ipaddrs = sorted(self.ip_addresses())
        for ip in group_ipaddrs:
            if "/" in ip:
                self.debug.print(2, f"ip has a slash, not a native group: '{ip}'")
                return False
        vms = self.virtual_machines()
        if len(group_ipaddrs) != len(vms):
            self.debug.print(2, f"groups ip addresses is not the same length as vms ipaddresses")
            self.debug.print(4, f"group_ipaddrs ({len(group_ipaddrs)}): {group_ipaddrs}")
            self.debug.print(4, f"vms ({len(vms)}): {vms}")
            return False
        for vm in vms:
            vm_ipaddrs = sorted(vm.ip_addresses())
            if not vm_ipaddrs == group_ipaddrs:
                self.debug.print(2, f"vm ipaddrs not matching group ipaddrs")
                self.debug.print(4, f"vm_ipaddrs: {vm_ipaddrs}")
                self.debug.print(4, f"group_ipaddrs: {group_ipaddrs}")
                return False
        return True

    # ---------------------------------------------------------------------------- #
    #                                    audit                                     #
    # ---------------------------------------------------------------------------- #

    def audit_vm_tag_criteria(self) -> bool:
        """
        Returns true if:

        at least one of the expressions is a 'VirtualMachine Tag EQUALS group_name'
        """
        self.debug.print(2, f"checking for valid tag criteria: {self.name()}")
        for e in self.expression_list():
            if e.is_matching_vm_tag(self.name()):
                self.debug.print(2, f"valid tag criteria found")
                return True
        self.debug.print(2, f"valid tag criteria missing")
        return False

    # ---------------------------------------------------------------------------- #
    #                                    output                                    #
    # ---------------------------------------------------------------------------- #

    def output(self, format: Union[Literal["human"], Literal["json"]]) -> str:
        """Returns a string representation of the group object"""
        outlines = []
        if format == "human":
            outlines.append("")
            outlines.append(f"Group Name:   {self.name()}")
            outlines.append(f"Description:  {self.description()}")
            outlines.append(self.condition_table())
            outlines.append(self.conjunction_table())
            outlines.append(self.ipaddress_table())
        if format == "json":
            data = json.dumps(
                {
                    "name": self.name(),
                    "description": self.description(),
                    "expression_list": self.expression_data(),
                }
            )
            outlines.append(data)
        return "\n".join(outlines)

    def condition_table(self):
        headers = ["member_type", "key", "operator", "value"]
        data = []
        for e in self.expression_list():
            if e.type() == "Condition":
                data.append([e.member_type(), e.key(), e.operator(), e.value()])
        if not data:
            return ""
        return format_table(headers, data)

    def conjunction_table(self):
        headers = ["conjunction"]
        data = []
        for e in self.expression_list():
            if e.type() == "ConjunctionOperator":
                data.append([e.conjunction_operator()])
        if not data:
            return ""
        return format_table(headers, data)

    def ipaddress_table(self):
        headers = ["ip_addresses"]
        data = []
        for e in self.expression_list():
            if e.type() == "IPAddressExpression":
                for i in e.ip_addresses():
                    data.append([i])
        if not data:
            return ""
        return format_table(headers, data)

    def expression_data(self) -> list[str]:
        out = []
        for e in self.expression_list():
            d = None
            if e.type() == "Condition":
                d = {
                    "member_type": e.member_type(),
                    "key": e.key(),
                    "operator": e.operator(),
                    "value": e.value(),
                }
            if e.type() == "ConjunctionOperator":
                d = {"conjunction_operator": e.conjunction_operator()}
            if e.type() == "IPAddressExpression":
                d = {
                    "ip_addresses": e.ip_addresses(),
                }
            if d is not None:
                out.append(d)
        return out
