import hashlib
import io
import os
import os.path
import re
import sys

from collections.abc import (
    Mapping,
    Sequence,
)
from os import (
    PathLike,
)
from typing import (
    Any,
    Callable,
)

## this module
from .defaults import (
    J2SUBST_ENV_CI,
    J2SUBST_ENV_SKIP,
)


def is_str(x: Any) -> bool:
    return isinstance(x, str)


def is_str_or_path(x: Any) -> bool:
    return is_str(x) or isinstance(x, PathLike)


def is_seq(x: Any) -> bool:
    return isinstance(x, Sequence) and not is_str_or_path(x)


def is_map(x: Any) -> bool:
    return isinstance(x, Mapping)


def is_plain_key(x: Any | None) -> bool:
    if not (is_str_or_path(x) and x):
        return False
    return bool(re.fullmatch(r'[a-zA-Z_][a-zA-Z0-9_]*', str(x)))


def uniq(a: Sequence[Any]) -> list[Any]:
    return list(set(a))


def only_str(a: Sequence[Any]) -> list[str]:
    return [str(x) for x in filter(is_str_or_path, a)]


def non_empty_str(a: Sequence[Any]) -> list[str]:
    return only_str(list(filter(None, a)))


def uniq_str_list(a: Sequence[Any]) -> list[Any]:
    return uniq(non_empty_str(a))


def str_split_to_list(s: str, sep: str | re.Pattern[str] = r'\s+') -> list[str]:
    return non_empty_str(re.split(sep, s))


def dict_to_str_list(x: dict[str, Any]) -> list[str]:
    r: list[str] = []
    for k in sorted(x.keys()):
        if x[k] is None:
            r.append(f'{k}')
        else:
            r.append(f'{k}={str(x[k])}')
    return r


def any_to_str_list(x: Any) -> list[str]:
    if x is None:
        return []
    if is_str_or_path(x):
        return [str(x)]
    if is_seq(x):
        return [str(e) for e in x]
    if is_map(x):
        return dict_to_str_list(x)
    return [str(x)]


def is_re_match(x: Any, pat: str | re.Pattern[str], opt: int = 0) -> bool:
    if is_str_or_path(x):
        return bool(re.match(pat, str(x), opt))
    if is_seq(x):
        return any(is_re_match(v, pat, opt) for v in x)
    if is_map(x):
        return any(is_re_match(v, pat, opt) for v in x.keys())
    return False


def is_re_fullmatch(x: Any, pat: str | re.Pattern[str], opt: int = 0) -> bool:
    if is_str_or_path(x):
        return bool(re.fullmatch(pat, str(x), opt))
    if is_seq(x):
        return any(is_re_fullmatch(v, pat, opt) for v in x)
    if is_map(x):
        return any(is_re_fullmatch(v, pat, opt) for v in x.keys())
    return False


def re_match(x: Any, pat: str | re.Pattern[str], opt: int = 0) -> Any:
    if is_str_or_path(x):
        return re.match(pat, str(x), opt)
    if is_seq(x):
        return [v for v in x if re_match(v, pat, opt)]
    if is_map(x):
        return {k: v for k, v in x.items() if re_match(k, pat, opt)}
    return None


def re_fullmatch(x: Any, pat: str | re.Pattern[str], opt: int = 0) -> Any:
    if is_str_or_path(x):
        return re.fullmatch(pat, str(x), opt)
    if is_seq(x):
        return [v for v in x if re_fullmatch(v, pat, opt)]
    if is_map(x):
        return {k: v for k, v in x.items() if re_fullmatch(k, pat, opt)}
    return None


def re_match_neg(x: Any, pat: str | re.Pattern[str], opt: int = 0) -> Any:
    if is_str_or_path(x):
        return not bool(re.match(pat, str(x), opt))
    if is_seq(x):
        return [v for v in x if re_match_neg(v, pat, opt)]
    if is_map(x):
        return {k: v for k, v in x.items() if re_match_neg(k, pat, opt)}
    return x


def re_fullmatch_neg(x: Any, pat: str | re.Pattern[str], opt: int = 0) -> Any:
    if is_str_or_path(x):
        return not bool(re.fullmatch(pat, str(x), opt))
    if is_seq(x):
        return [v for v in x if re_fullmatch_neg(v, pat, opt)]
    if is_map(x):
        return {k: v for k, v in x.items() if re_fullmatch_neg(k, pat, opt)}
    return x


