import enum

## NB: formats must be listed in upper case
class J2substDumpFormat(enum.Enum):
    YAML = enum.auto()
    JSON = enum.auto()
