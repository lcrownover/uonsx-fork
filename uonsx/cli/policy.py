from __future__ import annotations

import click
from uonsx.error import (
    NSXGroupNotFoundError,
    NSXInvalidGroupError,
    NSXInvalidPathError,
    NSXInvalidPortProtocolError,
    NSXObjectNotFoundError,
    NSXPolicyInvalidNameError,
    NSXPolicyNotFoundError,
    NSXRuleNotFoundError,
    NSXServiceNotFoundError,
)
from uonsx.unit.rule import NSXRule

# ---------------------------------------------------------------------------- #
#                                    show                                      #
# ---------------------------------------------------------------------------- #


@click.command()
@click.pass_context
@click.option("--name", "policy_name", help="Show rules for a specific policy")
@click.option(
    "--format",
    type=click.Choice(["human", "json"]),
    default="human",
    help="Output format",
)
def show(ctx, policy_name, format):
    nsx = ctx.obj["nsx"]

    # `show` can be run without a policy name in order to show all policies
    if not policy_name:
        click.echo(nsx.policy.output(format=format))
        return

    # Single policy was provided
    try:
        nsxpolicy = nsx.policy.get(policy_name)
    except NSXPolicyNotFoundError:
        click.echo(f"Policy not found: '{policy_name}'")
        exit()

    click.echo(nsxpolicy.output(format=format))


# ---------------------------------------------------------------------------- #
#                                   create                                     #
# ---------------------------------------------------------------------------- #


@click.command()
@click.pass_context
@click.option(
    "--name", "policy_name", help="Name of the policy to create", required=True
)
@click.option("--description", help="Description for the policy to be created")
@click.option(
    "--destination_group",
    help="Name of the destination group that all the rules should use",
)
@click.option(
    "--category",
    help="DFW Category the policy should be created in. Default is Application",
)
@click.option(
    "--create_group",
    is_flag=True,
    default=False,
    help="Create the matching destination group for this policy if not found",
)
@click.option(
    "--ip_address",
    help="IP Address of the group member. Required if using --create-group",
)
@click.option(
    "--owner",
    help="Owner of this group (dba, nts, cas, ctl). Required if using --create-group",
)
def create(
    ctx,
    policy_name,
    description,
    destination_group,
    category,
    create_group,
    ip_address,
    owner,
):
    nsx = ctx.obj["nsx"]

    if nsx.cfg.rules.enforce_convention:
        if not nsx.policy.audit_name(policy_name):
            click.echo(
                f"Policy name '{policy_name}' does not follow convention. See NAMING.md"
            )
            exit()

    if nsx.cfg.rules.require_ipaddress_for_groups:
        if create_group and not ip_address:
            click.echo(f"--ip_address is required when creating groups.")
            exit()

    if create_group and not owner:
        click.echo(f"--owner is required when creating groups.")
        exit()

    try:
        nsx.policy.get(policy_name)
        click.echo(f"Policy already exists: '{policy_name}'")
        exit()
    except NSXPolicyNotFoundError:
        pass

    if not destination_group:
        destination_group = policy_name

    try:
        nsxdestgroup = nsx.group.get(destination_group)
    except NSXGroupNotFoundError:
        if create_group:
            nsxdestgroup = nsx.group.create(name=destination_group)
            nsxdestgroup.add_ipaddress(ip_address)
            nsxdestgroup.add_tag("owner", owner)
            click.echo(f"Successfully created group: '{nsxdestgroup.name()}'")
        else:
            click.echo(f"Destination group not found: '{destination_group}'")
            exit()

    if not category:
        category = "Application"

    nsx.policy.create(
        name=policy_name,
        description=description,
        destination_group=nsxdestgroup,
        category=category,
    )
    click.echo(f"Successfully created policy: '{policy_name}'")


# ---------------------------------------------------------------------------- #
#                                    delete                                    #
# ---------------------------------------------------------------------------- #