def dict_remap_keys(x: dict[Any, Any], key_map: Callable[[Any], Any] | None) -> dict[Any, Any]:
    if key_map is None:
        print('J2subst: dict_remap_keys(): key_map is None', file=sys.stderr)
        return x
    m: dict[Any, Any] = {}
    for k in x.keys():
        v = key_map(k)
        if v in m:
            ## merely debug output
            print(f'J2subst: dict_remap_keys(): duplicate key {repr(v)} <= {repr(k)}', file=sys.stderr)
            continue
        m[v] = x[k]
    return m


def re_sub(x: Any, pat: str | re.Pattern[str], repl: str | Callable[[re.Match[str]], str], count: int = 0, opt: int = 0) -> Any:
    if is_str_or_path(x):
        return re.sub(pat, repl, str(x), count, opt)
    if is_seq(x):
        return [re_sub(v, pat, repl, count, opt) for v in x]
    if is_map(x):
        return dict_remap_keys(x, lambda k: re_sub(k, pat, repl, count, opt))
    return x


def any_to_env_dict(x: Any) -> dict[str, str | None]:
    if x is None:
        return {}

    h: dict[str, str | None] = {}

    ## TODO: review
    def __feed_dict(key: Any, value: Any = None, parse_key: bool = True):
        if not key:
            return
        if (value is None) and (not parse_key):
            return
        k = str(key)
        if not k:
            return
        v = value
        if parse_key:
            k2, m, v2 = k.partition('=')
            if m == '=':
                k = k2
                v = v2
        if is_env_skipped(k) or (not is_plain_key(k)):
            return
        if k in h:
            return
        if v is not None:
            v = str(v)
        h[k] = v

    if is_str_or_path(x):
        __feed_dict(str(x))
    elif is_seq(x):
        for e in x:
            __feed_dict(e)
    elif is_map(x):
        for k in x:
            __feed_dict(k, x[k], False)
    else:
        return {}

    return h


def dict_keys(x: dict[Any, Any]) -> list[Any]:
    return sorted(x.keys())


def dict_empty_keys(x: dict[Any, Any]) -> list[Any]:
    return sorted([k for k in x.keys() if x[k] is None])


def dict_non_empty_keys(x: dict[Any, Any]) -> list[Any]:
    return sorted([k for k in x.keys() if x[k] is not None])


def list_diff(a: Sequence[Any], b: Sequence[Any]) -> list[Any]:
    return list(set(a) - set(b))


def list_intersect(a: Sequence[Any], b: Sequence[Any]) -> list[Any]:
    return list(set(a) & set(b))


## ref: https://click.palletsprojects.com/en/stable/options/#values-from-environment-variables
def click_bool(x: Any) -> bool:
    if is_str(x):
        return str(x).strip().lower() in { "1", "on", "t", "true", "y", "yes" }
    if isinstance(x, bool):
        return x
    return False

## ref: https://click.palletsprojects.com/en/stable/options/#values-from-environment-variables
def click_bool_neg(x: Any) -> bool:
    if is_str(x):
        return str(x).strip().lower() in { "0", "f", "false", "n", "no", "off" }
    if isinstance(x, bool):
        return not x
    return False


## ref: https://pkg.go.dev/strconv#ParseBool
## behavior is mostly the same except no errors for invalid values
def go_bool(x: Any) -> bool:
    if is_str(x):
        return str(x) in { "1", "T", "TRUE", "True", "t", "true" }
    if isinstance(x, bool):
        return x
    return False

## ref: https://pkg.go.dev/strconv#ParseBool
## behavior is mostly the same except no errors for invalid values
def go_bool_neg(x: Any) -> bool:
    if is_str(x):
        return str(x) in { "0", "F", "FALSE", "False", "f", "false" }
    if isinstance(x, bool):
        return not x
    return False


