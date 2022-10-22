from __future__ import annotations

import click
from uonsx.error import NSXSegmentNotFoundError

# ---------------------------------------------------------------------------- #
#                                     show                                     #
# ---------------------------------------------------------------------------- #

@click.command()
@click.pass_context
@click.option(
    "--segment_name",
    help="Show config for a specific segment",
    required=True
)
def show(ctx, segment_name):
    nsx = ctx.obj["nsx"]
    if not segment_name:
        click.echo(nsx.segment.all_segments_table())
        exit()
    try:
        nsxsegment = nsx.segment.get(segment_name)
    except NSXSegmentNotFoundError:
        click.echo(f"Segment not found: '{segment_name}'")
        exit()

    # preload the groups and services
    with click.progressbar(
        [nsx.segment],
        label="Gathering NSX objects",
        length=2,
    ) as bar:
        for operation in bar:
            operation.get_all()

    click.echo("")
    click.echo(f"Segment Name:  {nsxsegment.name()}")
    click.echo(nsxsegment.all_segments_table())


# ---------------------------------------------------------------------------- #
#                                     show                                     #
# ---------------------------------------------------------------------------- #

@click.command()
@click.pass_context
@click.option(
    "--segment_name",
    help="Segment to connect",
    required=True,
)
@click.option(
    "--t1_name",
    help="T1 Gateway to connect to",
    required=True,
)
def connect_t1(ctx, segment_name):
    nsx = ctx.obj["nsx"]
    if not segment_name:
        click.echo(nsx.segment.all_segments_table())
        exit()
    try:
        nsxsegment = nsx.segment.get(segment_name)
    except NSXSegmentNotFoundError:
        click.echo(f"Segment not found: '{segment_name}'")
        exit()

    # preload the groups and services
    with click.progressbar(
        [nsx.segment],
        label="Gathering NSX objects",
        length=2,
    ) as bar:
        for operation in bar:
            operation.get_all()

    click.echo("")
    click.echo(f"Segment Name:  {nsxsegment.name()}")
    click.echo(nsxsegment.all_segments_table())
