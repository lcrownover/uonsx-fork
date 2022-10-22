from __future__ import annotations

import json
from typing import Union

from typing_extensions import Literal
from uonsx.config import NSXConfig
from uonsx.error import (
    NSXInvalidOutputFormatError,
    NSXInvalidPolicyCategoryError,
    NSXPolicyAlreadyExistsError,
    NSXPolicyCreationFailedError,
    NSXPolicyNotFoundError,
    NSXInvalidPolicyCategoryError,
)
from uonsx.http import HTTP
from uonsx.unit.group import NSXGroup
from uonsx.unit.policy import NSXPolicy
from uonsx.util import (
    cleanse_display_name,
    format_table,
    get_policy_id_from_path,
    get_rule_id_from_path,
)


class NSXPolicyManager:

    __instance = None
    __data_needs_refresh = True

    @staticmethod
    def get_instance():
        if NSXPolicyManager.__instance == None:
            raise Exception("NSXPolicyManager is not initialized")
        return NSXPolicyManager.__instance

    def __init__(self, cfg: NSXConfig):
        if NSXPolicyManager.__instance != None:
            raise Exception("use the get_instance() method to use the NSXPolicyManager")
        self.cfg = cfg
        self.debug = cfg.debug
        self.data = []
        self._highest_sequence_number = None
        self.debug.print(2, "initializing policy manager")
        self.http = HTTP.get_instance()
        NSXPolicyManager.__instance = self
        self.debug.print(2, "policy manager initialized")

    def _set_refresh(self, flag: bool = True) -> None:
        self.__data_needs_refresh = flag

    def _refresh_data(self, force: bool = False) -> None:
        if self.__data_needs_refresh or force:
            all_policies = self.load_all()
            self.data = all_policies
            self.__data_needs_refresh = False

    def _get_id(self, name: str) -> str:
        self._refresh_data()
        self.debug.print(2, f"getting id for policy name: {name}")
        for item in self.data:
            if item.name() == name:
                self.debug.print(2, f"found id for policy name: {name}")
                return item.id()
        self.debug.print(2, f"did not find id for policy name: {name}")
        raise NSXPolicyNotFoundError(name)

    def _get_by_id(self, id: str) -> NSXPolicy:
        self._refresh_data()
        self.debug.print(2, f"getting policy from id: {id}")
        for policy in self.data:
            if policy.id() == id:
                return policy
        self.debug.print(2, f"did not find policy for id: {id}")
        raise NSXPolicyNotFoundError(id)

    def _get_highest_sequence_number(self) -> int:
        """Returns the highest sequence number among all policies"""
        if self._highest_sequence_number:
            return self._highest_sequence_number
        self._refresh_data()
        highest = 0
        for policy in self.data:
            if policy.sequence_number() > highest:
                highest = policy.sequence_number()
        highest = highest
        self._highest_sequence_number = highest
        return highest

    def next_sequence_number(self, padding: int = 20) -> int:
        """Returns the next sequence number if you want to append a policy to the list"""
        return self._get_highest_sequence_number() + padding

    def _validate_policy_not_exists(self, name: str) -> None:
        self._refresh_data()
        for p in self.data:
            if p.name() == name:
                raise NSXPolicyAlreadyExistsError(name)

    def _validate_valid_category(self, category: str) -> None:
        valid_categories = [
            "Ethernet",
            "Emergency",
            "Infrastructure",
            "Environment",
            "Application",
        ]
        if category not in valid_categories:
            raise NSXInvalidPolicyCategoryError(category, valid_categories)

    def load_all(self) -> list[NSXPolicy]:
        """
        Query the API and return a list of all instances of NSXPolicy
        """
        self.debug.print(1, f"loading all: policy")

        ignored_policies = ["Default Layer2 Section", "Default Layer3 Section"]

        endpoint = f"{self.http.base_endpoint}/security-policies"

        resp = self.http.request(method="GET", endpoint=endpoint)
        resp_items = resp["results"]

        policies = [
            NSXPolicy(i)
            for i in resp_items
            if NSXPolicy(i).name() not in ignored_policies
        ]

        return policies

    def get(self, name: str) -> NSXPolicy:
        """
        Query the API and return an instance of NSXPolicy
        """
        self._refresh_data()
        self.debug.print(1, f"getting policy: {name}")

        id = self._get_id(name=name)
        if not id:
            self.debug.print(1, "policy not found")
            raise NSXPolicyNotFoundError(name)

        endpoint = f"{self.http.base_endpoint}/security-policies/{id}"

        policy_data = self.http.request(method="GET", endpoint=endpoint)

        if policy_data:
            return NSXPolicy(policy_data)

        raise NSXPolicyNotFoundError(name)

    def get_all(self) -> list[NSXPolicy]:
        """
        Get all instances of NSXPolicy from data
        """

        self._refresh_data()
        self.debug.print(1, f"getting all: policy")
        return self.data

    def create(
        self,
        name: str,
        destination_group: NSXGroup,
        description: str = "",
        sequence_number: int = None,
        category: str = "Application",
    ) -> NSXPolicy:
        """
        Create a new NSX Policy
        """

        self._refresh_data()
        self.debug.print(1, f"creating policy:  {name}")
        self._validate_policy_not_exists(name)
        self._validate_valid_category(category)

        data = {}
        data["display_name"] = name
        safe_id = cleanse_display_name(name)
        data["id"] = safe_id
        data["category"] = category
        data["scope"] = ["ANY"]  # Policy Scope overrides Rule scope, always "ANY"
        data["sequence_number"] = self.next_sequence_number()
        if sequence_number:
            data["sequence_number"] = sequence_number
        if description:
            data["description"] = description

        endpoint = f"{self.http.base_endpoint}/security-policies/{safe_id}"
        data = self.http.request(method="PUT", endpoint=endpoint, data=data)

        self._set_refresh()

        if not data:
            raise NSXPolicyCreationFailedError(name)

        policy = NSXPolicy(data)
        policy.set_destination_group(destination_group)
        return policy

    def delete(self, name: str) -> bool:
        """Delete an existing NSX Policy"""

        self._refresh_data()
        self.debug.print(1, f"deleting policy: {name}")

        id = self._get_id(name=name)

        endpoint = f"{self.http.base_endpoint}/security-policies/{id}"

        self.http.request(method="DELETE", endpoint=endpoint)

        self._set_refresh()
        return True

    def remove_rule_by_path(self, path: str) -> bool:
        """Removes a rule from a policy, given a valid NSX object path"""
        policy_id = get_policy_id_from_path(path)
        policy = self._get_by_id(policy_id)
        policy._reload()  # loads the rules
        rule_id = get_rule_id_from_path(path)
        rule = policy._get_rule_by_id(rule_id)
        policy.remove_rule(handle=rule.handle())
        return True

    # ---------------------------------------------------------------------------- #
    #                                    output                                    #
    # ---------------------------------------------------------------------------- #

    def output(self, format: Union[Literal["human"], Literal["json"]]) -> str:
        """Returns a string of output designed to be printed by Click depending on the format"""
        if format == "human":
            return self.all_policies_human()
        if format == "json":
            return self.all_policies_json()
        raise NSXInvalidOutputFormatError(format)

    def all_policies_human(self):
        headers = ["name"]
        data = []
        for policy in self.get_all():
            d = [
                policy.name(),
            ]
            data.append(d)

        return format_table(headers, data)

    def all_policies_json(self):
        return json.dumps([p.name() for p in self.get_all()])

    # ---------------------------------------------------------------------------- #
    #                                    audit                                     #
    # ---------------------------------------------------------------------------- #

    def audit_duplicates(self) -> list[str]:
        """Returns a list of policy names with duplicate display names"""
        self._refresh_data()
        self.debug.print(1, f"auditing duplicate policies")
        # compare the list of policy names against the unique list of policy names
        # and return empty list if length is the same
        if len([p.name() for p in self.data]) == len(
            list(set([p.name() for p in self.data]))
        ):
            return []
        issues = []
        seen = []
        for policy in self.data:
            if policy.name() in self.cfg.audit.ignored_policies:
                self.debug.print(
                    1, f"ignoring policy due to configuration: {policy.name()}"
                )
                continue
            if policy.name() not in seen:
                seen.append(policy.name())
                continue
            issues.append(policy.name())
        return issues

    def _has_valid_suffix(self, policy_name: str) -> bool:
        """Returns True if the policy display name has the vrf suffix"""
        for valid_vrf in self.cfg.audit.valid_vrfs:
            self.debug.print(3, f"validating against vrf: {valid_vrf}")
            if policy_name.endswith(valid_vrf):
                self.debug.print(1, f"valid suffix for policy: {policy_name}")
                return True
        self.debug.print(1, f"invalid suffix for policy: {policy_name}")
        return False

    def _has_valid_prefix(self, policy_name: str) -> bool:
        """Returns True if the policy display name has a valid prefix"""
        for valid_prefix in self.cfg.audit.valid_prefixes:
            self.debug.print(3, f"validating against prefix: {valid_prefix}")
            if policy_name.startswith(f"{valid_prefix}_"):
                self.debug.print(1, f"valid prefix for policy: {policy_name}")
                return True
        self.debug.print(1, f"invalid prefix for policy: {policy_name}")
        return False

    def audit_name(self, policy_name: str) -> bool:
        """Returns True if the policy display name matches our naming convention"""
        self.debug.print(1, f"validating: {policy_name}")
        if not self._has_valid_prefix(policy_name):
            return False
        if not self._has_valid_suffix(policy_name):
            return False
        return True

    def audit_naming_convention(self) -> list[str]:
        """Returns a list of policy names that don't follow the naming convention"""
        self._refresh_data()
        self.debug.print(1, f"auditing naming conventions for all policies")
        issues = []
        for policy in self.data:
            if policy.name() in self.cfg.audit.ignored_policies:
                self.debug.print(
                    1, f"ignoring policy due to configuration: {policy.name()}"
                )
                continue
            if not self.audit_name(policy.name()):
                issues.append(policy.name())
        return issues

    def audit_rule_destinations(self) -> list[dict[str, list[dict[str, str]]]]:
        """Returns a dict of policy names and invalid rules where any rule in that policy has an invalid destination"""
        self._refresh_data()
        self.debug.print(1, f"auditing rule destinations for all policies")
        issues = []
        for policy in self.data:
            if policy.name() in self.cfg.audit.ignored_policies:
                self.debug.print(
                    1, f"ignoring policy due to configuration: {policy.name()}"
                )
                continue
            invalid_rule_report = {"policy_name": policy.name(), "invalid_rules": []}
            for rule in policy.audit_invalid_rule_destinations():
                invalid_rule_report["invalid_rules"].append(rule)
            if invalid_rule_report["invalid_rules"]:
                issues.append(invalid_rule_report)
        return issues
