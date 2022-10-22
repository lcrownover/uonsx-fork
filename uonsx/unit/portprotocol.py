from __future__ import annotations

from uonsx.error import NSXInvalidPortProtocolError
from uonsx.manager.policy import NSXPolicyManager


class NSXPortProtocolParser:
    def __init__(self, port_protocol_str: str):
        self.debug = NSXPolicyManager.get_instance().debug
        self.data = self._parse(port_protocol_str)

    def _check_valid_port_field(self, field) -> bool:
        if '-' in field:
            self.debug.print(3, f"found port range: {field}")
            for part in field.split('-'):
                try:
                    int(part)
                except ValueError:
                    return False
            return True
        self.debug.print(3, f"found singular port: {field}")
        try:
            int(field)
            return True
        except ValueError:
            return False

    def _parse(self, name: str) -> dict[str, str]:
        """
        Gets a data representation of a raw port protocol as an alternative to a Service

        Name parsing:
        "TCP_SRC_port1_port2_port3_DST_port1_port2"

        Examples:
        TCP_8081 -- shorthand for DST
        TCP_SRC_443_DST_8081
        TCP_2206-2209 -- port range
        """

        try:
            data = {
                "display_name": name,
                "l4_protocol": "TCP",
                "resource_type": "L4PortSetServiceEntry",
                "source_ports": [],
                "destination_ports": [],
            }

            components = [e.strip().upper() for e in name.split("_") if e.strip()]
            flag = False
            while components:
                part = components.pop(0)
                self.debug.print(3, f"processing part: {part}")

                if part in ["TCP", "UDP"]:  # this will only show up first
                    self.debug.print(3, f"l4_protocol detected: {part}")
                    data["l4_protocol"] = part
                    continue

                if part == "DST":
                    self.debug.print(3, "destination flag set")
                    flag = "destination"
                    continue

                if part == "SRC":
                    self.debug.print(3, "source flag set")
                    flag = "source"
                    continue

                if flag == "source":
                    self.debug.print(3, f"appending to source ports: {part}")
                    if not self._check_valid_port_field(part):
                        raise ValueError
                    data["source_ports"].append(part)
                    continue

                if flag == "destination" or not flag:
                    self.debug.print(3, f"appending to destination ports: {part}")
                    if not self._check_valid_port_field(part):
                        raise ValueError
                    data["destination_ports"].append(part)
                    continue

            self.debug.print(3, f"data: {data}")
            return data

        except ValueError:
            raise NSXInvalidPortProtocolError(name)

        except:
            raise NSXInvalidPortProtocolError(name)


    def dump(self) -> dict[str, str]:
        return self.data
