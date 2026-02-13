import enum

## NB: members must be listed in upper case
class J2substFileKind(enum.Enum):
    IGNORED = enum.auto()
    CONFIG  = enum.auto()
    MIXIN = enum.auto()
