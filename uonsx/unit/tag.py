from __future__ import annotations

import json
from pprint import pformat
from typing import Union

from uonsx.error import NSXTagUninitializedError
from uonsx.util import strfmt


class NSXTag:
    """
    Wrapper/Constructor for NSX Tags

    example:
    {
      "scope": "os",
      "tag": "windows",
    }
    """

    def __init__(self, name: str = "", scope: str = "", data: dict = {}):
        if not name and not data:
            raise NSXTagUninitializedError
        if name:
            self.data = {"tag": name, "scope": scope}
        if data:
            self.data = data

    def __repr__(self) -> str:
        return json.dumps(self.__dict__())

    def __str__(self) -> str:
        return strfmt(json.dumps(self.__dict__()))

    def __dict__(self) -> dict:
        return self.dump()

    def dump(self) -> dict:
        return self.data

    def to_json(self) -> str:
        return json.dumps(self.dump())

    def pformat(self) -> str:
        return pformat(self.dump())

    def name(self) -> str:
        return self.data["tag"]

    def scope(self) -> str:
        return self.data["scope"]

    def tag_dict(self) -> dict:
        return {"tag": self.name(), "scope": self.scope()}

    def tagged_count(self) -> Union[int, None]:
        tagged_objects_count = self.data.get("tagged_objects")
        if tagged_objects_count:
            return int(tagged_objects_count)
        return None
