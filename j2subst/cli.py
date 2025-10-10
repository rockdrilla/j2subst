#!/usr/bin/env python3

import os

from typing import (
    Any,
)

## click
import click
import click.core

## this module
from .dumpfmt import J2substDumpFormat
from .defaults import (
    J2SUBST_DICT_NAME_CFG,
    J2SUBST_DICT_NAME_ENV,
    J2SUBST_DUMP_FORMAT,
    J2SUBST_MAX_DEPTH,
    J2SUBST_TEMPLATE_PATH_PARTS,
    J2SUBST_TEMPLATE_PATH,
    J2SUBST_VERSION,
)
from .functions import (
    click_bool,
    click_bool_neg,
    is_ci,
    is_str,
    str_split_to_list,
)
from .cli_help import (
    J2SUBST_CLI_HELP__CICD,
    J2SUBST_CLI_HELP__CLICK,
    J2SUBST_CLI_HELP__DUMP,
    J2SUBST_CLI_HELP__ENV,
    J2SUBST_CLI_HELP__TEMPLATE_PATH,
)
from .j2subst import J2subst


## NB: click.option() with "show_envvar=True" does a somewhat horrible formatting
## so we do it manually (see cli_help.py)

J2SUBST_CLI_HELP_CONFIG_PATH = '''
    Colon-separated list of configuration files or directories.
    Supported formats: YAML (".yaml", ".yml"), JSON (".json"), TOML (".toml").
'''

J2SUBST_CLI_HELP_TEMPLATE_PATH = f'''
    Colon-separated list of template directories.

    Default: {J2SUBST_TEMPLATE_PATH}
'''

J2SUBST_CLI_HELP_PYTHON_MODULES = '''
    Space-separated list of Python modules to import.

    To import module with an alias, use format: <alias_name>:<module_name>.
'''


def __dump_callback(_ctx: Any, _param: Any, value: str | bool | None) -> J2substDumpFormat | None:
    if value is None:
        return None

    if value is True:
        return J2SUBST_DUMP_FORMAT
    if value is False:
        return None

    if is_str(value):
        if click_bool(value):
            return J2SUBST_DUMP_FORMAT
        if click_bool_neg(value):
            return None
        value = value.upper()
        if value in [ e.name for e in J2substDumpFormat ]:
            return J2substDumpFormat[value]

    raise click.BadParameter(f"must be one of: {', '.join([e.name for e in J2substDumpFormat])}.")


J2SUBST_CLI_CONTEXT_SETTINGS = {
    'help_option_names': ['-h', '--help'],
}


@click.command(
    no_args_is_help=not is_ci(),
    context_settings=J2SUBST_CLI_CONTEXT_SETTINGS,
)
@click.version_option(version=J2SUBST_VERSION,
    prog_name='j2subst',
    message='%(prog)s %(version)s'
)

## extra help topics
@click.option('--help-cicd',
    'o_help_cicd', is_flag=True,
    help='Show help for J2subst behavior in CI/CD.',
)
@click.option('--help-click',
    'o_help_click', is_flag=True,
    help='Show help for Click behavior.',
)
@click.option('--help-dump',
    'o_help_dump', is_flag=True,
    help='Show help for "--dump" mode.',
)
@click.option('--help-env',
    'o_help_env', is_flag=True,
    help='Show help for environment variables.',
)
@click.option('--help-template-path',
    'o_help_template_path', is_flag=True,
    help='Show help for "--template-path".',
)

@click.option('--dump',
    'o_dump_fmt', is_flag=False, flag_value=True, type=click.UNPROCESSED, callback=__dump_callback,
    help='Dump configuration to stdout and exit.',
    metavar='FORMAT',
)

@click.option('--verbose', '-v',
    'o_verbose', count=True,
    envvar='J2SUBST_VERBOSE',
    help='Increase verbosity.',
)
@click.option('--quiet', '-q',
    'o_quiet', is_flag=True,
    envvar='J2SUBST_QUIET',
    help='Enable quiet mode (overrides any --verbose).',
)

