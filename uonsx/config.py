from __future__ import annotations

import configparser
import json
import yaml
import os
from typing import Union
import getpass

from uonsx.debug import Debug
from uonsx.error import NSXMissingConfigurationItemError
from uonsx.util import strfmt


def _merge_arg(arg_name, priority_list: list[Union[str, int, None]] = []):
    """Returns first valid item in priority list. Raise if none are valid."""
    for item in priority_list:
        if item is not None:
            return item
    raise NSXMissingConfigurationItemError(arg_name)


def _str_to_l(s):
    """Returns a list of strings from the given comma-separated string"""
    if s is None:
        return []
    return [i.strip() for i in s.split(",") if i.strip()]


class NSXConfigAudit:
    def __init__(self):
        self.valid_prefixes = []
        self.valid_vrfs = []
        self.ignored_groups = []
        self.ignored_policies = []


class NSXConfigRules:
    def __init__(self):
        self.enforce_convention = True
        self.require_ipaddress_for_groups = True


class NSXConfig:
    valid_config_paths = [
        os.path.join(os.path.expanduser("~"), ".uonsx", "config.yaml"),
        os.path.join(os.path.expanduser("~"), ".config", "uonsx", "config.yaml"),
    ]

    def __init__(
        # These are None because of _merge_arg
        self,
        server: str = None,
        username: str = None,
        password: str = None,
        domain_id: str = None,
        debug_level: int = 0,
        enforce_convention: bool = None,
        require_ipaddress_for_groups: bool = None,
        mock: bool = False,
    ):
        self.mock = mock
        self.debug_level = debug_level
        self.enforce_convention = enforce_convention
        self.require_ipaddress_for_groups = require_ipaddress_for_groups
        self.audit = NSXConfigAudit()
        self.rules = NSXConfigRules()
        """
        If all required parameters are configured,
        don't try to read any configuration file.
        """
        self.server = server
        self.username = username
        self.password = password
        self.domain_id = domain_id

        if all([self.server, self.username, self.password, self.domain_id]):
            config = {}
            # print("skipping config")
        else:
            # Otherwise, load in the config
            # print("loading config")
            config = self._load_config()
        self._configure(config)

    def _load_config(self):
        """
        Not all required args were passed, go to process the config file.

        Reads config file and merges settings into one NSXConfig object,
        prioritizing any values passed in as parameters.
        """
        try:
            config_path = self.find_config()
        except FileNotFoundError:
            self.prompt_for_config()
        try:
            config_path = self.find_config()
        except FileNotFoundError:
            exit(1)

        env_username = os.getenv("NSX_USERNAME")
        env_password = os.getenv("NSX_PASSWORD")

        with open(config_path, "r") as f:
            config = yaml.safe_load(f)

        self.server = str(_merge_arg("server", [self.server, config.get("server")]))
        self.username = str(
            _merge_arg(
                "username", [self.username, env_username, config.get("username")]
            )
        )
        self.password = str(
            _merge_arg(
                "password", [self.password, env_password, config.get("password")]
            )
        )
        self.domain_id = str(
            _merge_arg("domaind_id", [self.domain_id, config.get("domain_id")])
        )
        self.debug_level = int(
            _merge_arg("debug_level", [self.debug_level, config.get("debug_level"), 0])
        )

        if not self.username:
            print(
                "username not found. use either $NSX_USERNAME environment variable or config file."
            )
            exit(1)
        if not self.password:
            print(
                "password not found. use either $NSX_PASSWORD environment variable or config file."
            )
            exit(1)
        return config

    def _configure(self, config):
        """
        Configure the more obscure settings using the config map (which can be empty)
        """
        # Auditing settings
        if config.get("audit"):
            self.audit.valid_prefixes = config["audit"].get("prefixes", None)
            self.audit.valid_vrfs = config["audit"].get("vrfs", None)
            self.audit.ignored_groups = config["audit"].get("ignore_groups", None)
            self.audit.ignored_policies = config["audit"].get("ignore_policies", None)

        # Rules settings
        self.rules.enforce_convention = bool(
            _merge_arg(
                "enforce_convention",
                [self.enforce_convention, config.get("enforce_convention"), True],
            )
        )
        self.rules.require_ipaddress_for_groups = bool(
            _merge_arg(
                "require_ipaddress_for_groups",
                [
                    self.require_ipaddress_for_groups,
                    config.get("require_ipaddress_for_groups"),
                    True,
                ],
            )
        )

        self.base_url = f"https://{self.server}"
        self.debug = Debug(int(self.debug_level))
        self.auth = (self.username, self.password)

    def __repr__(self):
        out = {}
        for k, v in self.__dict__.items():
            if k == "password":
                out["password"] = "********"
                continue
            if k == "debug":
                out["debug"] = bool(self.debug)
                continue
            if k == "auth":
                continue
            out[k] = v
        return json.dumps(out)

    def __str__(self):
        return strfmt(self.__repr__())

    def get(self, attr: str, fallback=None):
        """Reimplementation of dict.get()"""
        try:
            return getattr(self, attr)
        except:
            return fallback

    def find_config(self) -> str:
        """Returns path to the first config file found in valid paths"""
        for path in self.valid_config_paths:
            if os.path.isfile(path):
                return path
        raise FileNotFoundError("uonsx config file not found")

    def prompt_for_config(self) -> None:
        print("No config file found at any of the following locations:")
        for p in self.valid_config_paths:
            print(f"  {p}")
        ans = input("Would you like to create a new config file? [yes]: ")
        if ans.lower() in ["", "yes", "y"]:
            self.generate_new_config()
        return None

    def generate_new_config(self) -> None:
        path = self.valid_config_paths[0]

        config = {}
        default_server = "myserver.example.org"
        default_domain_id = "default"
        default_valid_prefixes = ["fn", "mem"]
        default_valid_suffixes = ["DATA"]
        default_vrfs = ["DATA"]
        default_ignore_groups = [
            "NLB.PoolLB.[vra-...-pool][reg-...-lb01]",
            "NLB.PoolLB.[vrop...-pool][reg-...-lb01]",
            "NLB.PoolLB.[wsa-...-pool][reg-...-lb01]",
            "NLB.VIP.[vra-http-redirect]",
            "NLB.VIP.[vra-https]",
            "NLB.VIP.[vrops-http-redirect]",
            "NLB.VIP.[vrops-https]",
            "NLB.VIP.[wsa-http-redirect]",
            "NLB.VIP.[wsa-https]",
            "VCF-Created-Virtual-Machines",
        ]

        config["server"] = default_server
        server = input(f"nsx server [{default_server}]: ").strip()
        if server:
            config["server"] = server

        config["domain_id"] = default_domain_id

        print("You will now be prompted for your username and password.")
        print("Your credentials will be stored in plaintext in your config file.")
        print(
            "Make sure to modify the permissions of this file (`chmod 0600`) to secure it after it has been generated."
        )
        print(
            "If you'd prefer to use the environment variables NSX_USERNAME and NSX_PASSWORD,"
        )
        print("leave the following inputs blank.")
        print(
            "Otherwise, your username should be in the format: username@example.org"
        )
        config["username"] = input("nsx username [none]: ").strip()
        config["password"] = getpass.getpass("nsx password [none]: ").strip()

        config["enforce_convention"] = True
        config["debug_level"] = 0

        config["audit"] = {
            "prefixes": default_valid_prefixes,
            "suffixes": default_valid_suffixes,
            "vrfs": default_vrfs,
            "ignore_groups": default_ignore_groups,
            "ignore_policies": [],
        }

        config["rules"] = {
            "enforce_convention": True,
            "require_ipaddress_for_groups": True,
        }

        parent_path = os.path.join(os.path.expanduser("~"), ".uonsx")
        try:
            if not os.path.isdir(parent_path):
                os.makedirs(parent_path)
        except:
            print(f"Failed to create parent path: {parent_path}")

        try:
            with open(path, "w") as f:
                f.write(yaml.dump(config, sort_keys=False))
            print(f"Config saved to: {path}")
        except Exception as e:
            print(f"Failed to open file path: {path}")
            print(e)
            exit(1)
