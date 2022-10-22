from __future__ import annotations

from typing import Union

from uonsx.config import NSXConfig
from uonsx.error import NSXBridgeProfileNotFoundError
from uonsx.http import HTTP
from uonsx.unit.bridge_profile import NSXBridgeProfile
from uonsx.util import format_table

class NSXBridgeProfileManager:
    """Manager class for NSX Bridge Profiles"""

    __instance = None
    __data_needs_refreshed = True

    @staticmethod
    def get_instance():
        if NSXBridgeProfileManager.__instance == None:
            raise Exception("NSXBridgeProfileManager is not inititalized")
        return NSXBridgeProfileManager.__instance

    def __init__(self, cfg: NSXConfig):
        if NSXBridgeProfileManager.__instance != None:
            raise Exception("Use the get_instance() method to use the NSX BridgeProfileManager")
        self.debug = cfg.debug
        self.debug.print(2, "Initializing bridge profile manager")
        self.http = HTTP.get_instance()
        self.data = []
        NSXBridgeProfileManager.__instance = self
        self.debug.print(2, "Bridge Profile Manager initialized")

    def _set_refresh(self, flag: bool = True) -> None:
        self.__data_needs_refreshed = flag

    def _refresh_data(self, force: bool = False):
        if self.__data_needs_refreshed or force:
            all_bridge_profiles = self.load_all_bridge_profiles()
            self.data = all_bridge_profiles
            self.__data_needs_refreshed = False

    def get_by_path(self, path: str) -> Union[NSXBridgeProfile,str]:
        self._refresh_data()
        for item in self.data:
            if item.path() == path:
                return item
        return path


    def load_all_bridge_profiles(self) -> list[NSXBridgeProfile]:
        """Query the API and return a list of all instances of NSXBridgeProfile"""
        self.debug.print(1,"loading all: bridge profiles")

        endpoint = "policy/api/v1/infra/sites/default/enforcement-points/default/edge-bridge-profiles"

        resp = self.http.request(method="GET", endpoint=endpoint)
        resp_items = resp["results"]

        all_bridge_profiles = [NSXBridgeProfile(bp) for bp in resp_items]

        return all_bridge_profiles


    def get(self, name: str) -> Union[NSXBridgeProfile, None]:
        """Query the API and return as instance of NSXBridgeProfile"""
        self._refresh_data()

        bridge_profile = None
        for bp in self.data:
            if bp.name() == name:
                bridge_profile = bp

        if not bridge_profile:
            raise NSXBridgeProfileNotFoundError(name)

        return bridge_profile

    def get_all(self) -> list[NSXBridgeProfile]:
        """return a list of all instances of NSXBridgeProfile"""
        self._refresh_data()
        self.debug.print(1, "getting all: bridge profile")
        return self.data


    def all_bridge_profiles_table(self):
        headers = ["name", "type", "ha_mode", "failover_mode", "path"]
        data = []
        for bridge_prof in self.get_all():
            d = [bridge_prof.name(), bridge_prof.type(), bridge_prof.ha_mode(), bridge_prof.failover_mode(), bridge_prof.path()]
            data.append(d)
        return format_table(headers, data)
