from __future__ import annotations

import json

from uonsx.util import strfmt

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from uonsx.unit.group import NSXGroup


class NSXRule:
    """
    Wrapper/Constructor for NSX Rule

    example:
    {
      "description": "comm entry",
      "display_name": "ce-1",
      "sequence_number": 1,
      "source_groups": [
          "/infra/domains/DOMAIN/groups/webgroup"
      ],
      "logged": false,
      "destination_groups": [
          "/infra/domains/DOMAIN/groups/dbgroup"
      ],
      "scope": [
          "ANY"
      ],
      "action": "DROP",
      "services": [
          "ANY"
      ]
    }
    """
    valid_actions = ["ALLOW", "DROP", "REJECT", "JUMP_TO_APPLICATION"]

    def __init__(self, data: dict):
        from uonsx.manager.service import NSXServiceManager
        self.service_manager = NSXServiceManager.get_instance()
        from uonsx.manager.group import NSXGroupManager
        self.group_manager = NSXGroupManager.get_instance()
        self.data = data

    def __repr__(self):
        return json.dumps(self.dump())

    def __str__(self) -> str:
        return strfmt(json.dumps(self.dump()))

    def __lt__(self, other) -> bool:
        if isinstance(other, NSXRule):
            return self.sequence_number() < other.sequence_number()
        return self.sequence_number < other

    def __le__(self, other) -> bool:
        if isinstance(other, NSXRule):
            return self.sequence_number() <= other.sequence_number()
        return self.sequence_number <= other

    def __gt__(self, other) -> bool:
        if isinstance(other, NSXRule):
            return self.sequence_number() > other.sequence_number()
        return self.sequence_number > other

    def __ge__(self, other) -> bool:
        if isinstance(other, NSXRule):
            return self.sequence_number() >= other.sequence_number()
        return self.sequence_number >= other

    def __eq__(self, other) -> bool:
        if isinstance(other, NSXRule):
            return self.sequence_number() == other.sequence_number()
        return self.sequence_number == other

    def __ne__(self, other) -> bool:
        if isinstance(other, NSXRule):
            return self.sequence_number() != other.sequence_number()
        return self.sequence_number != other

    def dump(self) -> dict:
        return self.data

    def to_json(self) -> str:
        return json.dumps(self.dump())

    def name(self) -> str:
        return self.data.get("display_name", "")

    def id(self) -> str:
        return self.data.get("id", "")

    def handle(self) -> int:
        return self.data.get("rule_id", 0)

    def logged(self) -> bool:
        return self.data["logged"]

    def source_groups(self) -> list[NSXGroup]:
        return [self.group_manager.get_by_path(gp) for gp in self.source_group_paths()]

    def source_group_paths(self, trim_names: bool = False) -> list[str]:
        source_group_paths = self.data.get("source_groups", [])
        if trim_names:
            return [sg.split('/')[-1] for sg in source_group_paths if sg]
        return source_group_paths

    def destination_group_paths(self, trim_names: bool = False) -> list[str]:
        destination_group_paths = self.data.get("destination_groups", [])
        if trim_names:
            return [dg.split('/')[-1] for dg in destination_group_paths if dg]
        return destination_group_paths

    def service_paths(self, trim_names: bool = False) -> list[str]:
        serv_paths = self.data.get("services", [])
        if trim_names:
            return [sp.split('/')[-1] for sp in serv_paths if sp]
        return serv_paths

    def service_entries(self) -> list[str]:
        serv_entries = self.data.get("service_entries", [])
        out = []
        for s in serv_entries:
            entry_str = "{}_{}".format(s["l4_protocol"], "_".join(s["destination_ports"]))
            out.append(entry_str)
        return out

    def services_str(self) -> list[str]:
        service_paths = self.service_paths()
        # get_by_path returns either an NSXService or a string, so we have to manually check
        mixed_services = [self.service_manager.get_by_path(path) for path in service_paths]
        services = []
        for s in mixed_services:
            if isinstance(s, str):
                services.append(s)
            else:
                services.append(s.name())

        service_entries = self.service_entries()
        # When service entries are present, services is just "ANY", even if only service_entries.
        if service_entries and services == ["ANY"]:
            return service_entries
        return services + service_entries

    def sequence_number(self) -> int:
        return int(self.data["sequence_number"])

    def set_sequence_number(self, sequence_number: int) -> None:
        self.data["sequence_number"] = sequence_number

    def action(self) -> str:
        return self.data.get("action", "")

    def scope(self) -> list[str]:
        return self.data.get("scope", [])


#     def dump(self):
#         out = {}
#         for k, v in self.__repr__().items():
#             if k in ["source_groups", "destination_groups"]:
#                 glist = []
#                 for item in v:
#                     if isinstance(item, NSXGroup):
#                         glist.append(item.path())
#                         continue
#                     glist.append(item)
#                 out[k] = glist
#                 continue
#             out[k] = v
#         return out
