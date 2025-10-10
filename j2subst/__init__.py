## this module
from .dumpfmt import J2substDumpFormat
from .j2subst import J2subst


if __name__ == '__main__':
    from .cli import cli

    # pylint: disable=E1120
    cli()
