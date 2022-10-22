from __future__ import annotations

import json
from typing import Union

import requests
import urllib3

urllib3.disable_warnings()

from uonsx.config import NSXConfig
from uonsx.error import (
    NSXHTTPError,
    NSXHTTPUnhandledResponseError,
    NSXObjectAlreadyExistsError,
    NSXObjectHasDependenciesError,
    NSXObjectNotFoundError,
)


class HTTP:

    __instance = None

    @staticmethod
    def get_instance():
        if HTTP.__instance == None:
            raise Exception("HTTP is not initialized")
        return HTTP.__instance

    def __init__(self, cfg: NSXConfig):
        if HTTP.__instance != None:
            raise Exception("use the get_instance() method to use the HTTP handler")
        self.base_url = cfg.base_url
        self.headers = {"Content-Type": "application/json"}
        self.auth = cfg.auth
        self.domain_id = cfg.domain_id
        self.debug = cfg.debug
        self.base_endpoint = self._base_endpoint()
        self.mock = cfg.mock
        HTTP.__instance = self

    def _validate_method(self, method: str):
        valid_methods = ["GET", "POST", "PUT", "PATCH", "DELETE"]
        if method.upper() not in valid_methods:
            raise Exception(f"invalid http method: {method}")

    def _cleanse_endpoint(self, endpoint: str) -> str:
        if endpoint.startswith("/"):
            endpoint = endpoint[1:]
        self.debug.print(2, f"endpoint={endpoint}")
        return endpoint

    def _build_url(self, endpoint: str) -> str:
        url = f"{self.base_url}/{endpoint}"
        self.debug.print(2, f"url={url}")
        return url

    def _cleanse_data(self, data: Union[str, dict] = None) -> Union[str, None]:
        if isinstance(data, dict):
            return json.dumps(data)
        self.debug.print(3, f"data={data}")
        return data

    def _parse_response(self, response: requests.Response) -> dict:
        self.debug.print(1, f"response.status_code={response.status_code}")
        if str(response.status_code).startswith("4"):
            r = json.loads(response.text)
            if "may not have been realized on enforcement point" in r["error_message"]:
                raise NSXObjectNotFoundError(r["error_message"])
            if "as it already exists" in r["error_message"]:
                raise NSXObjectAlreadyExistsError(r["error_message"])
            if (
                "cannot be deleted as either it has children or it is being referenced by other objects"
                in r["error_message"]
            ):
                raise NSXObjectHasDependenciesError(r["error_message"])
            if "credentials were incorrect" in r["error_message"]:
                print(r["error_message"])
                exit(1)
            if str(r["error_code"]) == "600":
                if (
                    "could not be found. Object identifiers are case sensitive"
                    in r["error_message"]
                ):
                    raise NSXObjectNotFoundError(r["error_message"])
            raise NSXHTTPError(response)
        if response.text:
            self.debug.print(4, f"{response.text}")
            return json.loads(response.text)
        if str(response.status_code).startswith("2") and not response.text:
            return {"status": "success"}
        raise NSXHTTPUnhandledResponseError(response)

    def _base_endpoint(
        self,
        base_api: str = "policy",
        api_version: str = "v1",
        domain_id: str = "",
    ) -> str:
        if not domain_id:
            domain_id = self.domain_id
        self.debug.print(
            3,
            f"building base endpoint: base_api={base_api}, api_version={api_version}, domain_id={domain_id}",
        )
        endpoint = f"/{base_api}/api/{api_version}/infra/domains/{domain_id}"
        return endpoint

    def _method_switch(self, method: str):
        self.debug.print(1, f"http method: {method}")
        if method == "GET":
            return requests.get
        if method == "POST":
            return requests.post
        if method == "PUT":
            return requests.put
        if method == "PATCH":
            return requests.patch
        if method == "DELETE":
            return requests.delete

    def _make_request(
        self, f, url: str, headers: dict, auth: tuple[str, str], data: str = None
    ):
        return f(url, headers=headers, auth=auth, data=data, verify=False)

    def request(
        self, method: str, endpoint: str, data: Union[dict, str, None] = None
    ) -> dict:
        """
        Perform an http request of type `method` against a given endpoint and return a JSON dict
        """

        self._validate_method(method)

        endpoint = self._cleanse_endpoint(endpoint)
        url = self._build_url(endpoint)

        data = self._cleanse_data(data)

        func = self._method_switch(method.upper())

        if self.mock:
            return {}

        resp = self._make_request(
            func, url=url, headers=self.headers, auth=self.auth, data=data
        )

        return self._parse_response(resp)
