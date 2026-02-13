from typing import (
    Any,
    Callable,
)

## this module
from .j2subst import J2subst


## placeholder - will be overridden by J2subst instance during mixin loading
instance_getter: Callable[[], J2subst | None] = lambda: None


def get_instance() -> J2subst | None:
    return instance_getter()


def set_instance_getter(getter: Callable[[], J2subst | None]) -> None:
    global instance_getter
    instance_getter = getter


def j2subst_function(*args, **kwargs) -> Any:
    j2i: J2subst | None = get_instance()
    if j2i is None:
        return None

    def handle_func(func: Any, alias: str | None = None, as_filter: bool = True):
        j2i.import_function(func, alias)
        if as_filter:
            j2i.import_filter(func, alias)

    if len(args) == 1 and callable(args[0]) and not kwargs:
        func = args[0]
        handle_func(func)
        return func

    def inner_decorator(func: Any) -> Any:
        alias = kwargs.get('alias')
        if not isinstance(alias, str):
            alias = None
        as_filter = bool(kwargs.get('as_filter', True))
        handle_func(func, alias, as_filter)
        return func

    return inner_decorator


def j2subst_filter(*args, **kwargs) -> Any:
    j2i: J2subst | None = get_instance()
    if j2i is None:
        return None

    def handle_func(func: Any, alias: str | None = None):
        j2i.import_filter(func, alias)

    if len(args) == 1 and callable(args[0]) and not kwargs:
        func = args[0]
        handle_func(func)
        return func

    def inner_decorator(func: Any) -> Any:
        alias = kwargs.get('alias')
        if not isinstance(alias, str):
            alias = None
        handle_func(func, alias)
        return func

    return inner_decorator
