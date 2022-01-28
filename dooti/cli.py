import click
import sys
from .dooti import dooti


@click.group()
def cli():
    pass


@cli.command()
@click.argument("ext")
@click.argument("handler", required=False)
def ext(ext: str, handler: str = None):
    tgt = dooti()

    if handler is None:
        click.echo(tgt.get_default_ext(ext))
        return 0

    tgt.set_default_ext(ext, handler)
    return 0


@cli.command()
@click.argument("scheme")
@click.argument("handler", required=False)
def scheme(scheme: str, handler: str = None):
    tgt = dooti()

    if handler is None:
        click.echo(tgt.get_default_scheme(scheme))
        return 0

    tgt.set_default_scheme(scheme, handler)
    return 0


@cli.command()
@click.argument("uti")
@click.argument("handler", required=False)
def uti(uti: str, handler: str = None):
    tgt = dooti()

    if handler is None:
        click.echo(tgt.get_default_uti(uti))
        return 0

    tgt.set_default_uti(uti, handler)
    return 0


if __name__ == "__main__":
    sys.exit(cli())  # pragma: no cover
