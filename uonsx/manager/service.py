from __future__ import annotations

import json
from pprint import pformat
from typing import Union

from typing_extensions import Literal
from uonsx.config import NSXConfig
from uonsx.error import (
    NSXInvalidOutputFormatError,
    NSXInvalidPortProtocolError,
    NSXServiceAlreadyExistsError,
    NSXServiceNotFoundError,
    NSXServiceParsingError,
    NSXServicePathNotFoundError,
    NSXServiceRequiredError,
)
from uonsx.http import HTTP
from uonsx.unit.portprotocol import NSXPortProtocolParser
from uonsx.unit.service import NSXService
from uonsx.util import cleanse_display_name, format_table


class NSXServiceManager:
    """Manager class for NSX Service"""

    __instance = None
    __data_needs_refresh = True

    @staticmethod
    def get_instance():
        if NSXServiceManager.__instance == None:
            raise Exception("NSXServiceManager is not initialized")
        return NSXServiceManager.__instance

    @staticmethod
    def is_port_protocol(service_name: str) -> bool:
        if service_name.upper().startswith("TCP_"):
            return True
        if service_name.upper().startswith("UDP_"):
            return True
        return False

    def __init__(self, cfg: NSXConfig):
        if NSXServiceManager.__instance != None:
            raise Exception(
                "use the get_instance() method to use the NSXServiceManager"
            )
        self.debug = cfg.debug
        self.debug.print(2, "initializing service manager")
        self.http = HTTP.get_instance()
        self.data = []
        NSXServiceManager.__instance = self
        self.debug.print(2, "service manager initialized")

    def _set_refresh(self, flag: bool = True) -> None:
        self.__data_needs_refresh = flag

    def _refresh_data(self, force: bool = False):
        if self.__data_needs_refresh or force:
            all_groups = self.load_all()
            self.data = all_groups
            self.__data_needs_refresh = False

    def _validate_service_not_exists(self, name: str) -> None:
        self._refresh_data()
        for g in self.data:
            if g.name() == name:
                raise NSXServiceAlreadyExistsError(name)

    def get_by_path(self, path: str) -> Union[NSXService, str]:
        self._refresh_data()
        for item in self.data:
            if item.path() == path:
                return item
        return path

    def load_all(self) -> list[NSXService]:
        """Query the API and return a list of all instances of NSXService"""
        self.debug.print(1, f"loading all: service")

        endpoint = f"/policy/api/v1/infra/services"
        # TODO(lcrown): refactor endpoints into HTTP class and pull from dict

        resp = self.http.request(method="GET", endpoint=endpoint)
        resp_items = resp["results"]

        all_services = [NSXService(i) for i in resp_items]

        return all_services

    def get(self, name: str) -> NSXService:
        """Query the API and return an instance of NSXService, searching by Name"""
        self._refresh_data()
        self.debug.print(1, f"getting service: {name}")
        service = None
        if self.data:
            for s in self.data:
                if s.name() == name:
                    service = s
        if not service:
            raise NSXServiceNotFoundError(name)
        return service

    def get_by_id(self, id: str) -> NSXService:
        """Query the API and return an instance of NSXService, searching by ID"""
        self._refresh_data()
        self.debug.print(1, f"getting service: {id}")
        service = None
        if self.data:
            for s in self.data:
                if s.id() == id:
                    service = s
        if not service:
            raise NSXServiceNotFoundError(id)
        return service

    def get_all(self) -> list[NSXService]:
        """return a list of all instances of NSXService"""

        self._refresh_data()
        self.debug.print(1, f"getting all: service")
        return self.data

    def create(
        self,
        name: str,
        services: list[str],
        description: str = "",
    ) -> NSXService:
        """
        Create a new NSX Service.

        Parameters
        ----------
        name: str
            Name of the service to create. Make sure you're following the naming convention.
        services: list[str], optional
            List of port-protocol strings to use in the new service.
            Example: ["TCP_8080", "TCP_8081"]
        description: str, optional
            Description for the service.
        """

        self._refresh_data()
        self.debug.print(1, f"creating service: {name}")
        self._validate_service_not_exists(name)
        data = {}
        data["resource_type"] = "Service"
        data["display_name"] = name
        data["id"] = cleanse_display_name(name)
        if description:
            data["description"] = description
        _, data["service_entries"] = self._service_handler(services)

        self.debug.print(3, f"service data pre-creation: {data}")
        service = NSXService(data)
        service = self._api_create(service)
        self._set_refresh()
        return service

    def _api_create(self, service: NSXService) -> NSXService:
        """Private method to create the service using the API"""
        self.debug.print(3, pformat(service.dump()))
        endpoint = f"/policy/api/v1/infra/services/{service.id()}"
        try:
            data = self.http.request(
                method="PUT", endpoint=endpoint, data=service.dump()
            )
        except NSXServiceAlreadyExistsError:
            raise
        return NSXService(data)

    def delete(self, name: str) -> bool:
        """Destroy an existing NSX Service"""
        self._refresh_data()
        self.debug.print(1, f"deleting service: {name}")

        service = self.get(name=name)

        self._api_delete(service)
        self._set_refresh()
        return True

    def _api_delete(self, service: NSXService) -> None:
        """Private method to delete the service using the API"""
        self.debug.print(3, pformat(service.dump()))
        endpoint = f"/policy/api/v1/infra/services/{service.id()}"
        # group exists:
        self.http.request(method="DELETE", endpoint=endpoint, data=service.dump())

    def _service_handler(
        self, service: Union[str, list[str], NSXService, list[NSXService]]
    ) -> tuple[list[str], Union[list[str], None]]:
        """
        Handles multiple input types for service

        One or many of:
            Service
            PortProtocol

        Returns a tuple of (services, service_entries)
        where services is a list of paths or list of single "ANY"
        where service_entries is a list of service entry objects or None
        """

        def _single_parser(
            service: Union[str, NSXService]
        ) -> Union[str, dict[str, str]]:
            if isinstance(service, str):
                self.debug.print(3, f"service is a string: {service}")
                return self._service_str_handler(service)
            if isinstance(service, NSXService):
                self.debug.print(3, f"service is an NSXService: {service}")
                return service.path()

        parsed_services = None

        # many objects passed in
        if isinstance(service, list):
            self.debug.print(3, f"service is a list: {service}")
            parsed_services = [_single_parser(i) for i in service]  # parse each service
            parsed_services = [s for s in parsed_services if s]  # strip out the None's

        # single object passed in
        if isinstance(service, str) or isinstance(service, NSXService):
            self.debug.print(3, f"service is singular: {service}")
            parsed_services = [_single_parser(service)]

        if not parsed_services:
            raise NSXServiceParsingError(service)

        if (not parsed_services) and service:
            raise NSXServiceRequiredError

        # parsed_services could contain any permutation of strings and dicts
        # service_entries will always be a dict
        # services will always be strings
        self.debug.print(3, f"parsed_services: {parsed_services}")
        services = []
        service_entries = []
        for element in parsed_services:
            if isinstance(element, str):
                services.append(element)
            if isinstance(element, dict):
                service_entries.append(element)
        # if service_entries is not empty, but services is,
        # we need to use "ANY" for services
        if (not services) and service_entries:
            services = ["ANY"]

        return services, service_entries

    def _service_str_handler(self, name: str) -> Union[str, dict[str, str]]:
        """
        Handles string input for services.

        Valid types: ["service", "port_protocol"]

        For each input:
            If string starts with "TCP_", it will return the syntax for `service_entries`
            Otherwise, it will try to find all the services by name and return a list of their paths
        """

        if self.is_port_protocol(name):
            self.debug.print(3, f"detected port_protocol: {name}")
            return NSXPortProtocolParser(name).dump()

        if name.upper() == "ANY":
            self.debug.print(3, f"detected ANY: {name}")
            return "ANY"

        service = self.get(name)
        self.debug.print(3, f"found service: {service}")
        if not service:
            raise NSXServiceNotFoundError(name)
        self.debug.print(3, f"returning path: {service.path()}")
        return service.path()

    def output(self, format: Union[Literal["human"], Literal["json"]]) -> str:
        """Returns a string output for all services"""
        if format == "human":
            return self.all_services_table()
        if format == "json":
            return self.all_services_json()
        raise NSXInvalidOutputFormatError(format)

    def all_services_table(self):
        headers = ["name"]
        data = []
        for service in self.get_all():
            d = [
                service.name(),
            ]
            data.append(d)

        return format_table(headers, data)

    def all_services_json(self) -> str:
        return json.dumps([s.name() for s in self.get_all()])