## NB: not in J2SUBST_FUNCTIONS
def merge_dict_recurse(d1: dict[Any, Any] | None, d2: dict[Any, Any] | None) -> dict[Any, Any]:
    x: dict[Any, Any] = {}
    if d1:
        x = x | d1
    if not d2:
        return x

    keys1 = set(x.keys())
    keys2 = set(d2.keys())
    common = keys1 & keys2
    missing = keys2 - common

    map1 = {k for k in common if is_map(x.get(k))}
    seq1 = {k for k in common if is_seq(x.get(k))}
    misc1 = common - seq1 - map1

    merge_safe = missing | misc1
    x.update({k: d2.get(k) for k in merge_safe})

    map_common = {k for k in map1 if is_map(d2.get(k))}
    for k in map_common:
        y = d2.get(k)
        if not y:
            x[k] = {}
            continue
        x[k] = merge_dict_recurse(x.get(k), y)

    seq_common = {k for k in seq1 if is_seq(d2.get(k))}
    for k in seq_common:
        y = d2.get(k)
        if not y:
            x[k] = []
            continue
        ## TYPING-TODO
        x[k] = uniq(list(x.get(k)) + list(y))

    unmerged = (map1 - map_common) | (seq1 - seq_common)
    for k in unmerged:
        t1 = type(x.get(k))
        t2 = type(d2.get(k))
        print(f'J2subst: merge_dict_recurse(): skipping key {k} due to type mismatch: {t1} vs. {t2}', file=sys.stderr)

    return x


def join_prefix(prefix: str, *paths: Any) -> str:
    pfx = prefix or '/'
    pfx = '/' + pfx.strip('/')
    rv = os.path.normpath(os.path.join(pfx, *paths).rstrip('/')).rstrip('/')
    if rv == pfx:
        raise ValueError('J2subst: join_prefix(): empty path after prefix')
    common = os.path.commonpath([pfx, rv])
    if common == pfx:
        return rv
    ## slowpath
    rv = rv.removeprefix(common).lstrip('/')
    rv = os.path.join(pfx, rv)
    return rv


def md5(x: str) -> str:
    return hashlib.md5(x.encode('utf-8')).hexdigest()


def sha1(x: str) -> str:
    return hashlib.sha1(x.encode('utf-8')).hexdigest()


def sha256(x: str) -> str:
    return hashlib.sha256(x.encode('utf-8')).hexdigest()


def sha384(x: str) -> str:
    return hashlib.sha384(x.encode('utf-8')).hexdigest()


def sha512(x: str) -> str:
    return hashlib.sha512(x.encode('utf-8')).hexdigest()


def sha3_256(x: str) -> str:
    return hashlib.sha3_256(x.encode('utf-8')).hexdigest()


def sha3_384(x: str) -> str:
    return hashlib.sha3_384(x.encode('utf-8')).hexdigest()


def sha3_512(x: str) -> str:
    return hashlib.sha3_512(x.encode('utf-8')).hexdigest()


