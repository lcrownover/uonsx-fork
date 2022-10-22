from __future__ import annotations

import json

class NSXRouter:
    """
    Wrapper for NSX Router Information
    
    example:
    {
    "tier0_path": "/infra/tier-0s/is-work1-ec01-t0-gw01",
    "failover_mode": "NON_PREEMPTIVE",
    "enable_standby_relocation": true,
    "route_advertisement_types": [
        "TIER1_LB_SNAT",
        "TIER1_DNS_FORWARDER_IP",
        "TIER1_IPSEC_LOCAL_ENDPOINT",
        "TIER1_NAT",
        "TIER1_CONNECTED",
        "TIER1_STATIC_ROUTES",
        "TIER1_LB_VIP"
    ],
    "force_whitelisting": false,
    "default_rule_logging": false,
    "disable_firewall": false,
    "ipv6_profile_paths": [
        "/infra/ipv6-ndra-profiles/default",
        "/infra/ipv6-dad-profiles/default"
    ],
    "pool_allocation": "ROUTING",
    "resource_type": "Tier1",
    "id": "is-work1-ec01-t1-gw01",
    "display_name": "is-work1-ec01-t1-gw01",
    "tags": [
        {
            "scope": "Created by",
            "tag": "VCF"
        }
    ],
    "path": "/infra/tier-1s/is-work1-ec01-t1-gw01",
    "relative_path": "is-work1-ec01-t1-gw01",
    "parent_path": "/infra",
    "unique_id": "048bd362-d734-4b53-90c7-d2a9d7e38d16",
    "marked_for_delete": false,
    "overridden": false,
    "_create_user": "admin",
    "_create_time": 1627069249339,
    "_last_modified_user": "admin",
    "_last_modified_time": 1627069249343,
    "_system_owned": false,
    "_protection": "NOT_PROTECTED",
    "_revision": 0
    }
    """

    def __init__(self, data: dict):
        from uonsx.manager.router import NSXRouterManager

        self.data = data
        self._mgr = NSXRouterManager.get_instance()

    def __str__(self):
        return f"NSXRouter(name='{self.name()}'...)"

    def __bool__(self):
        return True if self.data else False

    def name(self) -> str:
        return self.data["display_name"]

    def id(self) -> str:
        return self.data.get("id", self.name())

    def type(self) -> str:
        return self.data['resource_type']

    def ha_mode(self) -> str:
        return self.data.get('ha_mode', "None")
    
    def failover_mode(self) -> str:
        return self.data['failover_mode']

    def path(self) -> str:
        return self.data["path"]

    def dump(self):
        return self.data

    def to_json(self):
        return json.dumps(self.dump())