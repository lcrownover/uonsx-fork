from __future__ import annotations

import click
from uonsx.error import (
    NSXExpressionIPAddressNotFoundError,
    NSXGroupHasNoTagsError,
    NSXGroupNotFoundError,
    NSXObjectHasDependenciesError,
    NSXTagNotFoundError,
)
from uonsx.util import expand_csl, format_dependency_list

# ---------------------------------------------------------------------------- #
#                                     show                                     #
# ---------------------------------------------------------------------------- #


@click.command()
@click.pass_context
@click.option(
    "--name", "group_name", help="Show membership criteria for the given group"
)
@click.option(
    "--format",
    type=click.Choice(["human", "json"]),
    default="human",
    help="Output format",
)
def show(ctx, group_name, format):
    nsx = ctx.obj["nsx"]
    if not group_name:
        click.echo(nsx.group.output(format))
        return

    try:
        nsxgroup = nsx.group.get(group_name)
    except NSXGroupNotFoundError:
        click.echo(f"Group not found: '{group_name}'")
        exit()

    click.echo(nsxgroup.output(format))


# ---------------------------------------------------------------------------- #
#                                    create                                    #
# ---------------------------------------------------------------------------- #


@click.command()
@click.pass_context
@click.option("--name", "group_name", help="Name of the group to create", required=True)
@click.option(
    "--description", "description", help="Description for the group to be created"
)
@click.option(
    "--ip_address",
    help="Comma-separated list of IP addresses/CIDR to be added to group criteria",
)
@click.option(
    "--owner",
    help="Owner of this group. (dba, nts, cas, ctl)",
    required=True,
)
def create(ctx, group_name, description, ip_address, owner):
    nsx = ctx.obj["nsx"]
    if nsx.cfg.rules.require_ipaddress_for_groups and not ip_address:
        click.echo(f"--ip_address is required when creating groups.")
        exit()
    if nsx.cfg.rules.enforce_convention:
        if not nsx.group.audit_name(group_name):
            click.echo(
                f"Group name '{group_name}' does not follow convention. See NAMING.md"
            )
            exit()
    try:
        nsx.group.get(group_name)
        click.echo(f"Group already exists: '{group_name}'")
        exit()
    except NSXGroupNotFoundError:
        pass
    g = nsx.group.create(name=group_name, description=description)
    if ip_address:
        ip_addrs = expand_csl(ip_address)
        g.add_ipaddress(ip_addrs)
    g.add_tag("owner", owner)
    click.echo(f"Successfully created group: '{group_name}'")


# ---------------------------------------------------------------------------- #
#                                    delete                                    #
# ---------------------------------------------------------------------------- #


@click.command()
@click.pass_context
@click.option("--name", "group_name", help="Name of the group to delete", required=True)
def delete(ctx, group_name):
    nsx = ctx.obj["nsx"]
    try:
        nsx.group.get(group_name)
        nsx.group.delete(name=group_name)
    except NSXGroupNotFoundError:
        click.echo(f"Group doesn't exist: '{group_name}'")
        exit()
    except NSXObjectHasDependenciesError as err:
        click.echo(
            f"Group '{group_name}' cannot be deleted because it's used in the following locations:"
        )
        click.echo(format_dependency_list(err))
        exit()
    click.echo(f"Successfully deleted group: '{group_name}'")


# ---------------------------------------------------------------------------- #
#                                add_ipaddress                                 #
# ---------------------------------------------------------------------------- #


@click.command()
@click.pass_context
@click.option("--name", "group_name", help="Name of the group to modify", required=True)
@click.option(
    "--ip_address",
    help="Comma-separated list of IP Addresses/CIDR to add to the group criteria",
    required=True,
)
def add_ipaddress(ctx, group_name, ip_address):
    nsx = ctx.obj["nsx"]
    try:
        g = nsx.group.get(group_name)
        ip_addrs = expand_csl(ip_address)
        g.add_ipaddress(ip_addrs)
    except NSXGroupNotFoundError:
        click.echo(f"Group doesn't exist: '{group_name}'")
        exit()
    click.echo(f"Successfully modified group: '{group_name}'")


# ---------------------------------------------------------------------------- #
#                                remove_ipaddress                              #
# ---------------------------------------------------------------------------- #


@click.command()
@click.pass_context
@click.option("--name", "group_name", help="Name of the group to modify", required=True)
@click.option(
    "--ip_address",
    help="Comma-separated list of IP Addresses/CIDR to remove from the group criteria. Use 'ALL' to remove all IP address objects.",
    required=True,
)
def remove_ipaddress(ctx, group_name, ip_address):
    nsx = ctx.obj["nsx"]
    try:
        g = nsx.group.get(group_name)
        if ip_address == "ALL":
            g.clear_ipaddresses()
        else:
            ip_addrs = expand_csl(ip_address)
            g.remove_ipaddress(ip_addrs)
    except NSXGroupNotFoundError:
        click.echo(f"Group doesn't exist: '{group_name}'")
        exit()
    except NSXExpressionIPAddressNotFoundError as e:
        click.echo(e.msg)
        exit()
    click.echo(f"Successfully modified group: '{group_name}'")


# ---------------------------------------------------------------------------- #
#                                    add_tag                                   #
# ---------------------------------------------------------------------------- #


@click.command()
@click.pass_context
@click.option("--name", "group_name", help="Name of the group to tag", required=True)
@click.option("--key", help="Key of the tag, also called 'scope'")
@click.option("--value", help="Value of the tag, also called 'name'")
def add_tag(ctx, group_name, key, value):
    nsx = ctx.obj["nsx"]
    try:
        g = nsx.group.get(group_name)
        g.add_tag(key, value)
    except NSXGroupNotFoundError:
        click.echo(f"Group doesn't exist: '{group_name}'")
        exit()
    click.echo(f"Successfully tagged group: '{group_name}'")


# ---------------------------------------------------------------------------- #
#                                    remove_tag                                #
# ---------------------------------------------------------------------------- #


@click.command()
@click.pass_context
@click.option(
    "--name", "group_name", help="Name of the group to remove tags from", required=True
)
@click.option("--key", help="Key of the tag, also called 'scope'")
@click.option("--value", help="Value of the tag, also called 'name'")
def remove_tag(ctx, group_name, key, value):
    nsx = ctx.obj["nsx"]
    try:
        g = nsx.group.get(group_name)
        g.remove_tag(key, value)
    except NSXGroupNotFoundError:
        click.echo(f"Group doesn't exist: '{group_name}'")
        exit()
    except NSXGroupHasNoTagsError:
        click.echo(f"Group has no tags: '{group_name}'")
        exit()
    except NSXTagNotFoundError:
        click.echo(f"Tag '{key}:{value}' not found in group: '{group_name}'")
        exit()
    click.echo(f"Successfully removed tag '{key}:{value}' from group: '{group_name}'")
