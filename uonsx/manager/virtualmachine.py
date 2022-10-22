from __future__ import annotations

from typing import Union

from uonsx.config import NSXConfig
from uonsx.error import NSXVirtualMachineNotFoundError
from uonsx.http import HTTP
from uonsx.unit.tag import NSXTag
from uonsx.unit.virtualmachine import NSXVirtualMachine, NSXVirtualInterface
from uonsx.unit.group import NSXGroup


class NSXVirtualMachineManager:
    """Manager class for NSX Virtual Machines"""

    __instance = None
    __data_needs_refresh = True

    @staticmethod
    def get_instance():
        if NSXVirtualMachineManager.__instance == None:
            raise Exception("NSXVirtualMachineManager is not initialized")
        return NSXVirtualMachineManager.__instance

    def __init__(self, cfg: NSXConfig):
        if NSXVirtualMachineManager.__instance != None:
            raise Exception(
                "use the get_instance() method to use the NSXVirtualMachineManager"
            )
        self.debug = cfg.debug
        self.data = []
        self.debug.print(2, "initializing virtualmachine manager")
        self.http = HTTP.get_instance()
        NSXVirtualMachineManager.__instance = self
        self.debug.print(2, "virtualmachine manager initialized")

    def _set_refresh(self, flag: bool = True) -> None:
        self.__data_needs_refresh = flag

    def _refresh_data(self, force: bool = False) -> None:
        if self.__data_needs_refresh or force:
            all_virtualmachines = self.load_all()
            self.data = all_virtualmachines
            self.__data_needs_refresh = False

    def _get_id(self, name: str) -> Union[str, None]:
        self._refresh_data()
        self.debug.print(2, f"getting id for virtualmachine name: {name}")
        if self.data:
            for item in self.data:
                if item.name() == name:
                    self.debug.print(2, f"found id for virtualmachine name: {name}")
                    return item.id()
        self.debug.print(2, f"did not find id for virtualmachine name: {name}")
        return None

    def load_all(self) -> list[NSXVirtualMachine]:
        """
        Query the API and return a list of all instances of NSXVirtualMachine
        """
        self.debug.print(1, f"getting all: virtualmachine")

        endpoint = f"/api/v1/fabric/virtual-machines"

        resp = self.http.request(method="GET", endpoint=endpoint)
        resp_items = resp["results"]

        virtualmachines = [NSXVirtualMachine(i) for i in resp_items]

        return virtualmachines

    def get(self, name: str) -> NSXVirtualMachine:
        """
        Query the API and return an instance of NSXVirtualMachine
        """

        self._refresh_data()
        self.debug.print(1, f"getting virtualmachine: {name}")

        # unlike policies, virtualmachines are fully-loaded when using `get_all()`
        virtualmachine = None
        if self.data:
            for vm in self.data:
                if vm.name() == name:
                    virtualmachine = vm

        if not virtualmachine:
            raise NSXVirtualMachineNotFoundError(name)

        return virtualmachine

    def get_all(self) -> list[NSXVirtualMachine]:
        """
        Query the API and return a list of all instances of NSXVirtualMachine
        """

        self._refresh_data()
        self.debug.print(1, f"getting all: virtualmachine")
        return self.data

    def add_tag(self, virtualmachine: NSXVirtualMachine, tag: NSXTag):
        self._refresh_data()
        self.debug.print(1, f"adding tag: {tag}")
        endpoint = f"/api/v1/fabric/virtual-machines?action=add_tags"
        data = {"external_id": virtualmachine.external_id(), "tags": [tag.tag_dict()]}
        self.http.request(method="POST", endpoint=endpoint, data=data)
        self._set_refresh()


    def remove_tag(self, virtualmachine: NSXVirtualMachine, tag: NSXTag):
        self._refresh_data()
        self.debug.print(1, f"removing tag: {tag}")
        endpoint = f"/api/v1/fabric/virtual-machines?action=remove_tags"
        data = {"external_id": virtualmachine.external_id(), "tags": [tag.tag_dict()]}
        self.http.request(method="POST", endpoint=endpoint, data=data)
        self._set_refresh()

    def all_vifs(self) -> list[NSXVirtualInterface]:
        self._refresh_data()
        endpoint = f"/api/v1/fabric/vifs"
        return [NSXVirtualInterface(i) for i in self.http.request(method="POST", endpoint=endpoint)["results"]]

    def group_name_list(self, virtualmachine: NSXVirtualMachine) -> list[str]:
        """Returns a list of Group names that this VM is a member of"""
        self._refresh_data()
        endpoint = f"/policy/api/v1/infra/virtual-machine-group-associations?vm_external_id={virtualmachine.external_id()}"
        return [i["target_display_name"] for i in self.http.request(method="GET", endpoint=endpoint)["results"]]

    def group_list(self, virtualmachine: NSXVirtualMachine) -> list[NSXGroup]:
        """Returns a list of NSXGroup objects that this VM is a member of"""
        from uonsx.manager.group import NSXGroupManager
        self._group_manager = NSXGroupManager.get_instance()
        self._refresh_data()
        return [self._group_manager.get(name) for name in self.group_name_list(virtualmachine)]

    # def _validate_component(self, component: str, valid_components: list[str]) -> str:
    #     verified_component = self._ignore_case_get(component, valid_components)
    #     if verified_component:
    #         return verified_component
    #     raise NSXvirtualmachineComponentNotFoundError(component, valid_components)

    # def _validate_value(self, value: str) -> str:
    #     """
    #     Used to validate the contents of the value property

    #     value should be two strings separated by a bar "|", the first string
    #     being the scope, and the second being the tag name
    #     I suppose it's actually fine to omit the scope, so we won't check for it,
    #     in case the user wants to force a scopeless tag
    #     """
    #     if value:
    #         return value

    #     raise NSXvirtualmachineValueEmptyError(value)

    # # def check(self, virtualmachine: NSXvirtualmachine):
    # #     """Validate an NSXvirtualmachine"""

    # def tag(self, name: str, scope: str = None) -> NSXvirtualmachine:
    #     """
    #     Shortcut for the `new` method.

    #     This method assumes you want the following logic:
    #     new(member_type="VirtualMachine", key="Tag", operator="EQUALS", value=<tag>, scope=<scope>)
    #     """

    #     return self.new(
    #         member_type="VirtualMachine",
    #         key="Tag",
    #         operator="EQUALS",
    #         value=name,
    #         scope=scope,
    #     )

    # def new(
    #     self, member_type: str, key: str, operator: str, value: str, scope: str = None
    # ):
    #     """
    #     Create a new virtualmachine object to be used with `nsx.group.create`

    #     Example [Any Virtual Machine tagged with the "is-managed" Tag]:
    #     new(member_type="VirtualMachine", key="Tag", operator="EQUALS", value="is-managed")

    #     Shorter example using the `tag` shortcut method:
    #     tag("is-managed")

    #     Parameters
    #     ----------
    #     member_type: str
    #         Type of NSX Component. Almost always "VirtualMachine".
    #         Valid options: [ IPSet, VirtualMachine, LogicalPort, LogicalSwitch, Segment, SegmentPort ]
    #     key: str
    #         Type of key.
    #         Valid options: [ Tag, Name, OSName, ComputerName ]
    #     operator: str
    #         Logic operator for this virtualmachine. Usually "EQUALS".
    #         Valid options: [ EQUALS, CONTAINS, STARTSWITH, ENDSWITH, NOTEQUALS ]
    #     value: str
    #         Value of the virtualmachine. Usually Tag name, or Virtual Machine name if using ComputerName key.
    #     scope: str, optional
    #         Adding scope will make the key {scope: value} instead of an unscoped value.

    #     Returns
    #     -------
    #     NSXvirtualmachine that contains everything you need to feed it to the `nsx.group.create` method.
    #     """

    #     if scope:
    #         value = f"{scope}|{value}"
    #     data = {}
    #     data["member_type"] = self._validate_component(
    #         member_type, self.valid_member_types
    #     )
    #     data["key"] = self._validate_component(key, self.valid_keys)
    #     data["operator"] = self._validate_component(operator, self.valid_operators)
    #     data["value"] = self._validate_value(value)
    #     data["resource_type"] = "Condition"
    #     virtualmachine = NSXvirtualmachine(data)
    #     return virtualmachine
