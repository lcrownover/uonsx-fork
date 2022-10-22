from __future__ import annotations

import click
from uonsx.error import NSXVirtualMachineNotFoundError, NSXGroupNotFoundError, NSXPolicyNotFoundError
from uonsx.unit.tag import NSXTag

# ---------------------------------------------------------------------------- #
#                                     show                                     #
# ---------------------------------------------------------------------------- #


# @click.command()
# @click.pass_context
# @click.option("--name", "vm_name", help="Show details for a specific Virtual Machine")
# @click.option(
#     "--format",
#     type=click.Choice(["human", "json"]),
#     default="human",
#     help="Output format",
# )
# def show(ctx, vm_name, format):
#     nsx = ctx.obj["nsx"]
#     if not vm_name:
#         click.echo(nsx.vm.output(format))
#         return
#
#     try:
#         nsxvm = nsx.vm.get(vm_name)
#     except NSXVirtualMachineNotFoundError:
#         click.echo(f"Virtual Machine not found: '{vm_name}'")
#         exit()
#
#     click.echo(nsxvm.output(format))


# ---------------------------------------------------------------------------- #
#                                   add_tag                                    #
# ---------------------------------------------------------------------------- #


@click.command()
@click.pass_context
@click.option(
    "--name",
    "vm_name",
    help="Name of the virtual machine that should be tagged",
    required=True,
)
@click.option(
    "--tag",
    help="Tag that should be added to the virtual machine",
    required=True,
)
@click.option(
    "--scope",
    help="Scope of the tag, usually not used",
    default="",
)
def add_tag(
    ctx,
    vm_name,
    tag,
    scope,
):
    nsx = ctx.obj["nsx"]

    # Validate VM
    try:
        nsxvm = nsx.vm.get(vm_name)
    except NSXVirtualMachineNotFoundError:
        click.echo(f"Virtual Machine doesn't exist: '{vm_name}'")
        exit()

    # Validate tag
    try:
        nsxtag = NSXTag(name=tag, scope=scope)
    except:
        click.echo(f"Invalid tag: '{scope}|{tag}'")
        exit()

    try:
        nsx.vm.add_tag(virtualmachine=nsxvm, tag=nsxtag)
        click.echo(f"Successfully tagged Virtual Machine '{vm_name}' with tag '{tag}'")

    except Exception as e:
        click.echo(e)
        exit()


# ---------------------------------------------------------------------------- #
#                                  remove_tag                                  #
# ---------------------------------------------------------------------------- #


@click.command()
@click.pass_context
@click.option(
    "--name",
    "vm_name",
    help="Name of the virtual machine where the tag resides",
    required=True,
)
@click.option(
    "--tag",
    help="Tag that should be removed from the virtual machine",
    required=True,
)
@click.option(
    "--scope",
    help="Scope of the tag, if it exists",
    default="",
)
def remove_tag(
    ctx,
    vm_name,
    tag,
    scope,
):
    nsx = ctx.obj["nsx"]

    # Validate VM
    try:
        nsxvm = nsx.vm.get(vm_name)
    except NSXVirtualMachineNotFoundError:
        click.echo(f"Virtual Machine doesn't exist: '{vm_name}'")
        exit()

    # Validate tag
    try:
        nsxtag = NSXTag(name=tag, scope=scope)
    except:
        click.echo(f"Invalid tag: '{scope}|{tag}'")
        exit()

    try:
        nsx.vm.remove_tag(virtualmachine=nsxvm, tag=nsxtag)
        click.echo(f"Successfully removed tag '{tag}' from Virtual Machine '{vm_name}'")

    except Exception as e:
        click.echo(e)
        exit()


# ---------------------------------------------------------------------------- #
#                                   show_rules                                 #
# ---------------------------------------------------------------------------- #


@click.command()
@click.pass_context
@click.option(
    "--name",
    "vm_name",
    help="Name of the virtual machine",
    required=True,
)
@click.option(
    "--format",
    type=click.Choice(["human", "json"]),
    default="human",
    help="Output format",
)
def show_rules(
    ctx,
    vm_name,
    format,
):
    nsx = ctx.obj["nsx"]

    # Validate VM
    try:
        nsxvm = nsx.vm.get(vm_name)
    except NSXVirtualMachineNotFoundError:
        click.echo(f"Virtual Machine doesn't exist: '{vm_name}'")
        exit()

    # Get tags for VM
    for tag in nsxvm.tags():
        try:
            group = nsx.group.get(tag.name())
        except NSXGroupNotFoundError:
            continue
        try:
            policy = nsx.policy.get(group.name())
        except NSXPolicyNotFoundError:
            continue

        click.echo(policy.output(format))