@click.command()
@click.pass_context
@click.option(
    "--name", "policy_name", help="Name of the policy to delete", required=True
)
@click.option(
    "--delete_group",
    is_flag=True,
    default=False,
    help="Delete the matching destination group for this policy if found",
)
def delete(ctx, policy_name, delete_group):
    nsx = ctx.obj["nsx"]
    try:
        nsx.policy.get(policy_name)
    except NSXPolicyNotFoundError:
        click.echo(f"Policy doesn't exist: '{policy_name}'")
    try:
        nsx.policy.delete(policy_name)
        click.echo(f"Successfully deleted policy: '{policy_name}'")
    except:
        click.echo(f"Failed to delete policy: '{policy_name}'")
    if delete_group:
        try:
            nsx.group.delete(policy_name)
            click.echo(f"Successfully deleted group: '{policy_name}'")
        except NSXGroupNotFoundError:
            pass


# ---------------------------------------------------------------------------- #
#                                    clone                                     #
# ---------------------------------------------------------------------------- #


@click.command()
@click.pass_context
@click.option(
    "--name", "policy_name", help="Name of the policy to create", required=True
)
@click.option("--description", help="Description for the policy to be created")
@click.option(
    "--source_policy", help="Name of the policy to copy from", required=True
)
def clone(ctx, policy_name, description, source_policy):
    nsx = ctx.obj["nsx"]

    try:
        sp = nsx.policy.get(source_policy)
    except NSXPolicyNotFoundError:
        click.echo(f"Source Policy doesn't exist: '{source_policy}'")
        exit()

    try:
        dg = nsx.group.get(policy_name)
    except NSXGroupNotFoundError:
        click.echo(f"Destination group not found: '{policy_name}'")
        exit()

    np = nsx.policy.create(
        name=policy_name,
        description=description,
        destination_group=policy_name,
        category=sp.category(),
    )
    click.echo(f"Successfully created policy: '{policy_name}'")

    for rule in sp.rules():
        np.add_rule(
            name=rule.name(),
            source_group=rule.source_groups(),
            destination_group=dg,
            action=rule.action(),
            service=rule.services_str(),
        )
        click.echo(f"Successfully added rule: '{rule.name()}'")

    click.echo(f"Successfully cloned policy: '{policy_name}'")


# ---------------------------------------------------------------------------- #
#                                  add_rule                                    #
# ---------------------------------------------------------------------------- #


