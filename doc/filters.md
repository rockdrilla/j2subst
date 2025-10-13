# J2subst Filters Documentation

This document provides comprehensive documentation for all Jinja2 filters available in the J2subst library.

## Overview

J2subst provides a comprehensive set of Jinja2 filters for string manipulation, type checking, regular expressions, hashing, and more. These filters can be used in Jinja2 templates to transform and process data.

## Available Filters

### Type Checking Filters

#### `is_str(x: Any) -> bool`
Checks if the input is a string.

**Parameters:**
- `x`: Any value to check

**Returns:**
- `bool`: `True` if `x` is a string, `False` otherwise

**Example:**
```jinja2
{{ "hello" | is_str }}  {# Output: true #}
{{ 123 | is_str }}      {# Output: false #}
```

#### `is_str_or_path(x: Any) -> bool`
Checks if the input is a string or `os.PathLike` object.

**Parameters:**
- `x`: Any value to check

**Returns:**
- `bool`: `True` if `x` is a string or `os.PathLike`, `False` otherwise

Reference: [Miscellaneous operating system interfaces](https://docs.python.org/3/library/os.html#os.PathLike)

#### `is_seq(x: Any) -> bool`
Checks if the input is a sequence (but not a string or path).

**Parameters:**
- `x`: Any value to check

**Returns:**
- `bool`: `True` if `x` is a sequence, `False` otherwise

#### `is_map(x: Any) -> bool`
Checks if the input is a mapping (dictionary-like object).

**Parameters:**
- `x`: Any value to check

**Returns:**
- `bool`: `True` if `x` is a mapping, `False` otherwise

#### `is_plain_key(x: Any | None) -> bool`
Checks if the input is a valid plain key (alphanumeric + underscore, starting with letter/underscore).

**Parameters:**
- `x`: Any value to check

**Returns:**
- `bool`: `True` if `x` matches pattern `[a-zA-Z_][a-zA-Z0-9_]*`, `False` otherwise

### String Manipulation Filters

#### `uniq(a: Sequence[Any]) -> list[Any]`
Returns unique elements from a sequence.

**Parameters:**
- `a`: Input sequence

**Returns:**
- `list[Any]`: List of unique elements

**Example:**
```jinja2
{{ [1, 2, 3, 2] | uniq }}  {# Output: [1, 2, 3] #}
```

#### `only_str(a: Sequence[Any]) -> list[str]`
Filters sequence to only string or `os.PathLike` elements and converts them to strings.

**Parameters:**
- `a`: Input sequence

**Returns:**
- `list[str]`: List of string elements

#### `non_empty_str(a: Sequence[Any]) -> list[str]`
Filters sequence to non-empty string or `os.PathLike` elements.

**Parameters:**
- `a`: Input sequence

**Returns:**
- `list[str]`: List of non-empty string elements

#### `uniq_str_list(a: Sequence[Any]) -> list[Any]`
Returns unique non-empty strings from a sequence.

**Parameters:**
- `a`: Input sequence

**Returns:**
- `list[Any]`: List of unique non-empty strings

#### `str_split_to_list(s: str, sep: str | re.Pattern[str] = r'\s+') -> list[str]`
Splits a string by separator and returns non-empty parts.

**Parameters:**
- `s`: Input string
- `sep`: Separator pattern (default: whitespace)

**Returns:**
- `list[str]`: List of non-empty split parts

**Example:**
```jinja2
{{ "a b  c" | str_split_to_list }}  {# Output: ["a", "b", "c"] #}
```

#### `dict_to_str_list(x: dict[str, Any]) -> list[str]`
Converts dictionary to list of strings in format "key=value" or "key" for None values.

**Parameters:**
- `x`: Input dictionary

**Returns:**
- `list[str]`: List of formatted strings

**Example:**
```jinja2
{{ {"a": 1, "b": None} | dict_to_str_list }}  {# Output: ["a=1", "b"] #}
```

#### `any_to_str_list(x: Any) -> list[str]`
Converts any value to a list of strings.

**Parameters:**
- `x`: Input value

**Returns:**
- `list[str]`: List of strings

**Behavior:**
- `None` → `[]`
- String/Path → `[str(x)]`
- Sequence → `[str(e) for e in x]`
- Mapping → `dict_to_str_list(x)`
- Other → `[str(x)]`

### Regular Expression Filters

#### `is_re_match(x: Any, pat: str | re.Pattern[str], opt: int = 0) -> bool`
Checks if input matches regular expression pattern.

**Parameters:**
- `x`: Input value (string, sequence, or mapping)
- `pat`: Regular expression pattern
- `opt`: Regex options

**Returns:**
- `bool`: `True` if pattern matches

#### `is_re_fullmatch(x: Any, pat: str | re.Pattern[str], opt: int = 0) -> bool`
Checks if input fully matches regular expression pattern.

**Parameters:**
- `x`: Input value (string, sequence, or mapping)
- `pat`: Regular expression pattern
- `opt`: Regex options

**Returns:**
- `bool`: `True` if pattern fully matches

#### `re_match(x: Any, pat: str | re.Pattern[str], opt: int = 0) -> Any`
Filters elements that match regular expression pattern.

**Parameters:**
- `x`: Input value (string, sequence, or mapping)
- `pat`: Regular expression pattern
- `opt`: Regex options

**Returns:**
- Filtered result based on input type

#### `re_fullmatch(x: Any, pat: str | re.Pattern[str], opt: int = 0) -> Any`
Filters elements that fully match regular expression pattern.

**Parameters:**
- `x`: Input value (string, sequence, or mapping)
- `pat`: Regular expression pattern
- `opt`: Regex options

**Returns:**
- Filtered result based on input type

#### `re_match_neg(x: Any, pat: str | re.Pattern[str], opt: int = 0) -> Any`
Filters elements that do NOT match regular expression pattern.

**Parameters:**
- `x`: Input value (string, sequence, or mapping)
- `pat`: Regular expression pattern
- `opt`: Regex options

**Returns:**
- Filtered result based on input type

#### `re_fullmatch_neg(x: Any, pat: str | re.Pattern[str], opt: int = 0) -> Any`
Filters elements that do NOT fully match regular expression pattern.

**Parameters:**
- `x`: Input value (string, sequence, or mapping)
- `pat`: Regular expression pattern
- `opt`: Regex options

**Returns:**
- Filtered result based on input type

#### `re_sub(x: Any, pat: str | re.Pattern[str], repl: str | Callable[[re.Match[str]], str], count: int = 0, opt: int = 0) -> Any`
Performs regex substitution on input.

**Parameters:**
- `x`: Input value (string, sequence, or mapping)
- `pat`: Regular expression pattern
- `repl`: Replacement string or function
- `count`: Maximum number of replacements
- `opt`: Regex options

**Returns:**
- Result with substitutions applied

**Example:**
```jinja2
{{ "hello world" | re_sub("world", "there") }}  {# Output: "hello there" #}
```

### Dictionary Filters

#### `dict_remap_keys(x: dict[Any, Any], key_map: Callable[[Any], Any] | None) -> dict[Any, Any]`
Remaps dictionary keys using provided mapping function.

**Parameters:**
- `x`: Input dictionary
- `key_map`: Function to transform keys

**Returns:**
- `dict[Any, Any]`: Dictionary with remapped keys

#### `any_to_env_dict(x: Any) -> dict[str, str | None]`
Converts any value to environment variable dictionary.

**Parameters:**
- `x`: Input value

**Returns:**
- `dict[str, str | None]`: Environment variable dictionary

#### `dict_keys(x: dict[Any, Any]) -> list[Any]`
Returns sorted dictionary keys.

**Parameters:**
- `x`: Input dictionary

**Returns:**
- `list[Any]`: Sorted list of keys

#### `dict_empty_keys(x: dict[Any, Any]) -> list[Any]`
Returns sorted dictionary keys with None values.

**Parameters:**
- `x`: Input dictionary

**Returns:**
- `list[Any]`: Sorted list of keys with None values

#### `dict_non_empty_keys(x: dict[Any, Any]) -> list[Any]`
Returns sorted dictionary keys with non-None values.

**Parameters:**
- `x`: Input dictionary

**Returns:**
- `list[Any]`: Sorted list of keys with non-None values

### List Operations

#### `list_diff(a: Sequence[Any], b: Sequence[Any]) -> list[Any]`
Returns elements in `a` but not in `b`.

**Parameters:**
- `a`: First sequence
- `b`: Second sequence

**Returns:**
- `list[Any]`: Difference of sequences

**Example:**
```jinja2
{{ [1, 2, 3] | list_diff([2, 4]) }}  {# Output: [1, 3] #}
```

#### `list_intersect(a: Sequence[Any], b: Sequence[Any]) -> list[Any]`
Returns elements common to both `a` and `b`.

**Parameters:**
- `a`: First sequence
- `b`: Second sequence

**Returns:**
- `list[Any]`: Intersection of sequences

**Example:**
```jinja2
{{ [1, 2, 3] | list_intersect([2, 3, 4]) }}  {# Output: [2, 3] #}
```

### Boolean Conversion Filters

#### `click_bool(x: Any) -> bool`
Converts value to boolean using Click's truthy values.

**Parameters:**
- `x`: Input value

**Returns:**
- `bool`: `True` for "1", "on", "t", "true", "y", "yes" (case-insensitive)

#### `click_bool_neg(x: Any) -> bool`
Converts value to boolean negation using Click's falsy values.

**Parameters:**
- `x`: Input value

**Returns:**
- `bool`: `True` for "0", "f", "false", "n", "no", "off" (case-insensitive)

#### `go_bool(x: Any) -> bool`
Converts value to boolean using Go's truthy values.

**Parameters:**
- `x`: Input value

**Returns:**
- `bool`: `True` for "1", "T", "TRUE", "True", "t", "true"

#### `go_bool_neg(x: Any) -> bool`
Converts value to boolean negation using Go's falsy values.

**Parameters:**
- `x`: Input value

**Returns:**
- `bool`: `True` for "0", "F", "FALSE", "False", "f", "false"

### Path and File Filters

#### `join_prefix(prefix: str, *paths: Any) -> str`
Joins paths with a prefix, ensuring result stays under prefix.

**Parameters:**
- `prefix`: Base path prefix
- `*paths`: Path components to join

**Returns:**
- `str`: Joined path

**Example:**
```jinja2
{{ "/base" | join_prefix("dir", "file.txt") }}  {# Output: "/base/dir/file.txt" #}
```

#### `is_file_io(x: Any) -> bool`
Checks if input is a valid file I/O object.

**Parameters:**
- `x`: Input value

**Returns:**
- `bool`: `True` if valid file I/O object

#### `is_file_io_read(x: Any) -> bool`
Checks if input is a readable file I/O object.

**Parameters:**
- `x`: Input value

**Returns:**
- `bool`: `True` if readable file I/O object

#### `is_file_io_write(x: Any) -> bool`
Checks if input is a writable file I/O object.

**Parameters:**
- `x`: Input value

**Returns:**
- `bool`: `True` if writable file I/O object

#### `is_stdin(x: Any) -> bool`
Checks if input represents stdin.

**Parameters:**
- `x`: Input value

**Returns:**
- `bool`: `True` if input is stdin

#### `is_stdout(x: Any) -> bool`
Checks if input represents stdout.

**Parameters:**
- `x`: Input value

**Returns:**
- `bool`: `True` if input is stdout

### Hash Functions

#### String Hash Functions

- `md5(x: str) -> str`: MD5 hash of string
- `sha1(x: str) -> str`: SHA1 hash of string
- `sha256(x: str) -> str`: SHA256 hash of string
- `sha384(x: str) -> str`: SHA384 hash of string
- `sha512(x: str) -> str`: SHA512 hash of string
- `sha3_256(x: str) -> str`: SHA3-256 hash of string
- `sha3_384(x: str) -> str`: SHA3-384 hash of string
- `sha3_512(x: str) -> str`: SHA3-512 hash of string

#### File Hash Functions

- `file_md5(x: str) -> str`: MD5 hash of file content
- `file_sha1(x: str) -> str`: SHA1 hash of file content
- `file_sha256(x: str) -> str`: SHA256 hash of file content
- `file_sha384(x: str) -> str`: SHA384 hash of file content
- `file_sha512(x: str) -> str`: SHA512 hash of file content
- `file_sha3_256(x: str) -> str`: SHA3-256 hash of file content
- `file_sha3_384(x: str) -> str`: SHA3-384 hash of file content
- `file_sha3_512(x: str) -> str`: SHA3-512 hash of file content

### Special Filters

#### `j2subst_escape(x: Any) -> Any`
Escapes values for shell-safe output in J2subst templates.

**Parameters:**
- `x`: Input value

**Returns:**
- Escaped value

**Behavior:**
- Empty string → `"''"`
- Strings with special characters → `repr(x)`
- Sequences/Mappings → Recursively escaped

## Filter Aliases

The following aliases are available for convenience:

- `j2e`: Alias for `j2subst_escape`

## Usage Examples

```jinja2
{# Type checking #}
{% if variable | is_str %}
  String detected
{% endif %}

{# String manipulation #}
{{ "a,b,c" | str_split_to_list(",") }}

{# Regular expressions #}
{{ files | re_match(".*\.txt$") }}

{# Dictionary operations #}
{{ config | dict_keys }}

{# Boolean conversion #}
{{ env_var | click_bool }}

{# Hashing #}
{{ "password" | sha256 }}
```

## Notes

- Most filters handle multiple input types (strings, sequences, mappings) appropriately
- Regular expression filters work recursively on sequences and mappings
- Hash functions expect string input for string hashes and file paths for file hashes
- The `j2subst_escape` filter is particularly useful for generating shell-safe output