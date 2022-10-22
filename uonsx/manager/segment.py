from __future__ import annotations

from typing import Union

from uonsx.config import NSXConfig
from uonsx.error import NSXSegmentNotFoundError
from uonsx.http import HTTP
from uonsx.unit.segment import NSXSegment
from uonsx.unit.bridge_profile import NSXBridgeProfile
from uonsx.util import format_table


class NSXSegmentManager:
    """Manager class for NSX Segments"""

    __instance = None
    __data_needs_refreshed = True

    @staticmethod
    def get_instance():
        if NSXSegmentManager.__instance == None:
            raise Exception("NSXSegmentManager is not initialized")
        return NSXSegmentManager.__instance


    def __init__(self, cfg: NSXConfig):
        if NSXSegmentManager.__instance != None:
            raise Exception("Use the get_instance() method to use the NSXSegmentManager")
        self.debug = cfg.debug
        self.debug.print(2, "Initializing segment manager")
        self.http = HTTP.get_instance()
        self.data = []
        NSXSegmentManager.__instance = self
        self.debug.print(2, "Segment Manager initialized")

    def _set_refresh(self, flag: bool = True) -> None:
        self.__data_needs_refreshed = flag

    def _refresh_data(self, force: bool = False):
        if self.__data_needs_refreshed or force:
            all_segments = self.load_all()
            self.data = all_segments
            self.__data_needs_refreshed = False

    def get_by_path(self, path: str) -> Union[NSXSegment,str]:
        self._refresh_data()
        for item in self.data:
            if item.path == path:
                return item
        return path

    def load_all(self) -> list[NSXSegment]:
        """Query the API and return a list of all instances of NSXSegment"""
        self.debug.print(1, f"loading all: segments")

        endpoint = "policy/api/v1/infra/segments"

        resp = self.http.request(method="GET", endpoint=endpoint)
        resp_items = resp["results"]

        all_segments = [NSXSegment(i) for i in resp_items]

        return all_segments

    def get(self, name: str) -> Union[NSXSegment, None]:
        """Query the API and return an instance of NSXSegment"""
        self._refresh_data()
        self.debug.print(1, f"getting segment: {name}")

        segment = None
        for s in self.data:
            if s.name() == name:
                segment = s

        if not segment:
            raise NSXSegmentNotFoundError(name)

        return segment

    def get_all(self) -> list[NSXSegment]:
        """Return a list of all instances of NSXSegement"""
        self._refresh_data()
        self.debug.print(1, "getting all: segment")
        return self.data

    def all_segments_table(self):
        headers = ["name", "type", "admin_state", "bridge_profile", "bridge_vlans"]
        data = []
        for segment in self.get_all():
            d = []
            if not segment.bridge_profiles():
                d = [segment.name(), segment.type(), segment.admin_state(), "", ""]
            else:
                bps = segment.bridge_profiles()
                first_bp = True
                for bp in bps:
                    if first_bp:
                        d = [segment.name(), segment.type(), segment.admin_state(), bp['bridge_profile'], ','.join(bp['vlan_ids'])]
                        first_bp = False
                    else:
                        d = [ "","","", bp['bridge_profile'], ','.join(bp['vlan_ids'])]
            if d:
                data.append(d)

        return format_table(headers, data)
