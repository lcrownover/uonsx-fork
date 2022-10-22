from __future__ import annotations

import json

class NSXSegmentPort:
    """
    Wrapper for NSX Segement Port
    
    example:
    {
            "attachment": {
                "id": "b29584a6-ab08-499c-b289-7372ecc62d54",
                "traffic_tag": 0,
                "hyperbus_mode": "DISABLE"
            },
            "admin_state": "UP",
            "resource_type": "SegmentPort",
            "id": "default:605d5083-2023-4e1c-b0ea-17b2769c98be",
            "display_name": "cwtest.vmx@b29584a6-ab08-499c-b289-7372ecc62d54",
            "tags": [],
            "path": "/infra/segments/edge_is-work01-ec01_vlan_2742/ports/default:605d5083-2023-4e1c-b0ea-17b2769c98be",
            "relative_path": "default:605d5083-2023-4e1c-b0ea-17b2769c98be",
            "parent_path": "/infra/segments/edge_is-work01-ec01_vlan_2742",
            "unique_id": "605d5083-2023-4e1c-b0ea-17b2769c98be",
            "marked_for_delete": false,
            "overridden": false,
            "_create_user": "system",
            "_create_time": 1633983784764,
            "_last_modified_user": "system",
            "_last_modified_time": 1633983784765,
            "_system_owned": false,
            "_protection": "NOT_PROTECTED",
            "_revision": 0
        }
    """

    def __init__(self, data: dict):
        from uonsx.manager.segment_port import NSXSegmentPortManager

        self.data = data
        self._mgr = NSXSegmentPortManager.get_instance()

    def __str__(self):
        return f"NSXSegementPort(name='{self.name()}'..."

    def __bool__(self):
        return true if self.data else False

    def name(self) -> str:
        return self.data["display_name"]

    def id(self) -> str:
        return self.data.get("id", self.name())

    def admin_state(self) -> str:
        return self.data["admin_state"]

    def attachment_id(self) -> str:
        return self.data["attachment"]["id"]

    def path(self) -> str:
        return self.data['path']

    def dump(self) -> dict:
        return self.data
