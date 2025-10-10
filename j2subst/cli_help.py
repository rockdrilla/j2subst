import re

## this module
from .dumpfmt import J2substDumpFormat
from .defaults import (
    J2SUBST_DUMP_FORMAT,
    J2SUBST_EMPTY_JSON,
    J2SUBST_EMPTY_YAML,
    J2SUBST_MAX_DEPTH,
)
from .functions import (
    re_sub,
)


J2SUBST_CLI_HELP__DUMP = f'''
By default, dump format is {J2SUBST_DUMP_FORMAT.name}.

Available formats: {', '.join([e.name for e in J2substDumpFormat])}.

Format name is case-insensitive.

Empty config in YAML format is equivalent to:

{re_sub(J2SUBST_EMPTY_YAML.strip(), '^', ' ' * 2, opt = re.MULTILINE)}

Empty config in JSON format is equivalent to:

{re_sub(J2SUBST_EMPTY_JSON.strip(), '^', ' ' * 2, opt = re.MULTILINE)}
'''


J2SUBST_CLI_HELP__TEMPLATE_PATH = '''
Template path is colon-separated list of paths to search for templates.

Path component may contain placeholders:

@{CWD}    - current working directory
@{ORIGIN} - "origin" path

From CLI side, "origin" is always directory where template file is located.
From API side, "origin" maybe specified as any arbitrary directory.

If path component contains placeholder, it is replaced with the corresponding value.

If path component is still containing placeholder prefix ("@{"), it is skipped.

If path component does not contain [unresolved] placeholders, it is treated as directory.

'''


J2SUBST_CLI_HELP__ENV = '''
Corresponding environment variables are also supported.

|------------------------+------------------+---------|
| Environment variable   | Flag option      | Type    |
|------------------------+------------------+---------|
| J2SUBST_VERBOSE        | --verbose        | integer |
| J2SUBST_QUIET          | --quiet          | flag    |
| J2SUBST_DEBUG          | --debug          | flag    |
| J2SUBST_STRICT         | --strict         | flag    |
| J2SUBST_FORCE          | --force          | flag    |
| J2SUBST_UNLINK         | --unlink         | flag    |
| J2SUBST_DEPTH          | --depth          | integer |
| J2SUBST_CONFIG_PATH    | --config-path    | string  |
| J2SUBST_TEMPLATE_PATH  | --template-path  | string  |
| J2SUBST_PYTHON_MODULES | --python-modules | string  |
| J2SUBST_FN_FILTERS     | --fn-filters     | flag    |
| J2SUBST_DICT_NAME_CFG  | --dict-name-cfg  | string  |
| J2SUBST_DICT_NAME_ENV  | --dict-name-env  | string  |
|------------------------+------------------+---------|

See "--help-click" for more details about how Click handles environment variables, especially for flag options.

See "--help-cicd" for more details about how J2subst handles default values while in CI/CD.
'''


J2SUBST_CLI_HELP__CLICK = '''
Variable names are:
- Case-insensitive on Windows but not on other platforms.
- Not stripped of whitespaces and should match the exact name provided to the argument.

For flag options, there is two concepts to consider: the activation of the flag driven by the environment variable, and the value of the flag if it is activated.

The environment variable need to be interpreted, because values read from them are always strings.
We need to transform these strings into boolean values that will determine if the flag is activated or not.

Here are the rules used to parse environment variable values for flag options:
- "true", "1", "yes", "on", "t", "y" are interpreted as activating the flag.
- "false", "0", "no", "off", "f", "n" are interpreted as deactivating the flag.
- The presence of the environment variable without value is interpreted as deactivating the flag.
- Empty strings are interpreted as deactivating the flag.
- Values are case-insensitive, so the "True", "TRUE", "tRuE" strings are all activating the flag.
- Values are stripped of leading and trailing whitespaces before being interpreted, so the " True " string is transformed to "true" and so activates the flag.
- Any other value is interpreted as deactivating the flag.

---

Ref: https://click.palletsprojects.com/en/stable/options/#values-from-environment-variables
'''

J2SUBST_CLI_HELP__CICD = f'''
CI/CD notes:

- option "--depth" / variable "J2SUBST_DEPTH" defaults to "{J2SUBST_MAX_DEPTH}" if running in CI/CD and "1" otherwise.

- if argument list is empty then it set to current working directory.
'''
