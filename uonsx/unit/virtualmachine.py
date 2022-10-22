from __future__ import annotations

import json
import re
from pprint import pformat

from typing import Union
from typing_extensions import Literal
from uonsx.unit.tag import NSXTag
from uonsx.util import strfmt, format_table


class NSXVirtualInterface:
    """
    Wrapper/Constructor for NSX Virtual Interface

    example:
    {
      "resource_type": "VirtualNetworkInterface",
      "device_key": "4000",
      "device_name": "Network adapter 1",
      "ip_address_info": [
        {
          "ip_addresses": [
            "172.16.20.10",
            "fe80::250:56ff:fe86:f2b2"
          ],
          "source": "VM_TOOLS"
        }
      ],
      "vm_local_id_on_host": "1",
      "mac_address": "00:50:56:86:f2:b2",
      "owner_vm_id": "5006d98a-352f-134f-df6b-33e7f8d5de65",
      "external_id": "5006d98a-352f-134f-df6b-33e7f8d5de65-4000",
      "lport_attachment_id": "3d4b208c-b986-47f7-8a29-a74610d33a13",
      "host_id": "74730a28-e52d-11e5-936e-6f061d405a28"
    },
    """

    def __init__(self, data: dict):
        self.data = data

    def __repr__(self) -> str:
        return json.dumps(self.__dict__())

    def __dict__(self) -> dict:
        return self.dump()

    def __str__(self) -> str:
        return strfmt(json.dumps(self.__dict__))

    def dump(self) -> dict:
        return self.data

    def to_json(self) -> str:
        return json.dumps(self.dump())

    def pformat(self) -> str:
        return pformat(self.dump())

    def device_name(self) -> str:
        return self.data["device_name"]

    def ip_addresses(self) -> list[str]:
        return self.data["ip_address_info"][0]["ip_addresses"]

    def owner_vm_id(self) -> str:
        return self.data["owner_vm_id"]


class NSXVirtualMachine:
    """
    Wrapper/Constructor for NSX VirtualMachines

    example:
    {'_last_sync_time': 1639087490019,
     'compute_ids': ['moIdOnHost:13',
                     'hostLocalId:13',
                     'locationId:564d0223-f7d2-996f-3cef-c9fb86eb75ce',
                     'instanceUuid:5016c2a5-5d50-5395-28d5-be7436bccfe2',
                     'externalId:5016c2a5-5d50-5395-28d5-be7436bccfe2',
                     'biosUuid:4216cef3-8ae4-d9ff-fbb1-bbd8e68121df'],
     'display_name': 'lctest-guest1',
     'external_id': '5016c2a5-5d50-5395-28d5-be7436bccfe2',
     'guest_info': {'computer_name': 'lctest-guest1.in.uoregon.edu',
                    'os_name': 'Ubuntu Linux (64-bit)'},
     'host_id': 'bf8def47-8cbe-4612-b536-3b83836ed9f9',
     'local_id_on_host': '13',
     'power_state': 'VM_RUNNING',
     'resource_type': 'VirtualMachine',
     'source': {'is_valid': True,
                'target_display_name': 'cc-9-6-vx-w04.uocloud.in.uoregon.edu',
                'target_id': 'bf8def47-8cbe-4612-b536-3b83836ed9f9',
                'target_type': 'HostNode'},
     'tags': [{'scope': '', 'tag': 'fn_is-managed'},
              {'scope': '', 'tag': 'mem_lctest-guest1_DATA'}],
     'type': 'REGULAR'}
    """

    def __init__(self, data: dict):
        from uonsx.manager.virtualmachine import NSXVirtualMachineManager

        self._virtualmachine_manager = NSXVirtualMachineManager.get_instance()
        self.debug = self._virtualmachine_manager.debug
        self.data = data

    def __repr__(self) -> str:
        return json.dumps(self.__dict__())

    def __dict__(self) -> dict:
        return self.dump()

    def __str__(self) -> str:
        return strfmt(json.dumps(self.__dict__()))

    def dump(self) -> dict:
        return self.data

    def to_json(self) -> str:
        return json.dumps(self.dump())

    def pformat(self) -> str:
        return pformat(self.dump())

    def name(self) -> str:
        return self.data["display_name"]

    def id(self) -> str:
        return self.data["host_id"]

    def hostname(self) -> str:
        return self.data["guest_info"]["computer_name"]

    def osname(self) -> str:
        return self.data["guest_info"]["os_name"]

    def tags(self) -> list[NSXTag]:
        return [NSXTag(data=tag) for tag in self.data.get("tags", [])]

    def external_id(self) -> str:
        return self.data["external_id"]

    def add_tag(self, name: str, scope: str = "") -> None:
        print("adding tag from unit")
        tag = NSXTag(name, scope)
        self._virtualmachine_manager.add_tag(self, tag)

    def vifs(self) -> list[NSXVirtualInterface]:
        out = []
        for vif in self._virtualmachine_manager.all_vifs():
            if vif.owner_vm_id() == self.id():
                out.append(vif)
        return out

    def ip_addresses(self) -> list[str]:
        ipaddrs = []
        for vif in self.vifs():
            ipv4_pattern = r"((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)([ (\[]?(\.|dot)[ )\]]?(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)){3})"
            for ipaddr in vif.ip_addresses():
                if re.match(ipv4_pattern, ipaddr):
                    ipaddrs.append(ipaddr)
        return ipaddrs

    # ---------------------------------------------------------------------------- #
    #                                    output                                    #
    # ---------------------------------------------------------------------------- #

    def output(self, format: Union[Literal["human"], Literal["json"]]) -> str:
        """Returns a string representation of the vm object"""
        data = {
            "display_name": self.name(),
            "hostname": self.hostname(),
            "osname": self.osname(),
            "tags": [t.dump() for t in self.tags()],
            "groups": self._virtualmachine_manager.group_name_list(self),
        }

        if format == "json":
            return json.dumps(data)

        if format == "human":
            outlines = []
            outlines.append("")
            outlines.append("VM Name:   {display_name}".format(**data))
            outlines.append("Hostname:  {hostname}".format(**data))
            outlines.append("OS Name:   {osname}".format(**data))
            outlines.append(self.tag_table())
            outlines.append(self.group_table())
            return "\n".join(outlines)

    def tag_table(self):
        headers = ["tag", "scope"]
        data = []
        for tag in self.tags():
            data.append([tag.name(), tag.scope()])
        return format_table(headers, data)

    def group_table(self):
        headers = ["groups"]
        data = [[group_name] for group_name in self._virtualmachine_manager.group_name_list(self)]
        return format_table(headers, data)
