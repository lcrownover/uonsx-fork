from __future__ import annotations

import click
from uonsx.error import NSXGroupNotFoundError


@click.command()
@click.pass_context
@click.option('--tier', help="Show tier routers only")
def show(ctx, tier):
    nsx = ctx.obj["nsx"]
    if not tier:
        click.echo(nsx.router.all_routers_table())
        exit()
    elif tier == "0":
        click.echo(nsx.router.all_tier0s_table())
        exit()
    elif tier == "1":
        click.echo(nsx.router.all_tier1s_table())
        exit()