@click.option('--debug', '-D',
    'o_debug', is_flag=True,
    envvar='J2SUBST_DEBUG',
    help='Enable debug mode.',
)
@click.option('--strict', '-s',
    'o_strict', is_flag=True,
    envvar='J2SUBST_STRICT',
    help='Enable strict mode.',
)
@click.option('--force', '-f',
    'o_force', is_flag=True,
    envvar='J2SUBST_FORCE',
    help='Enable force mode.',
)
@click.option('--unlink', '-u',
    'o_unlink', is_flag=True,
    envvar='J2SUBST_UNLINK',
    help='Delete template files after expanding it.',
)
@click.option('--depth', '-d',
    'o_depth', type=click.IntRange(1, J2SUBST_MAX_DEPTH),
    envvar='J2SUBST_DEPTH',
    help='Set recursion depth to look for template files.',
    metavar='INTEGER',
)

@click.option('--config-path', '-c',
    'o_config_path',
    envvar='J2SUBST_CONFIG_PATH',
    help=J2SUBST_CLI_HELP_CONFIG_PATH,
    metavar='LIST',
)
@click.option('--template-path', '-t',
    'o_template_path',
    default=J2SUBST_TEMPLATE_PATH,
    envvar='J2SUBST_TEMPLATE_PATH',
    help=J2SUBST_CLI_HELP_TEMPLATE_PATH,
    metavar='LIST',
)

## extra options
@click.option('--python-modules',
    'o_python_modules',
    envvar='J2SUBST_PYTHON_MODULES',
    help=J2SUBST_CLI_HELP_PYTHON_MODULES,
    metavar='LIST',
)
@click.option('--fn-filters',
    'o_fn_filters', is_flag=True,
    envvar='J2SUBST_FN_FILTERS',
    help='Propagate filters as functions too.',
)
@click.option('--dict-name-cfg',
    'o_dict_name_cfg',
    envvar='J2SUBST_DICT_NAME_CFG',
    help='Assign configuration dictionary name to custom value.',
)
@click.option('--dict-name-env',
    'o_dict_name_env',
    envvar='J2SUBST_DICT_NAME_ENV',
    help='Assign environment dictionary name to custom value.',
)

@click.argument('cli_args',
    nargs=-1,
    metavar='[ARGUMENTS]',
)

