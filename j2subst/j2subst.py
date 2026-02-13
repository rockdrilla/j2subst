import io
import os
import os.path
import sys
import importlib
import importlib.util
import json
import tomllib

from collections.abc import (
    Mapping,
    Sequence,
)
from os import (
    PathLike,
)
from typing import (
    Any,
)

## jinja2
import jinja2
## natsort
import natsort
## pyyaml
import yaml

## this module
from .dumpfmt import J2substDumpFormat
from .defaults import (
    J2SUBST_BUILTIN_FUNCTION_ALIASES,
    J2SUBST_BUILTIN_FUNCTIONS,
    J2SUBST_CONFIG_EXT,
    J2SUBST_CONFIG_EXT_JSON,
    J2SUBST_CONFIG_EXT_TOML,
    J2SUBST_CONFIG_EXT_YAML,
    J2SUBST_DUMP_FORMAT,
    J2SUBST_EMPTY_JSON,
    J2SUBST_EMPTY_YAML,
    J2SUBST_JINJA_DEBUG_EXTENSIONS,
    J2SUBST_JINJA_EXTENSIONS,
    J2SUBST_MIXIN_EXT,
    J2SUBST_PYTHON_MODULE_ALIASES,
    J2SUBST_PYTHON_MODULES,
    J2SUBST_TEMPLATE_EXT,
    J2SUBST_TEMPLATE_PATH_PARTS,
)
from .functions import (
    J2SUBST_FUNCTIONS,
    J2SUBST_FUNCTION_ALIASES,
    is_ci,
    is_env_skipped,
    is_map,
    is_plain_key,
    is_seq,
    is_stdin,
    is_stdout,
    merge_dict_recurse,
    non_empty_str,
    sha3_256,
)
from .filekind import J2substFileKind


