from __future__ import annotations

import click
from uonsx.error import NSXObjectHasDependenciesError, NSXServiceNotFoundError
from uonsx.util import format_dependency_list

# ---------------------------------------------------------------------------- #
#                                     show                                     #
# ---------------------------------------------------------------------------- #


@click.command()
@click.pass_context
@click.option("--name", "service_name", help="Show details for a specific service")
@click.option(
    "--format",
    type=click.Choice(["human", "json"]),
    default="human",
    help="Output format",
)
def show(ctx, service_name, format):
    nsx = ctx.obj["nsx"]

    if not service_name:
        click.echo(nsx.service.output(format))
        return

    try:
        nsxservice = nsx.service.get(service_name)
    except NSXServiceNotFoundError:
        click.echo(f"Service not found: '{service_name}'")
        exit()

    click.echo(nsxservice.output(format))


# ---------------------------------------------------------------------------- #
#                                    create                                    #
# ---------------------------------------------------------------------------- #


@click.command()
@click.pass_context
@click.option("--name", "service_name", help="Name of the service to create", required=True)
@click.option("--description", help="Description for the service to be created")
@click.option(
    "--services",
    help="Comma-separated list of Port-Protocols to use for this service",
    required=True,
)
def create(ctx, service_name, description, services):
    nsx = ctx.obj["nsx"]
    try:
        nsx.service.get(service_name)
        click.echo(f"service already exists: '{service_name}'")
        exit()
    except NSXServiceNotFoundError:
        pass
    service_list = [s.strip() for s in services.split(',') if s.strip()]
    nsx.service.create(name=service_name, description=description, services=service_list)
    click.echo(f"Successfully created service: '{service_name}'")


# ---------------------------------------------------------------------------- #
#                                    delete                                    #
# ---------------------------------------------------------------------------- #


@click.command()
@click.pass_context
@click.option("--name", "service_name", help="Name of the service to delete", required=True)
def delete(ctx, service_name):
    nsx = ctx.obj["nsx"]
    try:
        nsx.service.get(service_name)
        nsx.service.delete(name=service_name)
    except NSXServiceNotFoundError:
        click.echo(f"service doesn't exist: '{service_name}'")
        exit()
    except NSXObjectHasDependenciesError as err:
        click.echo(
            f"service '{service_name}' cannot be deleted because it's used in the following locations:"
        )
        click.echo(format_dependency_list(err))
        exit()
    click.echo(f"Successfully deleted service: '{service_name}'")