@click.pass_context
def cli(ctx: click.Context,

        ## extra help topics
        o_help_cicd: bool,
        o_help_click: bool,
        o_help_dump: bool,
        o_help_env: bool,
        o_help_template_path: bool,

        o_dump_fmt: J2substDumpFormat | None,

        o_verbose: int,
        o_quiet: bool,
        o_debug: bool,
        o_strict: bool,
        o_force: bool,
        o_unlink: bool,
        o_depth: int | None,
        o_config_path: str | None,
        o_template_path: str | None,

        o_python_modules: str | None,
        o_fn_filters: bool,
        o_dict_name_cfg: str | None,
        o_dict_name_env: str | None,

        cli_args: tuple[str],
):

    ## extra help topics
    help_topics = [
        [ o_help_cicd,          J2SUBST_CLI_HELP__CICD, ],
        [ o_help_click,         J2SUBST_CLI_HELP__CLICK, ],
        [ o_help_dump,          J2SUBST_CLI_HELP__DUMP, ],
        [ o_help_env,           J2SUBST_CLI_HELP__ENV, ],
        [ o_help_template_path, J2SUBST_CLI_HELP__TEMPLATE_PATH, ],
    ]
    for h in help_topics:
        if h[0]:
            click.echo(h[1])
            ctx.exit()

    ## verify command-line usage
    if o_dump_fmt is not None:

        def __from_cmdline(key: str):
            return ctx.get_parameter_source(key) == click.core.ParameterSource.COMMANDLINE

        def __dump_usage_error(key: str, flag: str):
            if __from_cmdline(key):
                raise click.UsageError(f'Cannot use --dump with {flag}', ctx)

        __dump_usage_error('o_force',  '--force')
        __dump_usage_error('o_unlink', '--unlink')
        __dump_usage_error('o_depth',  '--depth')

        __dump_usage_error('o_template_path', '--template-path')

        __dump_usage_error('o_python_modules', '--python-modules')
        __dump_usage_error('o_fn_filters',     '--fn-filters')
        __dump_usage_error('o_dict_name_cfg',  '--dict-name-cfg')
        __dump_usage_error('o_dict_name_env',  '--dict-name-env')

        ## TODO: support --dump with output file name
        if len(list(cli_args)) > 0:
            raise click.UsageError("Cannot use --dump with arguments", ctx)

    ## adjust verbosity level:
    ## -1 - quiet
    ##  0 - warnings
    ##  1 - info
    ##  2 and more - not implemented
    if o_quiet:
        o_verbose = -1

    _config_path = None
    if o_config_path is not None:
        _config_path = str_split_to_list(o_config_path, ':')

    if o_dump_fmt is not None:
        j = J2subst(dump_only=True,
            verbosity=o_verbose,
            debug=o_debug,
            strict=o_strict,
            config_path=_config_path,
        )

        ## TODO: support --dump with output file name
        print(j.dump_config(o_dump_fmt), flush=True)
        ctx.exit()

    ## here goes regular processing

    if o_depth is None:
        if is_ci():
            o_depth = J2SUBST_MAX_DEPTH
        else:
            o_depth = 1

    if o_template_path is None:
        _template_path = J2SUBST_TEMPLATE_PATH_PARTS
    else:
        _template_path = str_split_to_list(o_template_path, ':')

    if o_dict_name_cfg is None:
        o_dict_name_cfg = J2SUBST_DICT_NAME_CFG
    if o_dict_name_env is None:
        o_dict_name_env = J2SUBST_DICT_NAME_ENV

    _python_modules: dict[str,str] = {}
    if o_python_modules is not None:
        _modules = str_split_to_list(o_python_modules)
        for m in _modules:
            # if m.index(':') < 0:
            #     _python_modules.update( { m: m, } )
            #     continue
            _m = str_split_to_list(m, ':')
            _len = len(_m)
            if _len == 1:
                _python_modules.update( { _m[0]: _m[0], } )
            elif _len == 2:
                _python_modules.update( { _m[0]: _m[1], } )
            else:
                raise click.UsageError(f'not valid "python_modules": {repr(m)}', ctx)

    args: list[str] = list(cli_args)
    if len(args) == 0:
        if is_ci():
            args = [ os.getcwd() ]
        else:
            raise click.UsageError('no arguments were specified', ctx)

    j = J2subst(
            verbosity=o_verbose,
            debug=o_debug,
            strict=o_strict,
            force=o_force,
            unlink=o_unlink,

            config_path=_config_path,
            template_path=_template_path,

            python_modules=_python_modules,
            filters_as_functions=o_fn_filters,
            dict_name_cfg=o_dict_name_cfg,
            dict_name_env=o_dict_name_env,
    )

    ## deal with 1/2 argument mode
    _in, _out = j.handle_simple_cli_args(*args[:2])

    r = True
    if _in:
        r &= j.render_file(_in, _out)
    else:
        ## disallow stdin/stdout from this moment
        j.allow_stdin_stdout = False

        for arg in args:
            if os.path.isdir(arg):
                r &= j.render_directory(arg, o_depth)
            else:
                r &= j.render_file(arg)

    if not r:
        ctx.exit(1)

    ctx.exit(0)
    return


if __name__ == '__main__':
    # pylint: disable=E1120
    cli(
        prog_name='j2subst',
    )
