# This tool is used to:
#
# - scan through all rules
#
# - any rule where the source object(s) AND the destination object(s)
#   are native NSX objects (all IP addresses in the group are associated
#   with VMs that exist in NSX), report on that rule
#
# - if --fix is passed, it will change the Applied To field to the correct
#   scope for those groups
#
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from uonsx import NSX
    from uonsx.unit.rule import NSXRule


def site_rules(nsx: NSX) -> list[NSXRule]:
    rules = []
    return rules

from pprint import pprint

def rule_scope(nsx: NSX, fix: bool = False) -> None:
    gc = {}
    group = nsx.group.get("mem_lctest-guest1_DATA")
    print(group.check_native())
    # question for tomorrow:
    # Effective Members -> IP Addresses is holding on to an old IP address
    # how do i remove that? the host no longer has that IP
    return
    # group_vms = group.virtual_machines()
    # group_ipaddrs = group.ip_addresses()
        # figure out way to get a list of VM objects from group tag
        # then compare those objects to the list of IPs
        # if it all checks out, return True, otherwise as soon as somehting fails, return False

    pprint(group.dump())
    return

    cache = {}  # group_path: {group: nsxgroup, ipaddrs: [], vms: []}
    policies = nsx.policy.get_all()
    for policy in policies:
        policy._reload_rules()
        for rule in policy.rules():
            # number of vms found with tag matching group
            # has to equal the number of IP addr sources
            # those IPs have to match the VMs in the group
            # if "/" in any of the ip addrs, skip the group
            all_groups = []
            for group_path in rule.source_group_paths():
                if group_path in cache:
                    group = cache[group_path]
                    all_groups.append(group)
                    continue
                if group_path.startswith("/"):
                    group = nsx.group.get_by_path(group_path)
                    all_groups.append(group)
            for group_path in rule.destination_group_paths():
                if group_path in cache:
                    group = cache[group_path]
                    all_groups.append(group)
                    continue
                if group_path.startswith("/"):
                    group = nsx.group.get_by_path(group_path)
                    all_groups.append(group)

            all_native = True
            for group in all_groups:
                if not group.check_native():
                    all_native = False

            if all_native:
                print(all_groups)
