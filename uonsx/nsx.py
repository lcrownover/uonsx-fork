from __future__ import annotations

from multiprocessing import Pool
from typing import Union

from uonsx.config import NSXConfig
from uonsx.http import HTTP
from uonsx.manager.bridge_profile import NSXBridgeProfileManager
from uonsx.manager.expression import NSXExpressionManager
from uonsx.manager.group import NSXGroupManager
from uonsx.manager.policy import NSXPolicyManager
from uonsx.manager.router import NSXRouterManager
from uonsx.manager.segment import NSXSegmentManager
from uonsx.manager.segment_port import NSXSegmentPortManager
from uonsx.manager.service import NSXServiceManager
from uonsx.manager.virtualmachine import NSXVirtualMachineManager
from uonsx.manager.tool import NSXToolManager



class NSX:
    def __init__(
        self,
        server: str,
        username: str,
        password: str,
        domain_id: str,
        debug_level: int = 0,
        enforce_convention: bool = True,
        require_ipaddress_for_groups: bool = True,
        mock: bool = False,
    ):
        self.cfg = NSXConfig(
            server=server,
            username=username,
            password=password,
            domain_id=domain_id,
            debug_level=debug_level,
            enforce_convention=enforce_convention,
            require_ipaddress_for_groups=require_ipaddress_for_groups,
            mock=mock,
        )
        self.http = HTTP(self.cfg)
        self.vm = NSXVirtualMachineManager(self.cfg)
        self.policy = NSXPolicyManager(self.cfg)
        self.expression = NSXExpressionManager(self.cfg)
        self.group = NSXGroupManager(self.cfg)
        self.service = NSXServiceManager(self.cfg)
        self.router = NSXRouterManager(self.cfg)
        self.segment = NSXSegmentManager(self.cfg)
        self.segment_port = NSXSegmentPortManager(self.cfg)
        self.bridge_profile = NSXBridgeProfileManager(self.cfg)
        self.tools = NSXToolManager()


    def __str__(self):
        return self.cfg.__str__()