def file_md5(x: str) -> str:
    with open(x, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()


def file_sha1(x: str) -> str:
    with open(x, 'rb') as f:
        return hashlib.sha1(f.read()).hexdigest()


def file_sha256(x: str) -> str:
    with open(x, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()


def file_sha384(x: str) -> str:
    with open(x, 'rb') as f:
        return hashlib.sha384(f.read()).hexdigest()


def file_sha512(x: str) -> str:
    with open(x, 'rb') as f:
        return hashlib.sha512(f.read()).hexdigest()


def file_sha3_256(x: str) -> str:
    with open(x, 'rb') as f:
        return hashlib.sha3_256(f.read()).hexdigest()


def file_sha3_384(x: str) -> str:
    with open(x, 'rb') as f:
        return hashlib.sha3_384(f.read()).hexdigest()


def file_sha3_512(x: str) -> str:
    with open(x, 'rb') as f:
        return hashlib.sha3_512(f.read()).hexdigest()


## NB: not in J2SUBST_FUNCTIONS
def is_env_skipped(x: Any) -> bool:
    if not is_str(x):
        return True
    x = str(x)
    for r in J2SUBST_ENV_SKIP:
        if re.match(r, x):
            return True
    return False


def j2subst_escape(x: Any) -> Any:
    if x is None:
        return None
    if is_str_or_path(x):
        x = str(x)
        if x == '':
            return "''"
        if re.search(r'(?:\s|[;{}()\[\]\\\'"*?])', x):
            return repr(x)
        return x
    if is_seq(x):
        return [ j2subst_escape(v) for v in x ]
    if is_map(x):
        return dict_remap_keys(x, j2subst_escape)
    return j2subst_escape(str(x))


def is_file_io(x: Any) -> bool:
    if not isinstance(x, io.IOBase):
        return False
    if x.closed:
        return False
    ## TODO: avoid try-except
    try:
        n = x.fileno()
        return n >= 0
    except (OSError, io.UnsupportedOperation):
        pass
    return False


def is_file_io_read(x: Any) -> bool:
    if not is_file_io(x):
        return False
    return x.readable()


def is_file_io_write(x: Any) -> bool:
    if not is_file_io(x):
        return False
    return x.writable()


__j2subst_stdin_fd: int | None = None
__j2subst_stdout_fd: int | None = None


def is_stdin(x: Any) -> bool:
    _STDIN = '/dev/stdin'

    if x is None:
        return False

    # pylint: disable=W0603
    global __j2subst_stdin_fd

    if is_file_io_read(x):
        if __j2subst_stdin_fd is None:
            if is_file_io_read(sys.stdin):
                __j2subst_stdin_fd = sys.stdin.fileno()
            else:
                __j2subst_stdin_fd = -1
        if __j2subst_stdin_fd is None:
            return False
        if __j2subst_stdin_fd < 0:
            return False

        return os.path.sameopenfile(x.fileno(), __j2subst_stdin_fd)

    if not (x and is_str_or_path(x)):
        return False
    if str(x) in [ '-', _STDIN ]:
        return True
    return os.path.exists(x) and os.path.samefile(x, _STDIN)


def is_stdout(x: Any) -> bool:
    _STDOUT = '/dev/stdout'

    if x is None:
        return False

    # pylint: disable=W0603
    global __j2subst_stdout_fd

    if is_file_io_write(x):
        if __j2subst_stdout_fd is None:
            if is_file_io_read(sys.stdout):
                __j2subst_stdout_fd = sys.stdout.fileno()
            else:
                __j2subst_stdout_fd = -1
        if __j2subst_stdout_fd is None:
            return False
        if __j2subst_stdout_fd < 0:
            return False

        return os.path.sameopenfile(x.fileno(), __j2subst_stdout_fd)

    if not (x and is_str_or_path(x)):
        return False
    if str(x) in [ '-', _STDOUT ]:
        return True
    return os.path.exists(x) and os.path.samefile(x, _STDOUT)


__j2subst_is_ci: bool | None = None


## NB: not in J2SUBST_FUNCTIONS
def is_ci(_x: Any = None) -> bool:
    # pylint: disable=W0603
    global __j2subst_is_ci

    if __j2subst_is_ci is not None:
        return __j2subst_is_ci

    ## ref: https://github.com/watson/ci-info/blob/3fae1ac492f59c1835a56b2a3c40b8c2cbeb02c1/index.js#L37

    # if os.getenv('CI') == 'false':
    if click_bool_neg(os.getenv('CI')):
        __j2subst_is_ci = False
    else:
        __j2subst_is_ci = False
        for e in list_intersect(J2SUBST_ENV_CI, list(os.environ.keys())):
            if os.environ[e]:
                __j2subst_is_ci = True
                break

    return __j2subst_is_ci


J2SUBST_FILTERS: list[Any] = [
    any_to_env_dict,
    any_to_str_list,
    click_bool,
    click_bool_neg,
    dict_empty_keys,
    dict_keys,
    dict_non_empty_keys,
    dict_remap_keys,
    dict_to_str_list,
    file_md5,
    file_sha1,
    file_sha256,
    file_sha384,
    file_sha512,
    file_sha3_256,
    file_sha3_384,
    file_sha3_512,
    go_bool,
    go_bool_neg,
    is_file_io,
    is_file_io_read,
    is_file_io_write,
    is_map,
    is_plain_key,
    is_re_fullmatch,
    is_re_match,
    is_seq,
    is_stdin,
    is_stdout,
    is_str,
    is_str_or_path,
    j2subst_escape,
    join_prefix,
    list_diff,
    list_intersect,
    md5,
    non_empty_str,
    only_str,
    re_fullmatch,
    re_fullmatch_neg,
    re_match,
    re_match_neg,
    re_sub,
    sha1,
    sha256,
    sha384,
    sha512,
    sha3_256,
    sha3_384,
    sha3_512,
    str_split_to_list,
    uniq,
    uniq_str_list,
]

J2SUBST_FILTER_ALIASES: dict[str, Any] = {
    'j2e': j2subst_escape,
}
