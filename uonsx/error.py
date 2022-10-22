from __future__ import annotations

import requests


class NSXGenericError(Exception):
    def __init__(self, msg: str):
        super().__init__(msg)


# class NSXInvalidCredentialsError(Exception):
#     def __init__(self, msg: str = "Invalid credentials"):
#         super().__init__(msg)


class NSXInvalidConfigurationError(Exception):
    def __init__(
        self,
        msg: str = "Missing configuration items. See settings.ini.template for an example.",
    ):
        super().__init__(msg)


class NSXGroupNotFoundError(Exception):
    def __init__(self, name: str):
        msg = f"group not found: {name}"
        super().__init__(msg)

class NSXTagNotFoundError(Exception):
    def __init__(self, key: str, value: str):
        msg = f"tag not found: {key}:{value}"
        super().__init__(msg)

class NSXGroupHasNoTagsError(Exception):
    def __init__(self, name: str):
        msg = f"no tags found for group: {name}"
        super().__init__(msg)

class NSXExpressionIPAddressNotFoundError(Exception):
    def __init__(self, ipaddress: str):
        self.msg = f"ipaddress not found: {ipaddress}"
        super().__init__(self.msg)


class NSXServiceNotFoundError(Exception):
    def __init__(self, name: str):
        msg = f"service not found: {name}"
        super().__init__(msg)

class NSXInvalidPolicyCategoryError(Exception):
    def __init__(self, category: str, valid_categories: list[str]):
        msg = f"policy category '{category}' not found in valid categories: {valid_categories}"
        super().__init__(msg)

class NSXGroupPathNotFoundError(Exception):
    def __init__(self, path: str):
        msg = f"group not found using path: {path}"
        super().__init__(msg)


class NSXServicePathNotFoundError(Exception):
    def __init__(self, path: str):
        msg = f"service not found using path: {path}"
        super().__init__(msg)


class NSXRuleNotFoundError(Exception):
    def __init__(self, handle: int):
        msg = f"rule not found with handle: {str(handle)}"
        super().__init__(msg)


class NSXInvalidGroupError(Exception):
    def __init__(self, path: str):
        msg = f"path is not a valid NSXGroup: {path}"
        super().__init__(msg)


class NSXInvalidPortProtocolError(Exception):
    def __init__(self, port_protocol_str: str):
        msg = f"invalid port protocol: {port_protocol_str}"
        super().__init__(msg)


class NSXMissingConfigurationItemError(Exception):
    def __init__(self, arg_name: str):
        msg = f"missing configuration item: {arg_name}"
        super().__init__(msg)


class NSXVirtualMachineNotFoundError(Exception):
    def __init__(self, name: str):
        msg = f"virtualmachine not found: {name}"
        super().__init__(msg)


class NSXRouterNotFoundError(Exception):
    def __init__(self, name: str):
        msg = f"router not found: {name}"
        super().__init__(msg)


class NSXSegmentNotFoundError(Exception):
    def __init__(self, name: str):
        msg = f"segment not found: {name}"
        super().__init__(msg)


class NSXSegmentPortNotFoundError(Exception):
    def __init__(self, name: str):
        msg = f"segment port not found: {name}"
        super().__init__(msg)


class NSXBridgeProfileNotFoundError(Exception):
    def __init__(self, name: str):
        msg = f"bridge profile not found: {name}"
        super().__init__(msg)


class NSXObjectAlreadyExistsError(Exception):
    def __init__(self, error_message: str):
        try:
            obj_id = error_message.split("[")[1].split("]")[0].split("/")[-1]
        except:
            obj_id = f"<failed to get path: {error_message}"
        msg = f"Object already exists: {obj_id}"
        super().__init__(msg)


class NSXObjectHasDependenciesError(Exception):
    def __init__(self, error_message: str):
        try:
            obj_id = error_message.split("[")[1].split("]")[0].split("/")[-1]
        except:
            obj_id = f"<failed to get path: {error_message}>"
        try:
            paths = error_message.split("[")[2].split("]")[0].split(",")
            dependency_str = ",".join(paths)
        except:
            dependency_str = "<failed to get dependency string>"
        msg = f"Failed to delete '{obj_id}', has dependencies: [{dependency_str}]"
        super().__init__(msg)


class NSXObjectNotFoundError(Exception):
    def __init__(self, error_message: str):
        try:
            obj_path = error_message.replace("The requested object : ", "").split(" ")[
                0
            ]
        except:
            obj_path = f"<failed to get path: {error_message}>"
        msg = f"Object with path '{obj_path}' not found."
        super().__init__(msg)


class NSXPolicyNotFoundError(Exception):
    def __init__(self, name: str):
        msg = f"policy not found: {name}"
        super().__init__(msg)


class NSXGroupInvalidParametersError(Exception):
    def __init__(self, msg: str = "NSXGroup initialized with incorrect parameters"):
        super().__init__(msg)


class NSXPoliciesNotLoadedError(Exception):
    def __init__(
        self,
        msg: str = "Policies have not been loaded into NSXPolicyManager. Use load_security_policies() first.",
    ):
        super().__init__(msg)


class NSXRuleValidationError(Exception):
    """Raised when the NSXRule is not fully populated"""

    def __init__(self, message: str = "NSXRule is invalid."):
        self.message = message
        super().__init__(self.message)


