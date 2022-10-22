from __future__ import annotations

import json

class NSXBridgeProfile:
    """
    Wrapper for NSX Segment Information

    example:
    {
    "edge_paths": [
        "/infra/sites/default/enforcement-points/default/edge-clusters/38cabd60-3fb3-469c-9d5d-7fe1d75b9230/edge-nodes/2",
        "/infra/sites/default/enforcement-points/default/edge-clusters/38cabd60-3fb3-469c-9d5d-7fe1d75b9230/edge-nodes/3"
    ],
    "ha_mode": "ACTIVE_STANDBY",
    "failover_mode": "PREEMPTIVE",
    "resource_type": "L2BridgeEndpointProfile",
    "id": "edge_is-work01-ec01_bridge",
    "display_name": "edge_is-work01-ec01_bridge",
    "path": "/infra/sites/default/enforcement-points/default/edge-bridge-profiles/edge_is-work01-ec01_bridge",
    "relative_path": "edge_is-work01-ec01_bridge",
    "parent_path": "/infra/sites/default/enforcement-points/default",
    "unique_id": "2e40fac1-c4de-4294-8ffa-e4f622016b06",
    "marked_for_delete": false,
    "overridden": false,
    "_create_user": "adm-dteach@ad.uoregon.edu",
    "_create_time": 1633981569029,
    "_last_modified_user": "adm-dteach@ad.uoregon.edu",
    "_last_modified_time": 1633981569030,
    "_system_owned": false,
    "_protection": "NOT_PROTECTED",
    "_revision": 0
}
    """

    def __init__(self, data: dict):
        self.data = data

    def __str__(self):
        return f"NSXBridgeProfile(name='{self.name()}'...)"

    def __bool__(self):
        return True if self.data else False

    def name(self) -> str:
        return self.data['display_name']

    def id(self) -> str:
        return self.data.get("id", self.name())

    def type(self) -> str:
        return self.data['type']

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