@click.command()
@click.pass_context
@click.option(
    "--policy_name",
    "policy_name",
    help="Name of the policy that contains the rule to be added.",
    required=True,
)
@click.option(
    "--name",
    "rule_name",
    help="Name of the rule to be added. No convention required, make this descriptive.",
    required=True,
)
@click.option(
    "--source_group",
    help='Name of the source group, IP Address, CIDR, or "ANY"',
    required=True,
)
@click.option(
    "--destination_group",
    help="Name of the destination group",
)
@click.option(
    "--action",
    type=click.Choice(
        ["ALLOW", "DROP", "REJECT", "JUMP_TO_APPLICATION"], case_sensitive=False
    ),
    default="ALLOW",
    help='Action of the rule. Default: "ALLOW"',
)
@click.option(
    "--service",
    help="Service for the rule. This can be a valid NSX Service name, or a raw port protocol string: TCP_443",
    required=True,
)
@click.option(
    "--before",
    type=click.INT,
    help="Create the rule just before the specified handle. Default: Append rule to end of policy.",
)
@click.option(
    "--after",
    type=click.INT,
    help="Create the rule just after the specified handle. Default: Append rule to end of policy.",
)
@click.option(
    "--logged",
    is_flag=True,
    default=False,
    help="Log the rule or not. Default: False",
)
def add_rule(
    ctx,
    policy_name,
    rule_name,
    source_group,
    destination_group,
    action,
    service,
    before,
    after,
    logged,
):
    nsx = ctx.obj["nsx"]

    # Validate Policy name
    try:
        policy = nsx.policy.get(policy_name)
    except NSXPolicyNotFoundError:
        click.echo(f"Policy doesn't exist: '{policy_name}'")
        exit()

    # Validate before/after
    sequence_number = None
    if before and after:
        click.echo(f"use only one of: --before, --after")
        exit()
    if before:
        sequence_number = policy._get_sequence_number_before_handle(before)
    if after:
        sequence_number = policy._get_sequence_number_after_handle(after)

    # Validate Source Group
    try:
        sgs = [g.strip() for g in source_group.split(",")]
        v_source_groups = [nsx.group.get(source_group) for g in sgs if g != "ANY"]
        if "ANY" in sgs:
            v_source_groups.append("ANY")
    except NSXGroupNotFoundError:
        click.echo(f"source_group not found: '{source_group}'")
        exit()

    # Validate Destination Group
    try:
        if not destination_group:
            destination_group = policy_name
        dgs = [g.strip() for g in destination_group.split(",")]
        v_destination_groups = [
            nsx.group.get(destination_group) for g in dgs if g != "ANY"
        ]
        if "ANY" in dgs:
            v_destination_groups.append("ANY")
    except NSXGroupNotFoundError:
        click.echo(f"destination_group not found: '{destination_group}'")
        exit()

    # Validate Action
    if not action:
        v_action = "ALLOW"
    else:
        v_action = action.upper()
        if v_action not in NSXRule.valid_actions:
            click.echo(
                f"invalid action '{action}', valid actions: [{', '.join(NSXRule.valid_actions)}]"
            )
            exit()

    # Validate Service
    v_services = [s.strip() for s in service.split(",")]

    try:
        policy.add_rule(
            name=rule_name,
            source_group=v_source_groups,
            destination_group=v_destination_groups,
            action=v_action,
            service=v_services,
            sequence_number=sequence_number,
            logged=logged,
        )
        click.echo(f"Successfully added rule: '{rule_name}'")

    except NSXServiceNotFoundError as e:
        click.echo(e)
        exit()

    except NSXInvalidPortProtocolError as e:
        click.echo(e)
        exit()


# ---------------------------------------------------------------------------- #
#                                 remove_rule                                  #
# ---------------------------------------------------------------------------- #


@click.command()
@click.pass_context
@click.option(
    "--name",
    "policy_name",
    help="Name of the policy that contains the rule to be removed.",
)
@click.option(
    "--handle",
    help="Handle of the rule to be removed. Use the `show` command to find the handles for rules in a policy.",
)
@click.option(
    "--path",
    help="Object path of the rule to be deleted. Overrides policy_name and handle.",
)
def remove_rule(ctx, policy_name, handle, path):
    nsx = ctx.obj["nsx"]
    if path:
        if policy_name or handle:
            click.echo(f"If using --path, do not provide a --policy_name or --handle.")
            exit()
        try:
            nsx.policy.remove_rule_by_path(path)
            click.echo(f"Successfully removed rule: '{path}'")
        except NSXObjectNotFoundError:
            click.echo(f"Rule path not found: '{path}'")
        exit()
    if policy_name and handle:
        try:
            policy = nsx.policy.get(policy_name)
            handles = [int(h.strip()) for h in handle.split(",") if h.strip()]
            for h in handles:
                policy.remove_rule(handle=h)
                click.echo(f"Successfully removed rule: '{h}'")
        except ValueError:
            click.echo(f"Invalid handle '{handle}', handle must be an integer or comma-separated list of integers.")
        except NSXPolicyNotFoundError:
            click.echo(f"Policy doesn't exist: '{policy_name}'")
        except NSXRuleNotFoundError:
            click.echo(f"Rule not found with handle: '{handle}'")
        exit()
    click.echo(f"You must provide --policy_name and --handle if not using --path.")
    exit()