class NSXUnknownEndpointError(Exception):
    """Raised when the base manager doesn't have a registered endpoint for the given manager type"""

    def __init__(self, manager_type: str):
        self.message = f"Endpoint for manager type '{manager_type}' unknown. You might need to add this endpoint to NSXBaseManager's endpoint_table, or you're using an unsupported manager type."
        super().__init__(self.message)


class NSXExpressionValueEmptyError(Exception):
    """Raised when the NSXExpression[value] is empty"""

    def __init__(self, value: str):
        message = f"value '{value}' cannot be empty"
        super().__init__(message)


class NSXPolicyInvalidNameError(Exception):
    def __init__(self, policy_name: str):
        self.message = f"Policy name '{policy_name}' does not follow convention"
        super().__init__(self.message)


class NSXInvalidIPAddressError(Exception):
    def __init__(self, ipaddress: str):
        self.message = f"IPAddress invalid: '{ipaddress}'"
        super().__init__(self.message)


class NSXExpressionsTooComplicatedError(Exception):
    def __init__(self, group_name: str):
        self.message = f"Expressions are too complicated, not trying: '{group_name}'"
        super().__init__(self.message)


class NSXExpressionComponentNotFoundError(Exception):
    """Raised when the NSXExpression Component is invalid"""

    def __init__(self, component: str, valid_components: list[str]):
        message = (
            f"component '{component}' must be one of: {','.join(valid_components)}"
        )
        super().__init__(message)


class NSXExpressionListConjunctionError(Exception):
    """Raised when the a list of expressions were provided but no conjunction operator was used"""

    def __init__(
        self,
        message: str = "using multiple expressions to create a group is tricky. see the README for an example.",
    ):
        super().__init__(message)


class NSXPolicyAlreadyExistsError(Exception):
    """Raised when the user tries to create a policy that already exists"""

    def __init__(
        self,
        policy_name: str,
    ):
        message = f"policy '{policy_name}' already exists"
        super().__init__(message)


class NSXGroupAlreadyExistsError(Exception):
    """Raised when the user tries to create a group that already exists"""

    def __init__(
        self,
        group_name: str,
    ):
        message = f"group '{group_name}' already exists"
        super().__init__(message)


class NSXServiceAlreadyExistsError(Exception):
    """Raised when the user tries to create a service that already exists"""

    def __init__(
        self,
        service_name: str,
    ):
        message = f"service '{service_name}' already exists"
        super().__init__(message)


class NSXRuleInvalidSourceDestinationGroupsError(Exception):
    """Raised when the user tries to specify a datatype other than String or NSXGroup for source or destination groups for a new NSXRule"""

    def __init__(
        self,
        group,
    ):
        message = f"object of type '{type(group)}' does not match <Union[str, NSXGroup, list[ Union[str, NSXGroup]]]>"
        super().__init__(message)


class NSXPolicyScopeNotFoundError(Exception):
    """Raised when the `scope` property of a policy is referenced but unset"""

    def __init__(
        self,
        policy,
    ):
        message = f"scope for policy '{policy.name()}' is not set. you probably didn't get the policy with the policy manager?"
        super().__init__(message)


class NSXPolicyScopeParseError(Exception):
    """Raised when the `scope` parameter of the policy manager's `new_rule` method is not of type 'Union[str, NSXGroup]'"""

    def __init__(
        self,
        scope,
    ):
        message = f"scope of type '{type(scope)}' needs to be one of [str, NSXGroup]"
        super().__init__(message)


class NSXHTTPError(Exception):
    """Raised when an HTTP request receives a 400-level error"""

    def __init__(
        self,
        response: requests.Response,
    ):
        message = f"""
        response code: {response.status_code}
        response text:
        {response.text}
        """
        super().__init__(message)


class NSXHTTPUnhandledResponseError(Exception):
    """Raised when the HTTP handler receives an unhandled response"""

    def __init__(
        self,
        response: requests.Response,
    ):
        message = f"unhandled response: response.status_code={response.status_code}, response.text={response.text}"
        super().__init__(message)


class NSXUnhandledServiceError(Exception):
    def __init__(self, service: str):
        msg = f"service '{service}' unhandled"
        super().__init__(msg)


class NSXInvalidOutputFormatError(Exception):
    def __init__(self, format: str):
        msg = f"invalid output format: '{format}'"
        super().__init__(msg)


class NSXServiceInvalidParametersError(Exception):
    def __init__(self, msg: str = None):
        if not msg:
            msg = "NSXService initialized with incorrect parameters"
        super().__init__(msg)


class NSXPolicyCreationFailedError(Exception):
    def __init__(self, name: str):
        msg = f"failed to create policy: {name}"
        super().__init__(msg)


class NSXServiceParsingError(Exception):
    def __init__(self, service):
        msg = f"service handler expects one or many strings, or NSXService objects, not type: '{type(service)}'"
        super().__init__(msg)


class NSXServiceRequiredError(Exception):
    def __init__(self):
        msg = f"Service is required"
        super().__init__(msg)


class NSXPolicyHasNoAssociatedGroupError(Exception):
    def __init__(self, name: str):
        msg = f"policy '{name}' does not have a group with the same name."
        super().__init__(msg)


class NSXTagUninitializedError(Exception):
    def __init__(self):
        msg = f"you must instantiate an NSXTag with either <data> or <name>"
        super().__init__(msg)


class NSXDestinationNotFoundError(Exception):
    def __init__(self, msg: str):
        super().__init__(msg)


class NSXInvalidPathError(Exception):
    def __init__(self, msg: str):
        super().__init__(msg)
