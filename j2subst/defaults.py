from typing import (
    Any,
)

## this module
from .dumpfmt import J2substDumpFormat


J2SUBST_VERSION = '0.0.3'

J2SUBST_DICT_NAME_CFG = 'cfg'
J2SUBST_DICT_NAME_ENV = 'env'

J2SUBST_TEMPLATE_EXT = '.j2'

J2SUBST_TEMPLATE_PATH_PARTS = [ '@{ORIGIN}', '@{CWD}' ]
J2SUBST_TEMPLATE_PATH = ':'.join(J2SUBST_TEMPLATE_PATH_PARTS)

## merely ephemeral
J2SUBST_MAX_DEPTH = 20

## NB: leading dots are mandatory!
J2SUBST_CONFIG_EXT = [
    '.yaml', '.yml',
    '.json',
    '.toml',
]

J2SUBST_JINJA_EXTENSIONS = [
    'jinja2.ext.do',
    'jinja2.ext.loopcontrols',
]

J2SUBST_JINJA_DEBUG_EXTENSIONS = [
    'jinja2.ext.debug',
]

J2SUBST_PYTHON_MODULES = [
    'datetime',
    'hashlib',
    'pathlib',
    're',
    'secrets',
    'string',
]

J2SUBST_PYTHON_MODULE_ALIASES = {
    'os_path': 'os.path',
}

J2SUBST_BUILTIN_FUNCTIONS: list[Any] = [
    bool,
    # dict, ## already present
    filter,
    isinstance,
    len,
    list,
    repr,
    set,
    sorted,
    str,
    type,
]

J2SUBST_BUILTIN_FUNCTION_ALIASES: dict[str, Any] = {
}

J2SUBST_ENV_SKIP = [
    r'J2SUBST_',
    r'_$',
]

J2SUBST_ENV_CI = [
    'BUILD_ID',
    'BUILD_NUMBER',
    'CI',
    'CI_APP_ID',
    'CI_BUILD_ID',
    'CI_BUILD_NUMBER',
    'CI_NAME',
    'CONTINUOUS_INTEGRATION',
    'RUN_ID',
]

J2SUBST_DUMP_FORMAT = J2substDumpFormat.YAML

J2SUBST_EMPTY_YAML = '\n---\n# empty\n---\n'
J2SUBST_EMPTY_JSON = '{}'
