from datetime import datetime

from pyramid.config import Configurator
from restalchemy.exceptions import AttributeWrong
from sqlalchemy import DECIMAL, DateTime, Enum, Float, Integer, String, event

from .model import RestalchemyBase


def validate_int(column, value):
    if isinstance(value, str):
        try:
            value = int(value)
        except ValueError:
            raise AttributeWrong(column.key, f'"{value}" is not a valid number')

    if type(value) is not int:  # isinstance doesn't work because bool is subclass of int
        raise AttributeWrong(column.key, '"{value}" has to be a number')

    return value


def validate_float(column, value):
    if isinstance(value, str):
        try:
            value = float(value)
        except ValueError:
            raise AttributeWrong(column.key, f'"{value}" is not a valid float')

    if type(value) is not float:  # isinstance doesn't work because bool is subclass of int
        raise AttributeWrong(column.key, f'"{value}" has to be a float')

    return value


def validate_string(column, value):
    if not isinstance(value, str):
        raise AttributeWrong(column.key, f'"{value}" is not a string')
    return value


def validate_enum(column, value):
    enums = column.type.enums
    if value not in enums:
        raise AttributeWrong(column.key, f'"{value}" is not one of: {", ".join(e for e in enums)}.')
    return value


def validate_datetime(column, value):
    if isinstance(value, datetime):
        return value

    if not isinstance(value, str):
        raise AttributeWrong(column.key, "Datetime must be a string")

    if value == "0000-00-00T00:00:00":  # mysql allows 0000-00-00 dates for invalid dates
        return value

    orig_value = value
    # Allow ' ' or 'T' as date-time separator and only allow UTC timezone ('Z' or '+0000')
    value = value.replace("T", " ").replace("Z", "+")
    value, _, tz = value.partition("+")
    if tz.strip("0:") != "":
        raise AttributeWrong(column.key, "Only UTC (+0000) datetimes supported")

    _, _, microseconds = value.partition(".")
    # We (or better, Python) only supports microseconds (6 digits)
    if len(microseconds) > 6:
        value = value[: -(len(microseconds) - 6)]
    try:
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S.%f")
    except ValueError:
        pass

    try:
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        pass

    try:
        return datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        raise AttributeWrong(column.key, f'"{orig_value}" is not a valid datetime')


validators = {
    DateTime: validate_datetime,
    DECIMAL: validate_float,
    Float: validate_float,
    Integer: validate_int,
    String: validate_string,
    Enum: validate_enum,
}


def validate(value, column):
    """Check if `value` is a valid sqlalchemy type for `column`."""
    try:
        validator = validators.get(column.type.__class__)
    except Exception:
        return value
    if validator and value is not None:
        return validator(column, value)
    return value


def includeme(config: Configurator):
    # This event is called whenever an attribute on a class is instrumented
    @event.listens_for(RestalchemyBase, "attribute_instrument")
    def configure_listener(class_, key, inst):
        if not hasattr(inst.property, "columns"):
            return

        # This event is called whenever a "set"
        # occurs on that instrumented attribute
        @event.listens_for(inst, "set", retval=True)
        def set_(instance, value, oldvalue, initiator):
            return validate(value, inst.property.columns[0])
