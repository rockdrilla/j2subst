# j2subst - Jinja2 Template Substitution Tool

j2subst is a command-line tool for processing Jinja2 templates with configuration data from multiple sources. It's designed for use in CI/CD pipelines and configuration management workflows.

## Features

- **Multiple Configuration Formats**: Supports YAML, JSON, and TOML configuration files
- **Flexible Template Resolution**: Automatic template path resolution with placeholders
- **Environment Variables**: Access to environment variables within templates
- **Python Module Integration**: Import Python modules for advanced template logic
- **Built-in Functions & Filters**: Comprehensive set of built-in Jinja2 filters and functions
- **CI/CD Optimized**: Special behavior for CI/CD environments
- **Dump Mode**: Export configuration data for debugging and inspection

## Installation

### Using Docker

```sh
docker pull docker.io/rockdrilla/j2subst
```

### From PyPI

```sh
pip install j2subst
```

## Quick Start

### Docker Usage

Docker image `docker.io/rockdrilla/j2subst` has several extra things done:
1) entrypoint is set to `j2subst` script;
2) current working directory is set to "`/w`" and it's volume.
3) environment variable `J2SUBST_PYTHON_MODULES` is set to `"netaddr psutil"` - these packages are installed via `pip` and they are not dependencies in any kind, but provided for better usability; see file `docker/requirements-extra.txt`.

To simplify usage, the one may define shell alias:
```sh
alias j2subst='docker run --rm -v "${PWD}:/w" docker.io/rockdrilla/j2subst '
```

### Basic Usage

Process a single template file:

```sh
j2subst template.j2
```

This will process `template.j2` and output to `template` (removing the `.j2` extension).

### Input/Output Specification

Process template with explicit input and output:

```sh
j2subst input.j2 output.txt
```

Use stdin/stdout:

```sh
cat template.j2 | j2subst - > output.txt
j2subst input.j2 -
```

### Directory Processing

Process all templates in a directory (no recursion):

```sh
j2subst /path/to/templates/
```

Control recursion depth:

```sh
j2subst --depth 3 /path/to/templates/
```

## Configuration

### Configuration Files

j2subst can load configuration from multiple sources:

```sh
j2subst -c config.yml template.j2
j2subst -c /path/to/configs/ template.j2
```

Supported formats:
- YAML (`.yaml`, `.yml`)
- JSON (`.json`)
- TOML (`.toml`)

### Template Paths

Specify template search paths:

```sh
j2subst -t /custom/templates:/other/templates template.j2
```

Default template path is `"@{ORIGIN}:@{CWD}"`.

Template path placeholders:
- `@{CWD}` - current working directory
- `@{ORIGIN}` - directory containing the currently processed template file. This placeholder dynamically updates when processing multiple templates, always pointing to the directory of the template currently being rendered.

*Nota bene*: `@{ORIGIN}` is unavailable when processing template from stdin.

## Template Context

Templates have access to two main dictionaries:

- `{{ cfg }}` - Configuration data from files (default name)
- `{{ env }}` - Environment variables (default name)

### Example Template

```jinja2
# config.j2
server_name: {{ cfg.server.name }}
database_url: {{ cfg.database.url }}
environment: {{ env.ENVIRONMENT }}
```

With configuration file `config.yml`:
```yaml
server:
  name: myserver
database:
  url: postgresql://localhost/mydb
```

## Command Line Options

### Core Options

- `--dump [FORMAT]` - Dump configuration to stdout (YAML/JSON) and exit
- `--verbose, -v` - Increase verbosity (can be used multiple times)
- `--quiet, -q` - Enable quiet mode (overrides "`--verbose`")
- `--debug, -D` - Enable debug mode (prints debug messages to stderr; overrides "`--quiet`")
- `--strict, -s` - Enable strict mode (warnings become errors)
- `--force, -f` - Enable force mode (overwrite existing files)
- `--unlink, -u` - Delete template files after processing

### Configuration Options

- `--config-path, -c PATH` - Colon-separated list of config files/directories
- `--template-path, -t PATH` - Colon-separated list of template directories
- `--depth, -d INTEGER` - Set recursion depth for directory processing (1-20)

### Advanced Options

- `--python-modules LIST` - Space-separated list of Python modules to import
- `--fn-filters` - Propagate filters as functions too
- `--dict-name-cfg NAME` - Custom name for configuration dictionary
- `--dict-name-env NAME` - Custom name for environment dictionary

### Help Options

- `--help-cicd` - Show help for CI/CD behavior
- `--help-click` - Show help for Click behavior
- `--help-dump` - Show help for dump mode
- `--help-env` - Show help for environment variables
- `--help-template-path` - Show help for template paths

## Environment Variables

Corresponding environment variables are also supported:
```
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
```

See [Click documentation](https://click.palletsprojects.com/en/stable/options/#values-from-environment-variables) for more details about how Click handles environment variables, especially for flag options.

### CI/CD behavior

- option `--depth` / variable `J2SUBST_DEPTH` defaults to `20` if running in CI/CD and `1` otherwise.
- if argument list is empty then it set to current working directory.

## Built-in Python Modules

The following Python modules are available by default in templates:

- `datetime`
- `hashlib`
- `os_path` (alias for `os.path`)
- `pathlib`
- `re`
- `secrets`
- `string`

## Built-in Functions

Available built-in functions:

- `bool`, `filter`, `isinstance`, `len`, `list`, `repr`, `set`, `sorted`, `str`, `type`

## Examples

### Dump Configuration

```sh
j2subst --dump
j2subst --dump json
j2subst -c config.yml --dump
```

### Import Custom Python Modules

```sh
j2subst --python-modules "myjson:json math" template.j2
```

This imports:
- `json` module as `myjson`
- `math` module as `math`

### Custom Dictionary Names

```sh
j2subst --dict-name-cfg config --dict-name-env environment template.j2
```

Now use in templates:
```jinja2
{{ config.server.name }}
{{ environment.HOME }}
```

## Development

### Building Docker Image

```sh
export IMAGE_VERSION=wip
./docker/build-scripts/image-base.sh
./docker/build-scripts/image.sh
```

## License

Apache-2.0

- [spdx.org](https://spdx.org/licenses/Apache-2.0.html)
- [opensource.org](https://opensource.org/licenses/Apache-2.0)
- [apache.org](https://www.apache.org/licenses/LICENSE-2.0)
