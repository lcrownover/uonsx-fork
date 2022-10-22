from __future__ import annotations

import json
from typing import Union

from uonsx.error import NSXExpressionIPAddressNotFoundError, NSXGenericError


class NSXExpression:
    """Wrapper for an NSX Expression"""

    def __init__(self, data: dict):
        from uonsx.manager.expression import NSXExpressionManager

        self.data = data
        self._expression_manager = NSXExpressionManager.get_instance()
        self.debug = self._expression_manager.debug

    def __bool__(self) -> bool:
        return True if self.data else False

    def type(self) -> str:
        return self.data["resource_type"]

    def member_type(self) -> str:
        return self.data.get("member_type", "")

    def key(self) -> str:
        return self.data.get("key", "")

    def operator(self) -> str:
        return self.data.get("operator", "")

    def conjunction_operator(self) -> str:
        return self.data.get("conjunction_operator", "")

    def value(self) -> str:
        return self.data.get("value", "")

    def ip_addresses(self) -> list[str]:
        return self.data.get("ip_addresses", [])

    def _is_ipaddressexpression(self) -> bool:
        if self.type() == "IPAddressExpression":
            return True
        return False

    def _is_conditionexpression(self) -> bool:
        if self.type() == "Condition":
            return True
        return False

    def add_ip_address(self, ipaddress: Union[list[str], str]):
        if not self.type() == "IPAddressExpression":
            raise NSXGenericError(
                f"Tried to add an ip address when expression type was not 'IPAddressExpression'"
            )
        if isinstance(ipaddress, str):
            ipaddress = [ipaddress]
        for ipaddr in ipaddress:
            self.data["ip_addresses"].append(ipaddr)

    def remove_ip_address(self, ipaddress: Union[list[str], str]):
        if not self.type() == "IPAddressExpression":
            raise NSXGenericError(
                f"Tried to add an ip address when expression type was not 'IPAddressExpression'"
            )
        if isinstance(ipaddress, str):
            ipaddress = [ipaddress]
        for ipaddr in ipaddress:
            try:
                self.data["ip_addresses"].remove(ipaddr)
            except:
                raise NSXExpressionIPAddressNotFoundError(ipaddr)

    def clear_ipaddresses(self):
        if not self.type() == "IPAddressExpression":
            raise NSXGenericError(
                f"Tried to remove ip addresses when expression type was not 'IPAddressExpression'"
            )
        self.data["ip_addresses"] = []

    def tag_name(self) -> str:
        """
        Returns the tag name stripped away from the scope

        Beware, I have not handled this function call if the value is not assocated with a Tag key.
        """
        if not self.value():
            return ""
        if "|" in self.value():
            return self.value().split("|")[1].strip()
        return self.value()

    def tag_scope(self) -> str:
        """
        Returns the tag scope stripped away from the name

        Beware, I have not handled this function call if the value is not assocated with a Tag key.
        """
        return self.value().split("|")[0].strip()

    def dump(self) -> dict:
        return self.data

    def to_json(self) -> str:
        return json.dumps(self.dump())

    def is_matching_vm_tag(self, name: str) -> bool:
        """Returns true if the expression is 'VM Tag EQUALS name'"""
        if self.type() != "Condition":
            self.debug.print(
                2, f"resource type '{self.type()}' does not match 'Condition'"
            )
            return False
        if not self.member_type() == "VirtualMachine":
            self.debug.print(
                2, f"member type '{self.member_type()}' does not match 'VirtualMachine'"
            )
            return False
        if not self.key() == "Tag":
            self.debug.print(2, f"key '{self.key()}' does not match 'Tag'")
            return False
        if not self.operator() == "EQUALS":
            self.debug.print(2, f"operator '{self.operator()}' does not match 'EQUALS'")
            return False
        if not self.tag_name() == name:
            self.debug.print(
                2, f"tag name '{self.tag_name()}' does not match group name '{name}'"
            )
            return False
        return True

    @classmethod
    def to_condition_str(cls, expression: dict) -> str:
        value = expression["value"]
        if value.startswith("|"):
            value = value[1:]
        return "{} {} {} {}".format(
            expression["member_type"],
            expression["key"],
            expression["operator"],
            value,
        )
