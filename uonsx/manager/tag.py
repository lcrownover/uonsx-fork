# from typing import Union

# from uonsx.config import NSXConfig
# from uonsx.http import HTTP
# from uonsx.unit.tag import NSXTag


# class NSXTagManager:
#     """Manager class for NSX Tags"""

#     __instance = None

#     @staticmethod
#     def get_instance():
#         if NSXTagManager.__instance == None:
#             raise Exception("NSXTagManager is not initialized")
#         return NSXTagManager.__instance

#     def __init__(self, cfg: NSXConfig):
#         if NSXTagManager.__instance != None:
#             raise Exception(
#                 "use the get_instance() method to use the NSXTagManager"
#             )
#         self.debug = cfg.debug
#         self.data = None
#         self.debug.print(1, "initializing expression manager")
#         self.http = HTTP.get_instance()

#     def _refresh_data(self, force: bool = False) -> None:
#         if not self.data or force:
#             all_tags = self.get_all()
#             self.data = all_tags

#     def _get_id(self, name: str) -> Union[str, None]:
#         self._refresh_data()
#         self.debug.print(2, f"getting id for tag name: {name}")
#         if self.data:
#             for item in self.data:
#                 if item.name() == name:
#                     self.debug.print(2, f"found id for tag name: {name}")
#                     return item.id()
#         self.debug.print(2, f"did not find id for tag name: {name}")
#         return None

#     def get(self, name: str) -> Union[NSXTag, None]:
#         """
#         Query the API and return an instance of NSXtag
#         """
#         self.debug.print(1, f"getting tag: {name}")

#         id = self._get_id(name=name)
#         if not id:
#             self.debug.print(1, "tag not found")
#             return None

#         endpoint = f"{self.http.base_endpoint}/security-tags/{id}"

#         tag_data = self.http.request(method="GET", endpoint=endpoint)

#         if tag_data:
#             return NSXTag(tag_data)

#         return None

#     def get_all(self) -> list[NSXTag]:
#         """
#         Query the API and return a list of all instances of NSXtag
#         """
#         self.debug.print(1, f"getting all: tag")

#         endpoint = f"/api/v1/csm/virtual-machines"

#         resp = self.http.request(method="GET", endpoint=endpoint)
#         resp_items = resp["results"]

#         tags = [NSXTag(i) for i in resp_items]

#         return tags
#     # def _validate_component(self, component: str, valid_components: list[str]) -> str:
#     #     verified_component = self._ignore_case_get(component, valid_components)
#     #     if verified_component:
#     #         return verified_component
#     #     raise NSXExpressionComponentNotFoundError(component, valid_components)

#     # def _validate_value(self, value: str) -> str:
#     #     """
#     #     Used to validate the contents of the value property

#     #     value should be two strings separated by a bar "|", the first string
#     #     being the scope, and the second being the tag name
#     #     I suppose it's actually fine to omit the scope, so we won't check for it,
#     #     in case the user wants to force a scopeless tag
#     #     """
#     #     if value:
#     #         return value

#     #     raise NSXExpressionValueEmptyError(value)

#     # # def check(self, expression: NSXExpression):
#     # #     """Validate an NSXExpression"""

#     # def tag(self, name: str, scope: str = None) -> NSXExpression:
#     #     """
#     #     Shortcut for the `new` method.

#     #     This method assumes you want the following logic:
#     #     new(member_type="tag", key="Tag", operator="EQUALS", value=<tag>, scope=<scope>)
#     #     """

#     #     return self.new(
#     #         member_type="tag",
#     #         key="Tag",
#     #         operator="EQUALS",
#     #         value=name,
#     #         scope=scope,
#     #     )

#     # def new(
#     #     self, member_type: str, key: str, operator: str, value: str, scope: str = None
#     # ):
#     #     """
#     #     Create a new expression object to be used with `nsx.group.create`

#     #     Example [Any Virtual Machine tagged with the "is-managed" Tag]:
#     #     new(member_type="tag", key="Tag", operator="EQUALS", value="is-managed")

#     #     Shorter example using the `tag` shortcut method:
#     #     tag("is-managed")

#     #     Parameters
#     #     ----------
#     #     member_type: str
#     #         Type of NSX Component. Almost always "tag".
#     #         Valid options: [ IPSet, tag, LogicalPort, LogicalSwitch, Segment, SegmentPort ]
#     #     key: str
#     #         Type of key.
#     #         Valid options: [ Tag, Name, OSName, ComputerName ]
#     #     operator: str
#     #         Logic operator for this expression. Usually "EQUALS".
#     #         Valid options: [ EQUALS, CONTAINS, STARTSWITH, ENDSWITH, NOTEQUALS ]
#     #     value: str
#     #         Value of the expression. Usually Tag name, or Virtual Machine name if using ComputerName key.
#     #     scope: str, optional
#     #         Adding scope will make the key {scope: value} instead of an unscoped value.

#     #     Returns
#     #     -------
#     #     NSXExpression that contains everything you need to feed it to the `nsx.group.create` method.
#     #     """

#     #     if scope:
#     #         value = f"{scope}|{value}"
#     #     data = {}
#     #     data["member_type"] = self._validate_component(
#     #         member_type, self.valid_member_types
#     #     )
#     #     data["key"] = self._validate_component(key, self.valid_keys)
#     #     data["operator"] = self._validate_component(operator, self.valid_operators)
#     #     data["value"] = self._validate_value(value)
#     #     data["resource_type"] = "Condition"
#     #     expression = NSXExpression(data)
#     #     return expression
