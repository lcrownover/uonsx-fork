#!/usr/bin/env python3

from __future__ import annotations

import click
import getpass

import uonsx
import uonsx.cli.group as group_cli
import uonsx.cli.policy as policy_cli
import uonsx.cli.router as router_cli
import uonsx.cli.segment as segment_cli
import uonsx.cli.segment_port as segment_port_cli
import uonsx.cli.service as service_cli
import uonsx.cli.virtualmachine as vm_cli
import uonsx.cli.tools as tools_cli


def setup(
    cli_server,
    cli_username,
    cli_password,
    cli_domain_id,
    cli_debug_level,
    cli_enforce_convention,
    cli_require_ipaddress_for_groups,
) -> uonsx.NSX:
    cfg = uonsx.NSXConfig(
        server=cli_server,
        username=cli_username,
        password=cli_password,
        domain_id=cli_domain_id,
        debug_level=cli_debug_level,
        enforce_convention=cli_enforce_convention,
        require_ipaddress_for_groups=cli_require_ipaddress_for_groups,
    )
    nsx = uonsx.NSX(
        server=cfg.server,
        username=cfg.username,
        password=cfg.password,
        domain_id=cfg.domain_id,
        debug_level=cfg.debug_level,
        enforce_convention=cfg.rules.enforce_convention,
        require_ipaddress_for_groups=cfg.rules.require_ipaddress_for_groups,
    )
    return nsx


@click.group()
@click.option("--server", default=None, help="FQDN of server to connect to")
@click.option("--username", default=None, help="Username")
@click.option("--password", default=None, help="Password")
@click.option("--password_prompt", is_flag=True, default=False, help="Password Prompt")
@click.option("--domain_id", default=None, help="Domain ID")
@click.option("--debug_level", default=0, type=click.INT, help="debug level [0-4]")
@click.option(
    "--enforce_convention/--no_enforce_convention",
    default=True,
    is_flag=True,
    help="Enforce the naming convention during operation",
)
@click.option(
    "--require_ipaddress_for_groups/--no_require_ipaddress_for_groups",
    default=True,
    is_flag=True,
    help="Require an IP address when creating groups",
)
@click.pass_context
def cli(
    ctx,
    server,
    username,
    password,
    password_prompt,
    domain_id,
    debug_level,
    enforce_convention,
    require_ipaddress_for_groups,
):
    ctx.ensure_object(dict)
    ctx.allow_extra_args = True
    ctx.ignore_unknown_options = True
    if password_prompt:
        password = getpass.getpass("nsx password: ")
    ctx.obj["nsx"] = setup(
        cli_server=server,
        cli_username=username,
        cli_password=password,
        cli_domain_id=domain_id,
        cli_debug_level=debug_level,
        cli_enforce_convention=enforce_convention,
        cli_require_ipaddress_for_groups=require_ipaddress_for_groups,
    )


@cli.group()
def group():
    pass


group.add_command(group_cli.show)
group.add_command(group_cli.create)
group.add_command(group_cli.delete)
group.add_command(group_cli.add_ipaddress)
group.add_command(group_cli.remove_ipaddress)
group.add_command(group_cli.add_tag)
group.add_command(group_cli.remove_tag)


@cli.group()
def policy():
    pass


policy.add_command(policy_cli.show)
policy.add_command(policy_cli.create)
policy.add_command(policy_cli.delete)
policy.add_command(policy_cli.clone)
policy.add_command(policy_cli.add_rule)
policy.add_command(policy_cli.remove_rule)


@cli.group()
def service():
    pass


service.add_command(service_cli.show)
service.add_command(service_cli.create)
service.add_command(service_cli.delete)


@cli.group()
def vm():
    pass


# vm.add_command(vm_cli.show)
vm.add_command(vm_cli.add_tag)
vm.add_command(vm_cli.remove_tag)
vm.add_command(vm_cli.show_rules)


@cli.group()
def router():
    pass


router.add_command(router_cli.show)


@cli.group()
def segment():
    pass


segment.add_command(segment_cli.show)


@cli.group()
def segment_port():
    pass


segment_port.add_command(segment_port_cli.show)


@cli.group()
def tools():
    pass


tools.add_command(tools_cli.rule_scope)

if __name__ == "__main__":
    cli(obj={})
