from __future__ import annotations

import json

class NSXSegment:
    """
    Wrapper for NSX Segment Information

    example:
    {
    "type": "DISCONNECTED",
    "transport_zone_path": "/infra/sites/default/enforcement-points/default/transport-zones/86758391-2725-4172-aef1-0c7c1c5f36a0",
    "advanced_config": {
        "address_pool_paths": [],
        "hybrid": false,
        "inter_router": false,
        "local_egress": false,
        "urpf_mode": "STRICT",
        "connectivity": "ON"
    },
    "bridge_profiles": [
        {
            "bridge_profile_path": "/infra/sites/default/enforcement-points/default/edge-bridge-profiles/edge_is-work01-ec01_bridge",
            "uplink_teaming_policy_name": "edge_is-work01-ec01_edge-bridge_uplink1",
            "vlan_ids": [
                "2742"
            ],
            "vlan_transport_zone_path": "/infra/sites/default/enforcement-points/default/transport-zones/8ca24883-146f-4934-b812-768d79423ebb"
        }
    ],
    "admin_state": "UP",
    "replication_mode": "MTEP",
    "resource_type": "Segment",
    "id": "edge_is-work01-ec01_vlan_2742",
    "display_name": "edge_is-work01-ec01_vlan_2742",
    "path": "/infra/segments/edge_is-work01-ec01_vlan_2742",
    "relative_path": "edge_is-work01-ec01_vlan_2742",
    "parent_path": "/infra",
    "unique_id": "41b4bb71-4d87-4288-bc5c-16d91f751e0e",
    "marked_for_delete": false,
    "overridden": false,
    "_create_user": "adm-dteach@ad.uoregon.edu",
    "_create_time": 1633983513629,
    "_last_modified_user": "adm-dteach@ad.uoregon.edu",
    "_last_modified_time": 1633984112581,
    "_system_owned": false,
    "_protection": "NOT_PROTECTED",
    "_revision": 2
    }
    """

    def __init__(self, data: dict):
        from uonsx.manager.segment import NSXSegmentManager
        from uonsx.manager.bridge_profile import NSXBridgeProfileManager
        self.data = data
        self._segment_manager = NSXSegmentManager.get_instance()
        self._bridge_profile_manager  = NSXBridgeProfileManager.get_instance()


    def __str__(self):
        return f"NSXSegment(name='{self.name()}'...)"

    def __bool__(self):
        return True if self.data else False

    def name(self) -> str:
        return self.data['display_name']

    def id(self) -> str:
        return self.data.get("id", self.name())

    def type(self) -> str:
        return self.data['type']

    def admin_state(self) -> str:
        return self.data['admin_state']

    def bridge_profiles(self) -> list[dict]:
        """bridge profiles are losely coupled mapping of a bridge profile path, vlans, and transport zone to a segment."""
        bridge_profs = []
        if 'bridge_profiles' in self.data.keys():
            self._bridge_profile_manager._set_refresh()
            for bridge_profile in self.data['bridge_profiles']:
                vlan_ids = bridge_profile.get('vlan_ids', None)
                bridge_prof = self._bridge_profile_manager.get_by_path(bridge_profile['bridge_profile_path'])
                bridge_profs.append({'vlan_ids': vlan_ids, 'bridge_profile': bridge_prof.name()})
        return bridge_profs

    def dump(self):
        return self.data
