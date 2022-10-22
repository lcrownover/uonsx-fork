from __future__ import annotations

import click
from uonsx.unit.group import NSXGroup

# ---------------------------------------------------------------------------- #
#                                    rule-scope                                #
# ---------------------------------------------------------------------------- #


@click.command()
@click.pass_context
@click.option(
    "--fix",
    is_flag=True,
    default=False,
    help="Automatically fix the scopes",
)
def rule_scope(ctx, fix):
    nsx = ctx.obj["nsx"]
    nsx.tools.rule_scope(nsx, fix)
