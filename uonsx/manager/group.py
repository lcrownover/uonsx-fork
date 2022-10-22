from __future__ import annotations

import json
from pprint import pformat
from typing import Union

from typing_extensions import Literal
from uonsx.config import NSXConfig
from uonsx.error import (
    NSXExpressionListConjunctionError,
    NSXGroupAlreadyExistsError,
    NSXGroupNotFoundError,
    NSXGroupPathNotFoundError,
    NSXInvalidGroupError,
    NSXInvalidOutputFormatError,
)
from uonsx.http import HTTP
from uonsx.manager.expression import NSXExpressionManager
from uonsx.unit.expression import NSXExpression
from uonsx.unit.group import NSXGroup
from uonsx.util import cleanse_display_name, format_table


class NSXGroupManager:
    """Manager class for NSX Security Groups"""

    __instance = None
    __data_needs_refresh = True

    @staticmethod
    def get_instance():
        if NSXGroupManager.__instance == None:
            raise Exception("NSXGroupManager is not initialized")
        return NSXGroupManager.__instance

    def __init__(self, cfg: NSXConfig):
        if NSXGroupManager.__instance != None:
            raise Exception("use the get_instance() method to use the NSXGroupManager")
        self.debug = cfg.debug
        self.cfg = cfg
        self.debug.print(2, "initializing group manager")
        self.http = HTTP.get_instance()
        self.data = []
        self._expression_manager = NSXExpressionManager.get_instance()
        NSXGroupManager.__instance = self
        self.debug.print(2, "group manager initialized")

    def _set_refresh(self, flag: bool = True) -> None:
        self.__data_needs_refresh = flag

    def _refresh_data(self, force: bool = False):
        if self.__data_needs_refresh or force:
            all_groups = self.load_all()
            self.data = all_groups
            self.__data_needs_refresh = False

    def _looks_like_ip(self, source: str) -> bool:
        if source[0].isdigit() and "." in source:
            return True
        return False

    def get_by_path(self, path: str) -> NSXGroup:
        self._refresh_data()
        for item in self.data:
            if item.path() == path:
                return item
        # Path is a /group/path but not found in known groups
        if path.startswith("/"):
            raise NSXGroupPathNotFoundError(path)
        # Path is a CIDR or something
        raise NSXInvalidGroupError(path)

    def _get_id(self, name: str) -> str:
        for item in self.data:
            if item.name() == name:
                return item.id()
        raise NSXGroupNotFoundError(name)

    def _validate_group_not_exists(self, name: str) -> None:
        self._refresh_data()
        for g in self.data:
            if g.name() == name:
                raise NSXGroupAlreadyExistsError(name)

    def load_all(self) -> list[NSXGroup]:
        """Query the API and return a list of all instances of NSXGroup"""
        self.debug.print(1, f"loading all: group")

        endpoint = f"{self.http.base_endpoint}/groups"

        resp = self.http.request(method="GET", endpoint=endpoint)
        resp_items = resp["results"]

        all_groups = [NSXGroup(i) for i in resp_items]

        return all_groups

    def get(self, name: str) -> NSXGroup:
        """Query the API and return an instance of NSXGroup"""
        self._refresh_data()
        self.debug.print(1, f"getting group: {name}")

        if self._looks_like_ip(name):
            # This means it's an IP or CIDR, just return it...
            return name

        # unlike policies, groups are fully-loaded when using `get_all()`
        group = None
        for g in self.data:
            if g.name() == name:
                group = g

        if not group:
            raise NSXGroupNotFoundError(name)

        return group

    def get_all(self) -> list[NSXGroup]:
        """the API and return a list of all instances of NSXGroup"""
        self._refresh_data()
        self.debug.print(1, f"getting all: group")
        return self.data

    def create(
        self,
        name: str,
        description: str = "",
        expression: Union[NSXExpression, list[NSXExpression]] = None,
    ) -> NSXGroup:
        """
        Create a new NSX Group.

        Parameters
        ----------
        name: str
            Name of the group to create. Make sure you're following the naming convention.
        description: str, optional
            Description for the group.
        expression: Union[NSXExpression, list[NSXExpression]], optional
            If no expression is provided, it will use a single expression with tag name matching group name.
            One or many NSXExpression objects obtained with the `nsx.expression.new()` method.
            If more than one expression is passed as a list, each expression needs to be separated with an `nsx.expression.AND` or `nsx.expression.OR` object.
            Example: nsx.group.create(name="nts-nms", expression=[first_expr, nsx.expression.AND, second_expr])

        Returns
        -------
        NSXExpression that contains everything you need to feed it to the `nsx.group.create` method.
        """

        self._refresh_data()
        self.debug.print(1, f"creating group: {name}")
        self._validate_group_not_exists(name)
        data = {}
        data["display_name"] = name
        data["id"] = cleanse_display_name(name)
        if description:
            data["description"] = description
        if not expression:
            data["expression"] = [self._expression_manager.tag(name=name).dump()]
        else:
            data["expression"] = self._expand_expression(expression)
        group = NSXGroup(data)
        group = self._api_create(group)
        self._set_refresh()
        return group

    def delete(self, name: str) -> bool:
        """Destroy an existing NSX Group"""
        self._refresh_data()
        self.debug.print(1, f"deleting group: {name}")

        group = self.get(name=name)

        self._api_delete(group)
        self._set_refresh()
        return True

    def _validate_expression_list(self, expression_list: list[NSXExpression]) -> None:
        for i, v in enumerate(expression_list):
            if i % 2 != 0:  # odd indexes
                if v.dump().get("resource_type", None) != "ConjunctionOperator":
                    raise NSXExpressionListConjunctionError

    def _expand_expression(self, expression: Union[NSXExpression, list[NSXExpression]]):
        """Takes a single NSXExpression, list of NSXExpression, or None and expands to the correct data for the API"""
        if isinstance(expression, list):
            self._validate_expression_list(expression)
            return [expr.dump() for expr in expression]
        return [expression.dump()]

    def _api_create(self, group: NSXGroup) -> NSXGroup:
        """Private method to create the group using the API"""
        self.debug.print(3, pformat(group.dump()))
        endpoint = f"{self.http.base_endpoint}/groups/{group.id()}"
        try:
            data = self.http.request(method="PUT", endpoint=endpoint, data=group.dump())
        except NSXGroupAlreadyExistsError as e:
            raise
        return NSXGroup(data)

    def _api_delete(self, group: NSXGroup) -> None:
        """Private method to delete the group using the API"""
        self.debug.print(3, pformat(group.dump()))
        endpoint = f"{self.http.base_endpoint}/groups/{group.id()}"
        # group exists:
        self.http.request(method="DELETE", endpoint=endpoint, data=group.dump())

    # ---------------------------------------------------------------------------- #
    #                                    output                                    #
    # ---------------------------------------------------------------------------- #

    def output(self, format: Union[Literal["human"], Literal["json"]]) -> str:
        """Returns a string output representation of all groups"""
        if format == "human":
            return self.all_groups_table()
        if format == "json":
            return self.all_groups_json()
        raise NSXInvalidOutputFormatError(format)

    def all_groups_table(self):
        headers = ["name"]
        data = []
        for group in self.get_all():
            d = [
                group.name(),
            ]
            data.append(d)

        return format_table(headers, data)

    def all_groups_json(self) -> str:
        return json.dumps([g.name() for g in self.get_all()])

    # ---------------------------------------------------------------------------- #
    #                                    audit                                     #
    # ---------------------------------------------------------------------------- #

    def audit_duplicates(self) -> list[str]:
        """Returns a list of group names with duplicate display names"""
        self._refresh_data()
        self.debug.print(1, f"auditing duplicate groups")
        # compare the list of group names against the unique list of group names
        # and return empty list if length is the same
        if len([g.name() for g in self.data]) == len(
            list(set([g.name() for g in self.data]))
        ):
            return []
        issues = []
        seen = []
        for group in self.data:
            if group.name() in self.cfg.audit.ignored_groups:
                self.debug.print(
                    1, f"ignoring group due to configuration: {group.name()}"
                )
                continue
            if group.name() not in seen:
                seen.append(group.name())
                continue
            issues.append(group.name())
        return issues

    def _has_valid_suffix(self, group_name: str) -> bool:
        """Returns True if the group display name has the vrf suffix"""
        for valid_vrf in self.cfg.audit.valid_vrfs:
            self.debug.print(3, f"validating against vrf: {valid_vrf}")
            if group_name.endswith(valid_vrf):
                self.debug.print(1, f"valid suffix for group: {group_name}")
                return True
        self.debug.print(1, f"invalid suffix for group: {group_name}")
        return False

    def _has_valid_prefix(self, group_name: str) -> bool:
        """Returns True if the group display name has a valid prefix"""
        for valid_prefix in self.cfg.audit.valid_prefixes:
            self.debug.print(3, f"validating against prefix: {valid_prefix}")
            if group_name.startswith(f"{valid_prefix}_"):
                self.debug.print(1, f"valid prefix for group: {group_name}")
                return True
        self.debug.print(1, f"invalid prefix for group: {group_name}")
        return False

    def audit_name(self, group_name: str) -> bool:
        """Returns True if the group display name matches our naming convention"""
        self.debug.print(1, f"validating: {group_name}")
        if not self._has_valid_prefix(group_name):
            return False
        if not self._has_valid_suffix(group_name):
            return False
        return True

    def audit_naming_convention(self) -> list[str]:
        """Returns a list of group names that don't follow the naming convention"""
        self._refresh_data()
        self.debug.print(1, f"auditing naming conventions for all groups")
        issues = []
        for group in self.data:
            if group.name() in self.cfg.audit.ignored_groups:
                self.debug.print(
                    1, f"ignoring group due to configuration: {group.name()}"
                )
                continue
            if not self.audit_name(group.name()):
                issues.append(group.name())
        return issues

    def audit_required_criteria(self) -> list[str]:
        """Returns a list of group names that don't have an associated tag criteria"""
        self._refresh_data()
        self.debug.print(1, f"auditing tag criteria for all groups")
        issues = []
        for group in self.data:
            if group.name() in self.cfg.audit.ignored_groups:
                self.debug.print(
                    1, f"ignoring group due to configuration: {group.name()}"
                )
                continue
            if not group.audit_vm_tag_criteria():
                issues.append(group.name())
        return issues
