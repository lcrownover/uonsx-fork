from __future__ import annotations

import json

from uonsx.config import NSXConfig
from uonsx.error import (
    NSXExpressionComponentNotFoundError,
    NSXExpressionValueEmptyError,
    NSXInvalidIPAddressError,
)
from uonsx.http import HTTP
from uonsx.unit.expression import NSXExpression


class NSXExpressionManager:
    """Manager class for NSX Expressions"""

    __instance = None

    @staticmethod
    def get_instance():
        if NSXExpressionManager.__instance == None:
            raise Exception("NSXExpressionManager is not initialized")
        return NSXExpressionManager.__instance

    def __init__(self, cfg: NSXConfig):
        if NSXExpressionManager.__instance != None:
            raise Exception(
                "use the get_instance() method to use the NSXExpressionManager"
            )
        self.debug = cfg.debug
        self.debug.print(2, "initializing expression manager")
        self.http = HTTP.get_instance()
        self.valid_member_types = [
            "IPSet",
            "VirtualMachine",
            "LogicalPort",
            "LogicalSwitch",
            "Segment",
            "SegmentPort",
        ]
        self.valid_keys = ["Tag", "Name", "OSName", "ComputerName"]
        self.valid_operators = [
            "EQUALS",
            "CONTAINS",
            "STARTSWITH",
            "ENDSWITH",
            "NOTEQUALS",
        ]
        NSXExpressionManager.__instance = self
        self.AND = self.and_conjunction()
        self.OR = self.or_conjunction()
        self.debug.print(2, "expression manager initialized")

    def and_conjunction(self) -> NSXExpression:
        return NSXExpression(
            {"conjunction_operator": "AND", "resource_type": "ConjunctionOperator"}
        )

    def or_conjunction(self) -> NSXExpression:
        return NSXExpression(
            {"conjunction_operator": "OR", "resource_type": "ConjunctionOperator"}
        )

    def _ignore_case_get(self, value: str, valid: list[str]):
        """Returns the element from valid, matching value case-insensitively"""
        for v in valid:
            if value.lower() == v.lower():
                return v
        return None

    def _validate_component(self, component: str, valid_components: list[str]) -> str:
        verified_component = self._ignore_case_get(component, valid_components)
        if verified_component:
            return verified_component
        raise NSXExpressionComponentNotFoundError(component, valid_components)

    def _validate_value(self, value: str) -> str:
        """
        Used to validate the contents of the value property

        value should be two strings separated by a bar "|", the first string
        being the scope, and the second being the tag name
        I suppose it's actually fine to omit the scope, so we won't check for it,
        in case the user wants to force a scopeless tag
        """
        if value:
            return value

        raise NSXExpressionValueEmptyError(value)

    def _validate_ipaddress(self, ipaddress: str) -> str:
        """
        Returns a validated ip address/cidr string

        Raises NSXInvalidIPAddressError if invalid data provided
        """
        # TODO(lcrown): validate ip address data
        valid = True
        if not valid:
            raise NSXInvalidIPAddressError(ipaddress)
        return ipaddress

    def tag(self, name: str, scope: str = None) -> NSXExpression:
        """
        Shortcut for the `new_condition` method.

        This method assumes you want the following logic:
        new(member_type="VirtualMachine", key="Tag", operator="EQUALS", value=<tag>, scope=<scope>)
        """

        return self.new_condition(
            member_type="VirtualMachine",
            key="Tag",
            operator="EQUALS",
            value=name,
            scope=scope,
        )

    def new_condition(
        self, member_type: str, key: str, operator: str, value: str, scope: str = None
    ):
        """
        Create a new Condition expression object to be used with `nsx.group.create`

        Example [Any Virtual Machine tagged with the "is-managed" Tag]:
        new(member_type="VirtualMachine", key="Tag", operator="EQUALS", value="is-managed")

        Shorter example using the `tag` shortcut method:
        tag("is-managed")

        Parameters
        ----------
        member_type: str
            Type of NSX Component. Almost always "VirtualMachine".
            Valid options: [ IPSet, VirtualMachine, LogicalPort, LogicalSwitch, Segment, SegmentPort ]
        key: str
            Type of key.
            Valid options: [ Tag, Name, OSName, ComputerName ]
        operator: str
            Logic operator for this expression. Usually "EQUALS".
            Valid options: [ EQUALS, CONTAINS, STARTSWITH, ENDSWITH, NOTEQUALS ]
        value: str
            Value of the expression. Usually Tag name, or Virtual Machine name if using ComputerName key.
        scope: str, optional
            Adding scope will make the key {scope: value} instead of an unscoped value.

        Returns
        -------
        NSXExpression that contains everything you need to feed it to the `nsx.group.create` method.
        """

        if scope:
            value = f"{scope}|{value}"
        data = {}
        data["member_type"] = self._validate_component(
            member_type, self.valid_member_types
        )
        data["key"] = self._validate_component(key, self.valid_keys)
        data["operator"] = self._validate_component(operator, self.valid_operators)
        data["value"] = self._validate_value(value)
        data["resource_type"] = "Condition"
        expression = NSXExpression(data)
        return expression

    def new_ipaddress_expression(self, ip_address_list: list[str] = []):
        """
        Create a new IPAddressExpression object

        Usage:
        ip_addresses(ip_address_list=["10.0.0.0/24", "192.168.0.1"])

        Parameters
        ----------
        ip_address_list: str
            List of IP addresses/CIDR ranges to add to the group

        Returns
        -------
        NSXExpression that dumps to a valid IPAddressExpression
        """

        data = {}
        data["resource_type"] = "IPAddressExpression"
        data["ip_addresses"] = []
        for ip in ip_address_list:
            data["ip_addresses"].append(self._validate_ipaddress(ip))
        expression = NSXExpression(data)
        return expression
