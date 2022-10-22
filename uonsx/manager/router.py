from __future__ import annotations

from typing import Union

from uonsx.config import NSXConfig
from uonsx.error import (NSXInvalidPortProtocolError, NSXServiceNotFoundError,
                         NSXServicePathNotFoundError)
from uonsx.http import HTTP
from uonsx.unit.router import NSXRouter
from uonsx.util import format_table


class NSXRouterManager:
    """Manager class for NSX Router"""

    __instance = None
    __data_needs_refreshed = True

    @staticmethod
    def get_instance():
        if NSXRouterManager.__instance == None:
            raise Exception("NSXRouterManager is not initialized")
        return NSXRouterManager.__instance

    def __init__(self, cfg: NSXConfig):
        if NSXRouterManager.__instance != None:
            raise Exception("use the get_instance() method to use the NSXrouterManager")
        self.debug = cfg.debug
        self.debug.print(2, "inititializing router manager")
        self.http = HTTP.get_instance()
        self.data = []
        NSXRouterManager.__instance = self
        self.debug.print(2, "router manager initialized")

    def _set_refresh(self, flag: bool = True) -> None:
        self.__data_needs_refreshed = flag

    def _refresh_data(self, force: bool = False):
        if self.__data_needs_refreshed or force:
            all_tier0s = self.load_all_tier0s()
            all_tier1s = self.load_all_tier1s()
            self.data = all_tier0s + all_tier1s
            self.__data_needs_refresh = False

    def get_by_path(self, path: str) -> Union[NSXRouter,str]:
        self._refresh_data()
        for item in self.data:
            if item.path == path:
                return item
        return path

    def load_all_tier0s(self) -> list[NSXRouter]:
        """Query the API and return a lit of all instances of NSXrouter (tier0)"""
        self.debug.print(1, f"loading all: tier0s")

        endpoint = "policy/api/v1/infra/tier-0s"

        resp = self.http.request(method="GET", endpoint=endpoint)
        resp_items = resp["results"]

        all_tier0s = [NSXRouter(i) for i in resp_items]

        return all_tier0s

    def load_all_tier1s(self) -> list[NSXRouter]:
        """Query the API and return a lit of all instances of NSXrouter (tier1)"""
        self.debug.print(1, f"loading all: tier1s")

        endpoint = "policy/api/v1/infra/tier-1s"

        resp = self.http.request(method="GET", endpoint=endpoint)
        resp_items = resp["results"]

        all_tier1s = [NSXRouter(i) for i in resp_items]

        return all_tier1s

    def get(self, name: str) -> Union[NSXRouter, None]:
        """Query the API and return an instance of NSXrouter"""
        self._refresh_data()
        self.debug.print(1, f"getting router: {name}")

        router = None
        if self.data:
            for r in self.data:
                if r.name() == name:
                    router = r

        if not router:
            return None

        return router

    def get_all(self, ignore_checks: bool = False) -> list[NSXRouter]:
        """Return a list of all instances of NSXRouter"""
        self._refresh_data()
        self.debug.print(1, "getting all: router")
        return self.data

    def all_routers_table(self):
        headers = ["name", "type", "ha_mode", "failover_mode"]
        data = []
        for router in self.get_all():
            d = [router.name(), router.type(), router.ha_mode(), router.failover_mode()]
            data.append(d)
        return format_table(headers, data)

    def all_tier0s_table(self):
        headers = ["name", "type", "ha_mode", "failover_mode"]
        data = []
        for router in self.get_all():
            if router.type() == 'Tier0':
                d = [router.name(), router.type(), router.ha_mode(), router.failover_mode()]
                data.append(d)
        return format_table(headers, data)

    def all_tier1s_table(self):
        headers = ["name", "type", "ha_mode", "failover_mode"]
        data = []
        for router in self.get_all():
            if router.type() == 'Tier1':
                d = [router.name(), router.type(), router.ha_mode(), router.failover_mode()]
                data.append(d)
        return format_table(headers, data)

