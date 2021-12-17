# Copyright 2021 Canonical Ltd.
# See LICENSE file for licensing details.

"""Basic validator module."""

from collections.abc import Iterable
from typing import Any, List, Union

from typing_inspect import get_args, get_origin

__all__ = ["ValidationError", "ConfigValidator", "validator"]

LIBAPI = 0
LIBPATCH = 1

def validator(field):
    """Validator decorator to do custom validation to attributes.

    Add this decorator to a function to perform additional validation
    to a field of the config. This decorator expects a ValueError
    exception when the validation has failed.

    The decorator will inject one argument to the function with the
    value for the field that is under evaluation.

    The function using this decorator should return the value after
    the validation, which will enable the user to update the value
    while validating.

    Args:
        field: name of the attribute field to validate.

    Example:
        class MyConfig(ConfigValidator):
            debug_level: str

        @validator("debug_level")
        def validate_debug_level(self, value):
            valid_options = ("debug", "info", "warning", "error")
            lowercase_value = value.lower()
            if lowercase_value not in valid_options:
                raise ValueError("invalid value for debug_options.")
            return lowercase_value
    """

    def _call(function):
        def wrapper(field):
            result = function(ConfigValidator, field)
            return result

        wrapper.decorator = True
        wrapper.field = field
        return wrapper

    return _call


class _AttributeErrorTypes:
    INVALID_TYPE = "Invalid type"
    MISSING = "Missing attribute"
    UNDEFINED = "Undefined attribute"


class _AttributeError(Exception):
    def __init__(self, name: str, message: str):
        self.name = name
        self.message = message

    def __str__(self):
        return f"{self.name}\n    {self.message}\n"


class ValidationError(Exception):
    """Raised by the ConfigValidator when the validation is not successful."""

    _message = "{} validation errors.\n{}"

    def __init__(self, exceptions: List[_AttributeError]):
        self.exceptions = exceptions
        self.attribute_errors = {e.name: e.message for e in self.exceptions}

    def __repr__(self):
        return self._message.format(
            len(self.exceptions),
            "".join([str(exception) for exception in self.exceptions]),
        )

    def __str__(self):
        return self.__repr__()


class ConfigValidator:
    """Class for validating a config.

    Inherit from this class to validate attributes of a class. For that,
    you need to specify the types when defining the attributes of your class.
    These are the types supported and tested by this class:
      -  bool
      -  int
      -  str
      -  Tuple
      -  Set
      -  List
      -  Dict
      -  Optional

    Args:
        **data: Dictionary with key values to be validated

    Attributes:
        An attribute will be set per key in the config data ("-" will be replace by "_").

    Example:
        class MyConfig(ConfigValidator):
            enable_debug: bool  # check is boolean
            debug_level: str  # check is string
            users: List[str]  # check is a list of strings
            projects: Optional[List[str]]  # if set, check is a list of strings

        my_config_object = MyConfig(**{
            "enable_debug": True,
            "debug_level": "info",
            "users": ["admin", "guess"],
        })
    """

    def __init__(self, **data: Any):
        data = {k.replace("-", "_"): v for k, v in data.items()}

        values, validation_error = validate_config(self.__class__, data)

        if validation_error:
            raise validation_error

        setattr(self, "__dict__", values)


def validate_config(config, data):
    validation_exceptions = []
    config_attributes = getattr(config, "__annotations__")
    __decorator_validators__ = {
        validator.field: validator
        for validator in config.__dict__.values()
        if hasattr(validator, "decorator")
    }
    error = None
    values = {}
    # extra_attributes = [key for key in data if key not in config_attributes]
    # if extra_attributes:
    #     for extra_attr in extra_attributes:
    #         validation_exceptions.append(
    #             AttributeError(extra_attr, AttributeErrorTypes.UNDEFINED)
    #         )

    for attr_name, attr_type in config_attributes.items():
        optional = _is_optional_type(attr_type)
        type_to_check = _safe_get_type(attr_type)
        args_type = _safe_get_args(attr_type)

        data_value = data.get(attr_name)
        if data_value is None and not optional:
            validation_exceptions.append(_AttributeError(attr_name, _AttributeErrorTypes.MISSING))
        else:
            error_msg = ""
            try:
                _validate(data_value, type_to_check, args_type)
                if attr_name in __decorator_validators__:
                    data[attr_name] = __decorator_validators__[attr_name](data_value)
            except Exception as e:
                error_msg = str(e)
                validation_exceptions.append(_AttributeError(attr_name, error_msg))
                continue
    if validation_exceptions:
        error = ValidationError(exceptions=validation_exceptions)
    else:
        values.update({attr_name: data.get(attr_name) for attr_name in config_attributes})

    return values, error


def _safe_get_type(obj_type):
    if _is_optional_type(obj_type):
        return _safe_get_type(obj_type.__args__[0])
    else:
        origin = get_origin(obj_type)
        return origin if origin is not None else obj_type


def _safe_get_args(obj_type):
    if _is_optional_type(obj_type):
        return _safe_get_args(obj_type.__args__[0])
    else:
        return get_args(obj_type)


def _is_optional_type(obj_type):
    origin = get_origin(obj_type)
    args = get_args(obj_type)
    return origin == Union and len(args) == 2 and args[1] is type(None)  # noqa: E721


def _validate(data_value, type_to_check, args_type):
    if data_value is not None:
        if not isinstance(data_value, type_to_check):
            raise Exception(_AttributeErrorTypes.INVALID_TYPE)
        elif args_type and isinstance(data_value, Iterable):
            for v in data_value:
                tuple_of_types = (
                    (type(v), type(data_value[v])) if isinstance(data_value, dict) else (type(v),)
                )
                if tuple_of_types != args_type:
                    raise Exception(_AttributeErrorTypes.INVALID_TYPE)
