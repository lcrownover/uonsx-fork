from __future__ import annotations

from typing import Union

from uonsx.config import NSXConfig
from uonsx.error import NSXSegmentPortNotFoundError
from uonsx.http import HTTP
from uonsx.unit.segment_port import NSXSegmentPort
from uonsx.util import format_table


class NSXSegmentPortManager:
    """Manager class for NSX Segments"""

    __instance = None
    __data_needs_refreshed = True

    @staticmethod
    def get_instance():
        if NSXSegmentPortManager.__instance == None:
            raise Exception("NSXSegmentPortManager is not initialized")
        return NSXSegmentPortManager.__instance


    def __init__(self, cfg: NSXConfig):
        if NSXSegmentPortManager.__instance != None:
            raise Exception("Use the get_instance() method to use the NSXSegmentPortManager")
        self.debug = cfg.debug
        self.debug.print(2, "Initializing segment port manager")
        self.http = HTTP.get_instance()
        self.segment_name = None
        self.data = []
        NSXSegmentPortManager.__instance = self
        self.debug.print(2, "Segment Port Manager initialized")

    def _set_segment_name(self, segment_name):
        self.segment_name = segment_name

    def _set_refresh(self, flag: bool = True) -> None:
        self.__data_needs_refreshed = flag

    def _refresh_data(self, force: bool = False):
        if self.__data_needs_refreshed or force:
            all_segment_ports = self.load_all_ports()
            self.data = all_segment_ports
            self.__data_needs_refreshed = False

    def get_by_path(self, path: str) -> Union[NSXSegmentPort,str]:
        self._refresh_data()
        for item in self.data:
            if item.path == path:
                return item
        return path

    def load_all_ports(self) -> list[NSXSegmentPort]:
        """Query the API and return a list of all instances of NSXSegmentPort"""
        self.debug.print(1, f"loading all: ports for segment {self.segment_name}")

        endpoint = f"policy/api/v1/infra/segments/{self.segment_name}/ports"

        resp = self.http.request(method="GET", endpoint=endpoint)
        resp_items = resp["results"]

        all_segment_ports = [NSXSegmentPort(i) for i in resp_items]

        return all_segment_ports

    def get_all_ports(self, segment_name: str) -> list[NSXSegmentPort]:
        """Return a list of all instances of NSXSegement"""
        self._set_segment_name(segment_name)
        self._refresh_data()
        self.debug.print(1, "getting all: segment")
        return self.data

    def all_ports_table(self):
        headers = ["segment", "attachment_id", "VM name", "VM interface", "admin_state"]
        data = []
        for port in self.data:
            vm_name, vm_int  = port.name().split('.')
            vm_int = vm_int.split('@')[1]
            d = [self.segment_name, port.attachment_id(), vm_name, vm_int, port.admin_state()]
            data.append(d)
        return format_table(headers, data)
