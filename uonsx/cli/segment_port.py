from __future__ import annotations

import click
from uonsx.error import NSXSegmentPortNotFoundError


@click.command()
@click.pass_context
@click.option("--segment_name", help="Show ports connected to a specific segment")
def show(ctx, segment_name):
    nsx = ctx.obj["nsx"]
    try:
        nsx.segment_port.get_all_ports(segment_name)
    except NSXSegmentPortNotFoundError:
        click.echo(f"Segment not found: '{segment_name}'")
        exit()

    click.echo("")
    click.echo(f"Segment Name:  {segment_name}")
    click.echo(nsx.segment_port.all_ports_table())