class J2subst:

    def __init__(self,
                 dump_only: bool = False,

                 verbosity: int = 0,
                 debug: bool = False,
                 strict: bool = False,
                 force: bool = False,
                 unlink: bool = False,

                 config_path: Sequence[str | PathLike[str]] | None = None,
                 template_path: Sequence[str | PathLike[str]] | None = None,

                 python_modules: Sequence[str] | Mapping[str, str] | None = None,
                 enable_mixins: bool = False,
    ):

        self.dump_only = bool(dump_only)

        self.debug = bool(debug)
        self.verbosity = int(verbosity)

        self.force = bool(force)
        self.strict = bool(strict)
        self.unlink = False

        self.dict_cfg: dict[str, Any] = {}

        self.config_path: list[str] = []
        if config_path:
            self.config_path = non_empty_str(config_path)

        self.__merge_dict_default()

        if self.dump_only:
            return

        self.allow_stdin_stdout = True
        self.unlink = bool(unlink)

        template_path = template_path or J2SUBST_TEMPLATE_PATH_PARTS
        self.template_path: list[str] = non_empty_str(template_path)

        self.dict_env: dict[str, str] = {}
        self.j2fs_loaders: dict[str, jinja2.FileSystemLoader] = {}

        self.resolve_template_path(resolve_placeholders=False)

        ## make shallow copy of os.environ (for good)
        # self.dict_env = os.environ
        self.dict_env = { k: v for k, v in os.environ.items() if not is_env_skipped(k) }

        j2ext = list(J2SUBST_JINJA_EXTENSIONS)
        if self.debug:
            j2ext += J2SUBST_JINJA_DEBUG_EXTENSIONS

        self.j2env = jinja2.Environment(
            extensions=j2ext,
            ## dumb loader: does nothing by default
            loader=jinja2.DictLoader( { } ),
        )

        for m in J2SUBST_PYTHON_MODULES:
            self.import_python_module(m)
        for alias, m in J2SUBST_PYTHON_MODULE_ALIASES.items():
            self.import_python_module(m, alias)

        def __not_valid_python_module(m: Any):
            raise ValueError(f'not valid "python_modules": {repr(m)}')

        if python_modules is None:
            pass
        elif is_seq(python_modules):
            for m in python_modules:
                if not isinstance(m, str):
                    __not_valid_python_module(m)
                self.import_python_module(m)
        elif is_map(python_modules):
            for alias, m in python_modules.items():
                if not (isinstance(alias, str) and isinstance(m, str)):
                    __not_valid_python_module( {alias: m} )
                self.import_python_module(m, alias)
        else:
            __not_valid_python_module(python_modules)

        for f in J2SUBST_BUILTIN_FUNCTIONS:
            self.import_builtin_function(f)
        for alias, f in J2SUBST_BUILTIN_FUNCTION_ALIASES.items():
            self.import_builtin_function(f, alias)

        for f in J2SUBST_FUNCTIONS:
            self.import_filter(f)
        for alias, f in J2SUBST_FUNCTION_ALIASES.items():
            self.import_filter(f, alias)

        for f in J2SUBST_FUNCTIONS:
            self.import_function(f)
        for alias, f in J2SUBST_FUNCTION_ALIASES.items():
            self.import_function(f, alias)

        self.mixins: dict[str, Any] = {}
        if enable_mixins:
            self.__load_mixin_default()

    def __verify_dump_only(self):
        if not self.dump_only:
            return
        raise ValueError('"dump_only" is True')

    def __msg(self, source: str, message: str):
        print(f'J2subst: {source}: {message}', file=sys.stderr)

    def __show_warn(self) -> bool:
        return self.strict or self.debug or (self.verbosity >= 0)

    def __show_info(self) -> bool:
        return self.debug or (self.verbosity > 0)

    def __warn(self, source: str, message: str):
        if not self.__show_warn():
            return
        if self.strict:
            raise ValueError(message)
        self.__msg(source, message)

    def __info(self, source: str, message: str):
        if not self.__show_info():
            return
        self.__msg(source, message)

    def __debug(self, source: str, message: str):
        if not self.debug:
            return
        self.__msg(source, message)

    @staticmethod
    def __path_id(file_path: str | PathLike[str]) -> tuple[str | None, str | None]:
        f = os.path.abspath(file_path)
        if not os.path.isfile(f):
            return (None, None)
        return (str(f), sha3_256(f)[:16])

    @staticmethod
    def __filename_classify(name: str) -> J2substFileKind:
        ext = os.path.splitext(name)[1]
        if not ext:
            return J2substFileKind.IGNORED
        if ext in J2SUBST_CONFIG_EXT:
            return J2substFileKind.CONFIG
        if ext in J2SUBST_MIXIN_EXT:
            return J2substFileKind.MIXIN
        return J2substFileKind.IGNORED

    def __traverse_config_dir(self, file_kind: J2substFileKind) -> list[str]:

        def _warn(msg: str):
            self.__warn('traverse_config_dir', msg)

        ent: list[str] = []
        for p in self.config_path:
            if os.path.isfile(p):
                if J2subst.__filename_classify(p) == file_kind:
                    ent.append(p)
            elif os.path.isdir(p):
                _ent: list[str] = []
                for e in os.listdir(p):
                    if e.startswith('.'):
                        ## silently ignore hidden files
                        continue
                    if J2subst.__filename_classify(e) != file_kind:
                        continue
                    f = os.path.join(p, e)
                    if not os.path.isfile(f):
                        ## ignore directories and other types
                        continue
                    _ent.append(f)

                ent.extend(natsort.natsorted(_ent))
            else:
                _warn(f'not a file or directory, or does not exist: {p}')

        return ent

    def __merge_dict_default(self):
        for f in self.__traverse_config_dir(J2substFileKind.CONFIG):
            self.merge_dict_from_file(f)

    def __load_mixin_default(self):
        for f in self.__traverse_config_dir(J2substFileKind.MIXIN):
            self.import_mixin(f)

    def __ensure_fs_loader_for(self, path: str | PathLike[str]) -> bool:
        if not os.path.isdir(path):
            return False

        p = str(path)
        if p in self.j2fs_loaders:
            return True

        loader = jinja2.FileSystemLoader(
            path, encoding='utf-8', followlinks=True,
        )
        self.j2fs_loaders.update( { p: loader } )

        return True

    def ensure_fs_loader_for(self, path: str | PathLike[str]) -> bool:
        self.__verify_dump_only()

        def _warn(msg: str):
            self.__warn('ensure_fs_loader_for', msg)

        d = os.path.abspath(path)
        if os.path.isdir(d):
            pass
        elif os.path.isfile(d):
            d = os.path.dirname(d)
        else:
            _warn(f'not a file or directory, or does not exist: {repr(path)}')
            return False

        return self.__ensure_fs_loader_for(d)

    def __resolve_origin(self, origin: str | PathLike[str] | None = None) -> tuple[str | None, bool]:

        def _warn(msg: str):
            self.__warn('__resolve_origin', msg)

        if origin is None:
            return (None, False)

        if not os.path.exists(origin):
            _warn(f'does not exist: {repr(origin)}')
            return (None, False)

        _origin = os.path.normpath(origin)
        if os.path.isdir(_origin):
            _origin = str(_origin)
        elif os.path.isfile(_origin):
            _origin = str(os.path.dirname(_origin))
            if _origin == '':
                _origin = '.'
        else:
            _warn(f'not a file or directory: {repr(origin)}')
            return (None, False)

        _want_root = _origin.startswith('/')
        _origin = str(os.path.abspath(_origin))

        return (_origin, _want_root)

    def resolve_template_path(self, resolve_placeholders: bool, origin: str | PathLike[str] | None = None) -> list[str]:
        self.__verify_dump_only()

        def _warn(msg: str):
            self.__warn('resolve_template_path', msg)

        def _info(msg: str):
            self.__info('resolve_template_path', msg)

        def _debug(msg: str):
            self.__debug('resolve_template_path', msg)

        _origin, _want_root = self.__resolve_origin(origin)

        # dirs: list[str | PathLike[str]] = []
        dirs: list[str] = []

        for p in self.template_path:
            ## see J2SUBST_TEMPLATE_PATH_PARTS
            s = str(p)
            if s.find('@{') >= 0:
                if not resolve_placeholders:
                    _debug(f'not going to resolve template path: {repr(s)}')
                    continue

                s = s.replace('@{CWD}', os.getcwd())
                if _origin is not None:
                    s = s.replace('@{ORIGIN}', _origin)

                ## skip if there're still some special placeholders
                if s.find('@{') >= 0:
                    _warn(f'failed to resolve template path: {repr(s)}')
                    continue

            s = str(os.path.abspath(os.path.normpath(s)))
            if s in dirs:
                _info(f'duplicate template path: {repr(s)}')
                continue

            dirs.append(s)

        if _want_root:
            if '/' in dirs:
                _info('duplicate template path: "/"')
            else:
                dirs.append('/')

        dirs_final: list[str] = []
        for d in dirs:
            if self.__ensure_fs_loader_for(d):
                dirs_final.append(d)
                continue
            _warn(f'failed to load template directory: {repr(d)}')

        # return [str(d) for d in dirs_final]
        return dirs_final

    def remove_global(self, name: str):
        self.__verify_dump_only()

        self.j2env.globals.pop(name, None)

    def remove_filter(self, name: str):
        self.__verify_dump_only()

        self.j2env.filters.pop(name, None)

    def __import_python_module(self, module_name: str, alias: str):
        self.j2env.globals.update( { alias: importlib.import_module(module_name) } )

    def import_python_module(self, module_name: str, alias: str | None = None):
        self.__verify_dump_only()

        def _warn(msg: str):
            self.__warn('import_python_module', msg)

        n = alias or module_name
        if not is_plain_key(n):
            _warn(f'key is not "plain", module {repr(module_name)} will not be imported as {repr(n)}')
            return
        if n in self.j2env.globals:
            _warn(f'globals already has {repr(n)} key, replacing with module {repr(module_name)}')
        self.__import_python_module(module_name, n)

    def __import_filter(self, func: Any, alias: str):
        self.j2env.filters.update( { alias: func } )

    def import_filter(self, func: Any, alias: str | None = None):
        self.__verify_dump_only()

        if not callable(func):
            raise ValueError('func is not callable')

        def _warn(msg: str):
            self.__warn('import_filter', msg)

        n = alias or func.__name__
        if not is_plain_key(n):
            _warn(f'key is not "plain", filter {repr(func.__name__)} will not be imported as {repr(n)}')
            return
        if n in self.j2env.filters:
            _warn(f'filters already has {repr(n)} key, replacing with filter {repr(func.__name__)}')
        self.__import_filter(func, n)

    def __import_function(self, func: Any, alias: str):
        self.j2env.globals.update( { alias: func } )

    def import_builtin_function(self, func: Any, alias: str | None = None):
        self.__verify_dump_only()

        if not callable(func):
            raise ValueError('func is not callable')

        def _warn(msg: str):
            self.__warn('import_builtin_function', msg)

        n = alias or func.__name__
        if not is_plain_key(n):
            _warn(f'key is not "plain", builtin function {repr(func.__name__)} will not be imported as {repr(n)}')
            return
        if n in self.j2env.globals:
            _warn(f'globals already has {repr(n)} key, replacing with builtin function {repr(func.__name__)}')
        self.__import_function(func, n)

    def import_function(self, func: Any, alias: str | None = None):
        self.__verify_dump_only()

        if not callable(func):
            raise ValueError('func is not callable')

        def _warn(msg: str):
            self.__warn('import_function', msg)

        n = alias or func.__name__
        if not is_plain_key(n):
            _warn(f'key is not "plain", function {repr(func.__name__)} will not be imported as {repr(n)}')
            return
        if n in self.j2env.globals:
            _warn(f'globals already has {repr(n)} key, replacing with function {repr(func.__name__)}')
        self.__import_function(func, n)

    def __import_mixin(self, file_path: str, path_id: str):
        module_name = f'j2subst_mixin_{path_id}'

        def _warn(msg: str):
            self.__warn('import_mixin', msg)

        _dont_write_bytecode = sys.dont_write_bytecode
        sys.dont_write_bytecode = True

        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if (spec is None) or (spec.loader is None):
            _warn(f'Unable to construct module spec from {file_path}')
            sys.dont_write_bytecode = _dont_write_bytecode
            return

        module = importlib.util.module_from_spec(spec)

        from .decorators import (
            instance_getter,
            set_instance_getter,
        )
        _getter = instance_getter

        def bound_get_instance() -> J2subst | None:
            return self

        set_instance_getter(bound_get_instance)

        try:
            spec.loader.exec_module(module)
        except Exception as e:
            raise ImportError(f'Error loading mixin from {file_path}: {e}') from e

        set_instance_getter(_getter)
        sys.dont_write_bytecode = _dont_write_bytecode

        self.mixins.update( { path_id: module } )

    def import_mixin(self, file: str | PathLike[str]):
        self.__verify_dump_only()

        def _warn(msg: str):
            self.__warn('import_mixin', msg)

        (file_path, path_id) = J2subst.__path_id(file)
        if (file_path is None) or (path_id is None):
            return

        if path_id in self.mixins:
            _warn(f'mixin from {repr(file)} is already loaded')
            return

        self.__import_mixin(file_path, path_id)

    def merge_dict_from_yaml(self, filename: str | PathLike[str]):
        yaml_all_empty = True
        with open(filename, mode='r', encoding='utf-8') as fx:
            for x in yaml.safe_load_all(fx):
                if not x:
                    continue
                yaml_all_empty = False
                self.dict_cfg = merge_dict_recurse(self.dict_cfg, x)

        if yaml_all_empty:
            self.__info('merge_dict_from_yaml', f'received empty document(s) from: {repr(filename)}')

    def merge_dict_from_toml(self, filename: str | PathLike[str]):
        with open(filename, mode='rb') as fx:
            x = tomllib.load(fx)
            self.dict_cfg = merge_dict_recurse(self.dict_cfg, x)

    def merge_dict_from_json(self, filename: str | PathLike[str]):
        with open(filename, mode='r', encoding='utf-8') as fx:
            x = json.load(fx)
            self.dict_cfg = merge_dict_recurse(self.dict_cfg, x)

    def merge_dict_from_json_str(self, string: str):
        x = json.loads(string)
        self.dict_cfg = merge_dict_recurse(self.dict_cfg, x)

    def merge_dict_from_file(self, filename: str | PathLike[str]) -> bool:
        if not filename:
            return False

        def _warn(msg: str):
            self.__warn('merge_dict_from_file', msg)

        def _info(msg: str):
            self.__info('merge_dict_from_file', msg)

        if not os.path.isfile(filename):
            _warn(f'not a file or does not exist: {repr(filename)}')
            return False

        ext = os.path.splitext(filename)[1]
        if ext not in J2SUBST_CONFIG_EXT:
            _warn(f'non-recognized name extension: {repr(filename)}')
            return False

        if self.__show_info():
            real_f = str(os.path.realpath(filename))
            if real_f == str(filename):
                _info(f'try loading {filename}')
            else:
                _info(f'try loading {filename} <- {real_f}')

        if ext in J2SUBST_CONFIG_EXT_YAML:
            self.merge_dict_from_yaml(filename)
        elif ext in J2SUBST_CONFIG_EXT_TOML:
            self.merge_dict_from_toml(filename)
        elif ext in J2SUBST_CONFIG_EXT_JSON:
            self.merge_dict_from_json(filename)
        else:
            ## likely unreachable
            return False

        return True

    def dump_config_yaml(self) -> str:
        if not self.dict_cfg:
            return J2SUBST_EMPTY_YAML
        return yaml.safe_dump(self.dict_cfg, sort_keys=True)

    def dump_config_json(self) -> str:
        if not self.dict_cfg:
            return J2SUBST_EMPTY_JSON
        return json.dumps(self.dict_cfg, sort_keys=True)

    def dump_config(self, fmt: J2substDumpFormat = J2SUBST_DUMP_FORMAT) -> str:
        if fmt == J2substDumpFormat.YAML:
            return self.dump_config_yaml()
        if fmt == J2substDumpFormat.JSON:
            return self.dump_config_json()
        raise ValueError(f'unknown dump format: {repr(fmt)}')

    def env_overlay(self, j2subst_origin: str | PathLike[str] | None = None, **kwargs: dict[str, Any]) -> jinja2.Environment:
        self.__verify_dump_only()

        kw: dict[str, Any] = {}
        if kwargs:
            kw = kw | kwargs

        _x = kw.get('loader')
        if (_x is not None) and isinstance(_x, jinja2.BaseLoader):
            pass
        else:
            dirs: list[str] = self.resolve_template_path(resolve_placeholders=True, origin=j2subst_origin)

            loader: jinja2.BaseLoader
            if dirs:
                loader = jinja2.ChoiceLoader(
                    [ self.j2fs_loaders[d] for d in dirs ]
                )
            else:
                loader=jinja2.DictLoader( { } )

            kw.update( { 'loader': loader } )

        return self.j2env.overlay(**kw)

    def __prepare_kwargs(self, j2subst_file: str | None, j2subst_origin: str | None) -> dict[str, Any]:
        kw: dict[str, Any] = {
            ## hardcoded:
            'env': self.dict_env,
        }
        kw.update(self.dict_cfg)
        kw.update( {
            ## hardcoded:
            'is_ci': is_ci(),
            'j2subst_file': j2subst_file,
            'j2subst_origin': j2subst_origin,
        } )

        return kw

    def render_str(self, string: str, j2env_overlay: jinja2.Environment | None = None) -> tuple[str, str | None]:
        self.__verify_dump_only()

        _env = j2env_overlay
        if _env is None:
            _env = self.env_overlay()
        t = _env.from_string(string)

        kw = self.__prepare_kwargs(None, None)

        return t.render(**kw), None

    def render_text_io(self, io_source: io.TextIOBase, j2env_overlay: jinja2.Environment | None = None) -> tuple[str, str | None]:
        return self.render_str(''.join(io_source.readlines()), j2env_overlay)

    def render_from_file(self, filename: str, j2env_overlay: jinja2.Environment | None = None) -> tuple[str, str | None]:
        self.__verify_dump_only()

        def _debug(msg: str):
            self.__debug('render_from_file', msg)

        _env = j2env_overlay
        if _env is None:
            ## preserve internal settings
            (_v, _d, _s) = (self.verbosity, self.debug, self.strict)
            ## override internal settings for this call
            (self.verbosity, self.debug, self.strict) = (-1, False, False)
            _env = self.env_overlay()
            ## restore internal settings
            (self.verbosity, self.debug, self.strict) = (_v, _d, _s)

            _debug('trying to resolve with self.env_overlay()')

            ## TODO: avoid try-except
            try:
                _env.get_template(filename)
            except jinja2.TemplateNotFound:
                _debug(f'jinja2.TemplateNotFound: {repr(filename)}')
                _debug(f'trying to resolve with self.env_overlay({repr(filename)})')

                _env = self.env_overlay(filename)

        t = _env.get_template(filename)
        _origin, _ = self.__resolve_origin(t.filename)

        kw = self.__prepare_kwargs(t.filename, _origin)

        return t.render(**kw), t.filename

    def render_stdin(self, j2env_overlay: jinja2.Environment | None = None) -> str:
        self.__verify_dump_only()

        r, _ = self.render_text_io(sys.stdin, j2env_overlay)
        return r

    def render_file(self, file_in: str | PathLike[str], file_out: str | PathLike[str] | None = None, j2env_overlay: jinja2.Environment | None = None) -> bool:
        self.__verify_dump_only()

        rendered: str
        f_in: str | None = None
        f_stdin: bool = False
        f_out: str | None = None

        def _warn(msg: str):
            self.__warn('render_file', msg)

        def _render_error(msg: str) -> bool:
            _warn(msg)
            return False

        def _info(msg: str):
            self.__info('render_file', msg)

        def _debug(msg: str):
            self.__debug('render_file', msg)

        if is_stdin(file_in):
            if not self.allow_stdin_stdout:
                return _render_error('stdin not allowed')
            f_stdin = True
            rendered = self.render_stdin(j2env_overlay)
        else:
            rendered, f_in = self.render_from_file(str(file_in), j2env_overlay)

        if file_out is None:
            if f_stdin:
                f_out = '-'
            else:
                if f_in is None:
                    return _render_error('unable to determine output file name')
                if not f_in.endswith(J2SUBST_TEMPLATE_EXT):
                    return _render_error(f'input file name extension mismatch: {repr(file_in)}')
                f_out = os.path.splitext(f_in)[0]
        else:
            f_out = str(file_out)

        ## safety measures
        if f_out is None:
            return _render_error('unable to determine output file name')

        if is_stdout(f_out):
            if not self.allow_stdin_stdout:
                return _render_error('stdout not allowed')

            sys.stdout.write(rendered)
            sys.stdout.flush()

            if self.unlink:
                if f_stdin:
                    _info('cannot unlink() stdin')
                elif f_in:
                    os.unlink(f_in)

            return True

        ## TODO: there're still TOCTOU windows

        ## safety measures
        if os.path.islink(f_out):
            return _render_error(f'output file is symlink: {f_out}')
        if os.path.exists(f_out):
            if not os.path.isfile(f_out):
                return _render_error(f'output file is not a file: {f_out}')
            if f_in and os.path.samefile(f_in, f_out):
                return _render_error(f'unable to process template inplace: {f_in}')
            if not self.force:
                return _render_error(f'unable to overwrite existing file: {f_out}')

            os.unlink(f_out)

        with open(f_out, mode='w', encoding='utf-8') as f:
            f.reconfigure(write_through=True)
            f.write(rendered)
            f.flush()

        if self.unlink:
            if f_stdin:
                _info('cannot unlink() stdin')
            elif f_in:
                os.unlink(f_in)

        return True

    def render_directory(self, directory: str | PathLike[str], depth: int = 1, j2env_overlay: jinja2.Environment | None = None) -> bool:
        self.__verify_dump_only()

        def _warn(msg: str):
            self.__warn('render_directory', msg)

        def _render_error(msg: str) -> bool:
            _warn(msg)
            return False

        def _info(msg: str):
            self.__info('render_directory', msg)

        def _debug(msg: str):
            self.__debug('render_directory', msg)

        if not os.path.isdir(directory):
            return _render_error(f'not a directory: {repr(directory)}')

        ## minor adjustments
        if depth < 0:
            depth = -1
        if depth == 0:
            _debug('depth == 0')
            return True

        rv = True

        _entries: list[str] = []
        for e in os.listdir(directory):
            if e.startswith('.'):
                ## silently ignore hidden files
                continue
            _entries.append(e)

        for e in natsort.natsorted(_entries):
            p = os.path.join(directory, e)

            if os.path.isdir(p):
                if depth < 0:
                    rv &= self.render_directory(p, depth, j2env_overlay)
                else:
                    rv &= self.render_directory(p, depth - 1, j2env_overlay)
                continue

            if e.endswith(J2SUBST_TEMPLATE_EXT) and os.path.isfile(p):
                rv &= self.render_file(p, None, j2env_overlay)
                continue

            _info(f'ignore: {e}')

        return rv

    def handle_simple_cli_args(self, arg1: str | PathLike[str], arg2: str | PathLike[str] | None = None) -> tuple[str | None, str | None]:
        _in, _out = (None, None)

        ## 1st argument is missing or empty
        if not arg1:
            return (_in, _out)

        if is_stdin(arg1):
            _in = '-'
        else:
            a = os.path.normpath(arg1)
            if os.path.isfile(a) and a.endswith(J2SUBST_TEMPLATE_EXT):
                _in = str(arg1)

        ## early exit:
        ## 1) 1st argument not a stdin or file with supported file name extension
        ## 2) 2nd argument is missing or empty
        if (_in is None) or (not arg2):
            return (_in, _out)

        if is_stdout(arg2):
            _out = '-'
        else:
            a = os.path.normpath(arg2)
            if a.endswith(J2SUBST_TEMPLATE_EXT):
                ## perform regular processing: 2nd argument is (probably) template too
                _in = None
            else:
                _out = a

        return (_in, _out)
