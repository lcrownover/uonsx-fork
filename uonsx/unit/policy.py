from __future__ import annotations

import json
from pprint import pformat, pprint
from typing import Union

from typing_extensions import Literal
from uonsx.error import (
    NSXDestinationNotFoundError,
    NSXInvalidGroupError,
    NSXInvalidOutputFormatError,
    NSXPolicyScopeNotFoundError,
    NSXRuleNotFoundError,
    NSXRuleValidationError,
)
from uonsx.unit.group import NSXGroup
from uonsx.unit.rule import NSXRule
from uonsx.unit.service import NSXService
from uonsx.util import cleanse_display_name, format_table


class NSXPolicy:
    """
    Wrapper/Constructor for NSX Policies

    example:
    {
        "description": "comm map",
        "display_name": "application-section-1",
        "category": "Application",
        "rules": [
          {
            "description": " comm entry",
            "display_name": "ce-1",
            "sequence_number": 1,
            "source_groups": [
              "/infra/domains/vmc/groups/dbgroup"
            ],
            "destination_groups": [
              "/infra/domains/vmc/groups/appgroup"
            ],
            "services": [
              "/infra/services/HTTP",
              "/infra/services/CIM-HTTP"
            ],
            "action": "ALLOW"
          }

        ]
    }
    """

    def __init__(self, data: dict):
        from uonsx.manager.group import NSXGroupManager
        from uonsx.manager.policy import NSXPolicyManager
        from uonsx.manager.service import NSXServiceManager

        self.data = data
        self._policy_manager = NSXPolicyManager.get_instance()
        self._service_manager = NSXServiceManager.get_instance()
        self._group_manager = NSXGroupManager.get_instance()
        self.debug = self._policy_manager.debug
        self.http = self._policy_manager.http

    def __repr__(self) -> str:
        return json.dumps(self.data)

    def __str__(self) -> str:
        return json.dumps(self.data)

    def _reload_rules(self) -> None:
        self.data["rules"] = [
            rule.dump()
            for rule in sorted(self._policy_manager.get(self.name()).rules())
        ]
        self.data["rule_count"] = len(self.rules())

    def _reload(self) -> None:
        self._policy_manager.__data_needs_refresh = True
        policy = self._policy_manager.get(self.name())
        self.__init__(policy.dump())

    def dump(self) -> dict:
        return self.data

    def to_json(self) -> str:
        return json.dumps(self.dump())

    def pformat(self) -> str:
        return pformat(self.dump())

    def name(self) -> str:
        return self.data["display_name"]

    def description(self) -> str:
        return self.data.get("description", "")

    def category(self) -> str:
        return self.data.get("category", "")

    def id(self) -> str:
        return self.data["id"]

    def sequence_number(self) -> int:
        return int(self.data["sequence_number"])

    def scope(self) -> list[str]:
        scope = self.data.get("scope", None)
        if not scope:
            raise NSXPolicyScopeNotFoundError(self)
        return scope

    def _add_rule(self, rule: NSXRule) -> None:
        if not self.data.get("rules"):
            self.data["rules"] = []
        self.data["rules"].append(rule.dump())
        self.update_rule_count()

    def _remove_rule(self, rule: NSXRule) -> None:
        endpoint = f"/policy/api/v1/infra/domains/{self.http.domain_id}/security-policies/{self.id()}/rules/{rule.id()}"
        self.http.request(method="DELETE", endpoint=endpoint)
        self._policy_manager.__data_needs_refresh = True
        self._reload()

    def _get_rule_by_id(self, id: str) -> NSXRule:
        endpoint = f"/policy/api/v1/infra/domains/{self.http.domain_id}/security-policies/{self.id()}/rules/{id}"
        try:
            resp = self.http.request(method="GET", endpoint=endpoint)
            return NSXRule(resp)
        except:
            raise

    def rule_count(self) -> int:
        return self.data.get("rule_count", 0)

    def rules(self) -> list[NSXRule]:
        if self.data.get("rules"):
            return [
                NSXRule(r)
                for r in sorted(self.data["rules"], key=lambda d: d["sequence_number"])
            ]
        return []

    def set_rules(self, rules: list[NSXRule]) -> None:
        self.data["rules"] = [r.dump() for r in rules]

    def show_rules(
        self, format: Literal["default", "json", "pretty"] = "default"
    ) -> None:
        if format == "json":
            print(json.dumps(self.data["rules"]))
        if format == "pretty":
            pprint(self.data["rules"])
        else:
            print(self.rules())

    def update_rule_count(self) -> None:
        self.data["rule_count"] = len(self.rules())

    def set_destination_group(self, group: NSXGroup) -> None:
        self._destination_group = group

    def resequence_rules(self, padding: int = 10) -> None:
        """
        This evenly resequences the rules while maintaining rule order.
        """
        n = 10
        new_rules = []
        for rule in sorted(self.rules()):
            rule.set_sequence_number(n)
            new_rules.append(rule)
            n += padding
        self.set_rules(new_rules)

    def _get_sequence_number_before_handle(self, handle: int, padding: int = 2) -> int:
        """Returns the correct sequence number to use on a rule that is before the rule with the given handle."""
        for rule in self.rules():
            if rule.handle() == handle:
                return rule.sequence_number() - padding
        raise NSXRuleNotFoundError(handle)

    def _get_sequence_number_after_handle(self, handle: int, padding: int = 2) -> int:
        """Returns the correct sequence number to use on a rule that is after the rule with the given handle."""
        for rule in self.rules():
            if rule.handle() == handle:
                return rule.sequence_number() + padding
        raise NSXRuleNotFoundError(handle)

    def _get_next_rule_sequence_number(self, padding: int = 10) -> int:
        highest_num = 0
        for rule in self.rules():
            n = rule.sequence_number()
            if n > highest_num:
                highest_num = n
        return highest_num + padding

    def _logged_handler(self, logged: bool) -> bool:
        """Handles the logged parameter"""
        return bool(logged)

    def _rule_sequence_number_handler(self, sequence_number: Union[int, None]) -> int:
        """Handles the sequence number provided"""
        if not sequence_number:
            return self._get_next_rule_sequence_number()
        return int(sequence_number)

    def _scope_handler(
        self,
        source_groups: list[str],
        destination_groups: list[str],
    ) -> list[str]:
        """
        source_groups and destination_groups will come in as a list of group paths

        if "ANY" is in either of the lists, then we assign the rule to DFW (return empty list)
        otherwise, we set the scope to the paths provided

        *** for now, we're always going to set scope to ANY ***

        this is because as we're transitioning, each group will need to have both
        vm tag and ip address to classify members. because of the ip address requirement,
        we need to set the scope to DFW.

        TODO(lcrown): the next step is to write an auditing tool that will iterate
        through each rule in each policy.
        for each rule, if the source is NOT a cidr, count the list of IP addresses
        and compare against the number of VMs detected by the Tag. If the two counts match,
        then do the same process with the destination group.
        if both groups have equal counts between their tagged vms and ip addresses, set
        the scope to source_group,destination_group.
        """

        # short-circuit per the doc above
        return ["ANY"]

        scope = []

        # First, lets see if we can exit out with empty list ("ANY" condition)
        for path in source_groups:
            scope.append(path)
            if path == "ANY":
                return ["ANY"]
        for path in destination_groups:
            scope.append(path)
            if path == "ANY":
                return ["ANY"]

        # source and destination have specific paths, so we return the combined list
        return scope

    def _src_dest_handler(
        self,
        groups: Union[Literal["ANY"], NSXGroup, list[NSXGroup], str, list[str]],
    ):
        """
        Handles input from source_group and destination_group

        If Literal["ANY"], return ["ANY"]
        If NSXGroup or list of NSXGroup, return list of group paths
        """
        # handle the Literal["ANY"]
        self.debug.print(3, f'{groups} passed, returning ["ANY"]')
        if groups == "ANY" or groups == ["ANY"]:
            return ["ANY"]

        # handle list of NSXGroup
        if isinstance(groups, list):
            group_paths = []
            for g in groups:
                if isinstance(g, NSXGroup):
                    group_paths.append(g.path())
                else: # should be str
                    group_paths.append(g)
            return group_paths

        # handle single NSXGroup
        if isinstance(groups, NSXGroup):
            return [groups.path()]
        return [groups]

    def _src_handler(
        self,
        groups: Union[Literal["ANY"], NSXGroup, list[NSXGroup], str, list[str]],
    ) -> list[str]:
        """No special handling for source_groups, just calls the main handler"""
        self.debug.print(3, f"source groups: {groups}")
        return self._src_dest_handler(groups)

    def _dest_handler(
        self,
        groups: Union[Literal["ANY"], NSXGroup, list[NSXGroup], str, list[str], None],
    ) -> list[str]:
        """
        destination_group might be empty, in which case we check self.destination_group.
        If not found, raise an error that Destination is required.
        """
        self.debug.print(3, f"destination groups: {groups}")
        if not groups:  # handles the None case
            if self._destination_group:
                return [self._destination_group.path()]
            raise NSXDestinationNotFoundError(
                f"policy '{self.name()}' has no destination_group set and no destination_group provided to add_rule()"
            )
        return self._src_dest_handler(groups)

    def _action_handler(self, action: str) -> str:
        valid_actions = ["ALLOW", "DROP", "REJECT", "JUMP_TO_APPLICATION"]
        if action.upper() not in valid_actions:
            raise NSXRuleValidationError(
                f"action '{action}' not in valid actions: {','.join(valid_actions)}"
            )
        return action.upper()

    def add_rule(
        self,
        name: str,
        source_group: Union[Literal["ANY"], NSXGroup, list[NSXGroup], str, list[str]],
        action: str,
        service: Union[str, list[str], NSXService, list[NSXService]],
        destination_group: Union[Literal["ANY"], NSXGroup, list[NSXGroup], str, list[str], None] = None,
        sequence_number: Union[int, None] = None,
        description: str = "",
        logged: bool = False,
    ) -> None:
        """
        Add a rule to an existing NSX Policy

        Parameters
        ----------
        name: str
            Name of the rule. This can be anything reasonable (no crazy characters, dashes and underscores okay).
        source_group: Union[Literal["ANY"], NSXGroup, list[NSXGroup], str, list[str]]
            The source of the rule. Pass one or many NSXGroup objects, CIDR/IPAddr strings, or the string "ANY"
        action: str
            The action for the rule.
            Valid options: [ ALLOW, DROP, REJECT, JUMP_TO_APPLICATION ]
        service: Union[str, list[str], NSXService, list[NSXService]]
            The service you want to allow. You can pass one or many service names.
            For raw port-protocol, the service name should be in the following format:
            TCP_8080 -> TCP any source port, destination port 8080
            UDP_8700 -> UDP any source port, destination port 8700
            TCP_SRC_2334_DST_8080 -> TCP source port 2334, destination port 8080
        destination_group: Union[Literal["ANY"], NSXGroup, list[NSXGroup], str, list[str]], optional
            The destination of the rule.
            If not passed, it will inherit the destination group from the parent policy.
        sequence_number: int, optional
            Passing a sequence number allows you to insert a rule at the given position in the chain.
            If not passed, the rule will be appended to the end of the policy.
        logged: bool, optional
            If the traffic that hits this rule is logged.
            Default: True
        """

        self.debug.print(1, f"creating new rule for policy: {self.name()}")
        data = {}

        v_display_name = name
        v_id = cleanse_display_name(name)
        self.debug.print(3, f"display name cleansed into ID from '{name}' to '{v_id}'")

        v_source_groups = self._src_handler(source_group)
        v_destination_groups = self._dest_handler(destination_group)
        v_scope = self._scope_handler(v_source_groups, v_destination_groups)
        v_action = self._action_handler(action)
        v_sequence_number = self._rule_sequence_number_handler(sequence_number)
        v_logged = self._logged_handler(logged)

        data["display_name"] = v_display_name
        data["id"] = v_id
        data["action"] = v_action
        data["source_groups"] = v_source_groups
        data["destination_groups"] = v_destination_groups
        data["scope"] = v_scope
        data["description"] = description
        data["sequence_number"] = v_sequence_number
        data["logged"] = v_logged

        # service_entries can be unset
        # services has to be either:
        #   populated with valid services
        # or in the case of service_entries being present and no services:
        #   ["ANY"]
        services, service_entries = self._service_manager._service_handler(service)
        if services:
            data["services"] = services
        if service_entries:
            data["service_entries"] = service_entries

        rule = NSXRule(data)
        self._add_rule(rule)
        self.resequence_rules()
        self.save()

    def remove_rule(self, handle: int) -> bool:
        """Given a rule handle, remove the rule from the policy."""
        self.debug.print(1, f"removing rule {handle} from policy: {self.name()}")
        for rule in self.rules():
            if rule.handle() == handle:
                self._remove_rule(rule)
                self.resequence_rules()
                self.save()
                return True
        raise NSXRuleNotFoundError(handle)

    def save(self) -> bool:
        """
        Pass a valid NSXPolicy object to save changes to NSX
        """
        self.debug.print(1, f"saving security policy: {self.name()}")
        self.debug.print(3, self.pformat())
        endpoint = f"/policy/api/v1/infra/domains/{self.http.domain_id}/security-policies/{self.id()}"
        return bool(
            self.http.request(method="PATCH", endpoint=endpoint, data=self.dump())
        )

    # ---------------------------------------------------------------------------- #
    #                                    output                                    #
    # ---------------------------------------------------------------------------- #

    def output(self, format: Union[Literal["human"], Literal["json"]]) -> str:
        """Returns a string of output that represents the policy"""
        self._policy_manager.get_all()
        self._service_manager.get_all()
        outlines = []

        if format == "human":
            outlines.append("")
            outlines.append(f"Policy Name:  {self.name()}")
            outlines.append(f"Description:  {self.description()}")
            outlines.append(self.rules_outdata(format=format))

        if format == "json":
            outlines.append(self.rules_outdata(format=format))

        return "\n".join(outlines)

    def rules_outdata(self, format: Union[Literal["human"], Literal["json"]] = "human"):
        headers = [
            "name",
            "source",
            "destination",
            "service",
            "action",
            "handle",
            "seq",
        ]
        rule_data = []
        if not self.rules():
            return "\nNo rules configured for this policy."
        for rule in self.rules():
            source_groups = []
            for path in rule.source_group_paths():
                try:
                    group = self._group_manager.get_by_path(path)
                    source_groups.append(group.name())
                except NSXInvalidGroupError:
                    source_groups.append(path)

            destination_groups = []
            for path in rule.destination_group_paths():
                try:
                    group = self._group_manager.get_by_path(path)
                    destination_groups.append(group.name())
                except NSXInvalidGroupError:
                    destination_groups.append(path)

            services = []
            for path in rule.services_str():
                service = self._service_manager.get_by_path(path)
                if isinstance(service, NSXService):
                    services.append(service.name())
                else:
                    services.append(service)

            r = {
                "name": rule.name(),
                "source_groups": source_groups,
                "destination_groups": destination_groups,
                "services": services,
                "action": rule.action(),
                "handle": rule.handle(),
                # "seq": rule.sequence_number(),
            }
            rule_data.append(r)

        if format == "human":
            table_data = []
            for rule in rule_data:
                d = [
                    rule["name"],
                    "\n".join(rule["source_groups"]),
                    "\n".join(rule["destination_groups"]),
                    "\n".join(rule["services"]),
                    rule["action"],
                    rule["handle"],
                    # rule["seq"],
                ]
                table_data.append(d)
            return format_table(headers, table_data)

        if format == "json":
            out = {}
            out["policy_name"] = self.name()
            out["description"] = self.description()
            out["rules"] = rule_data
            return json.dumps(out)

        raise NSXInvalidOutputFormatError(format)

    def _get_group_list_from_destination_paths(
        self, destination_group_paths: list[str]
    ) -> list[NSXGroup]:
        """Converts a list of destination paths to a list of NSXGroup"""
        return [self._group_manager.get_by_path(p) for p in destination_group_paths]

    # ---------------------------------------------------------------------------- #
    #                                    audit                                     #
    # ---------------------------------------------------------------------------- #

    def audit_invalid_rule_destinations(self) -> list[dict[str, str]]:
        self._reload_rules()
        invalid_rules = []
        for rule in self.rules():
            if len(rule.destination_group_paths()) > 1:
                destination_names = []
                for destination_group_path in rule.destination_group_paths():
                    try:
                        group = self._group_manager.get_by_path(destination_group_path)
                        destination_names.append(group.name())
                    except NSXInvalidGroupError:
                        destination_names.append(destination_group_path)
                invalid_rules.append(
                    {
                        "rule_name": rule.name(),
                        "destination_groups": [n for n in destination_names],
                        "reason": "Rules should not have more than one destination group.",
                    }
                )
            destination_path = rule.destination_group_paths()[0]
            try:
                group = self._group_manager.get_by_path(destination_path)
                destination_name = group.name()
            except NSXInvalidGroupError:
                destination_name = destination_path
            if destination_name != self.name():
                invalid_rules.append(
                    {
                        "rule_name": rule.name(),
                        "destination_groups": [destination_name],
                        "reason": "Destination group name should match policy name.",
                    }
                )
        return invalid_rules
