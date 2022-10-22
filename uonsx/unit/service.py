from __future__ import annotations

import json
from typing import Union

from typing_extensions import Literal
from uonsx.error import NSXInvalidOutputFormatError
from uonsx.util import format_table


class NSXService:
    """
    Wrapper for an NSX Service

    example:
    {
        "resource_type": "Service",
        "description": "AD Server",
        "id": "AD_Server",
        "display_name": "AD Server",
        "path": "/infra/services/AD_Server",
        "parent_path": "/infra/services/AD_Server",
        "relative_path": "AD_Server",
        "service_entries": [
          {
              "resource_type": "L4PortSetServiceEntry",
              "id": "AD_Server",
              "display_name": "AD Server",
              "path": "/infra/services/AD_Server/service-entries/AD_Server",
              "parent_path": "/infra/services/AD_Server",
              "relative_path": "AD_Server",
              "destination_ports": [
                  "1024"
              ],
              "l4_protocol": "TCP",
              "_create_user": "system",
              "_create_time": 1517296380484,
              "_last_modified_user": "system",
              "_last_modified_time": 1517296380484,
              "_system_owned": true,
              "_protection": "NOT_PROTECTED",
              "_revision": 0
          }
        ],
        "_create_user": "system",
        "_create_time": 1517296380468,
        "_last_modified_user": "system",
        "_last_modified_time": 1517296380468,
        "_system_owned": true,
        "_protection": "NOT_PROTECTED",
        "_revision": 0
    }

    """

    def __init__(self, data: dict):
        from uonsx.manager.service import NSXServiceManager

        self.data = data
        self._mgr = NSXServiceManager.get_instance()

    def __str__(self):
        return f"NSXService(name='{self.name()}'...)"

    def __bool__(self):
        return True if self.data else False

    def name(self) -> str:
        return self.data["display_name"]

    def description(self) -> str:
        return self.data.get("description", "")

    def id(self) -> str:
        return self.data.get("id", self.name())

    def path(self) -> str:
        return self.data["path"]

    def service_entries(self) -> list[dict]:
        return self.data["service_entries"]

    def get_service_entries(self) -> list[NSXServiceEntry]:
        return [NSXServiceEntry(se) for se in self.service_entries()]

    def dump(self):
        return self.data

    def to_json(self):
        return json.dumps(self.dump())

    def output(self, format: Union[Literal["human"], Literal["json"]]) -> str:
        """Returns a string output of the given service"""
        outlines = []
        if format == "human":
            outlines.append("")
            outlines.append(f"service Name:   {self.name()}")
            outlines.append(f"Description:  {self.description()}")
            outlines.append(self.service_entry_table())
        if format == "json":
            data = {
                "name": self.name(),
                "description": self.description(),
                "service_entries": self.service_entry_data(),
            }
            outlines.append(json.dumps(data))
        return "\n".join(outlines)

    def service_entry_table(self) -> str:
        """Returns a formatted table of service entries for the service"""
        headers = [
            "name",
            "protocol",
            "source_ports",
            "destination_ports",
            "resource_type",
        ]
        data = []
        service_entries = self.get_service_entries()
        for e in service_entries:
            data.append(
                [
                    e.name(),
                    e.protocol(),
                    e.source_ports(),
                    e.destination_ports(),
                    e.resource_type(),
                ]
            )
        return format_table(headers, data)

    def service_entry_data(self) -> list[str]:
        """Returns a list of service entries"""
        data = []
        for e in self.get_service_entries():
            data.append(
                {
                    "name": e.name(),
                    "protocol": e.protocol(),
                    "source_ports": e.source_ports(),
                    "destination_ports": e.destination_ports(),
                    "resource_type": e.resource_type(),
                }
            )
        return data


class NSXServiceEntry:
    """
    Example of two different kinds:
    {
        "l4_protocol": "TCP",
        "source_ports": [],
        "destination_ports": [
            "3307"
        ],
        "resource_type": "L4PortSetServiceEntry",
        "id": "TCP_3307",
        "display_name": "TCP_3307",
        "path": "/infra/services/Daisy_-_Banner_Forms/service-entries/TCP_3307",
        "relative_path": "TCP_3307",
        "parent_path": "/infra/services/Daisy_-_Banner_Forms",
        "unique_id": "41c18e4a-4c87-48a5-8225-7aa5e5573ca6",
        "marked_for_delete": false,
        "overridden": false,
        "_create_user": "adm-lcrown@uoregon.edu",
        "_create_time": 1632333816631,
        "_last_modified_user": "adm-lcrown@uoregon.edu",
        "_last_modified_time": 1632333816633,
        "_system_owned": false,
        "_protection": "NOT_PROTECTED",
        "_revision": 0
    },
    {
        "nested_service_path": "/infra/services/MySQL",
        "resource_type": "NestedServiceServiceEntry",
        "id": "MySQL",
        "display_name": "MySQL",
        "path": "/infra/services/Daisy_-_Banner_Forms/service-entries/MySQL",
        "relative_path": "MySQL",
        "parent_path": "/infra/services/Daisy_-_Banner_Forms",
        "unique_id": "8723a724-fca6-40b2-ac78-abc6d126a935",
        "marked_for_delete": false,
        "overridden": false,
        "_create_user": "adm-lcrown@uoregon.edu",
        "_create_time": 1634232479444,
        "_last_modified_user": "adm-lcrown@uoregon.edu",
        "_last_modified_time": 1634232628816,
        "_system_owned": false,
        "_protection": "NOT_PROTECTED",
        "_revision": 1
    },
    """

    def __init__(self, data: dict):
        self.data = data

    def __str__(self):
        return f"NSXServiceEntry(name='{self.name()}'...)"

    def __bool__(self):
        return True if self.data else False

    def name(self) -> str:
        return self.data["display_name"]

    def id(self) -> str:
        return self.data["id"]

    def protocol(self) -> str:
        if self.is_nested_service():
            return ""
        return self.data["l4_protocol"]

    def path(self) -> str:
        return self.data["path"]

    def resource_type(self) -> str:
        return self.data["resource_type"]

    def source_ports(self) -> str:
        if self.is_nested_service():
            return ""
        source_ports = self.data["source_ports"]
        if not source_ports:
            return "ANY"
        return ",".join(source_ports)

    def destination_ports(self) -> str:
        if self.is_nested_service():
            return ""
        destination_ports = self.data["destination_ports"]
        if not destination_ports:
            return "ANY"
        return ",".join(destination_ports)

    def dump(self):
        return self.data

    def to_json(self):
        return json.dumps(self.dump())

    def is_nested_service(self) -> bool:
        return self.resource_type() == "NestedServiceServiceEntry"

    def is_port_protocol(self) -> bool:
        return self.resource_type() == "L4PortSetServiceEntry"
