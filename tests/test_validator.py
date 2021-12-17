# Copyright 2021 Canonical Ltd.
# See LICENSE file for licensing details.

from typing import Dict, List, Optional, Set, Tuple

from config_validator import (
    ConfigValidator,
    ValidationError,
    _AttributeError,
    _AttributeErrorTypes,
    validator,
)

MANDATORY_ATTRS = [
    "boolean",
    "integer",
    "string",
    "tuple_attr",
    "set_attr",
    "list_int",
    "list_str",
    "dict_str_int",
    "dict_int_str",
]

VALUES = {
    "boolean": False,
    "integer": 2,
    "string": "1",
    "tuple_attr": (1, 2),
    "set_attr": {1, 2},
    "list_int": [1, 2],
    "list_str": ["1", "2"],
    "dict_str_int": {"1": 1, "2": 2},
    "dict_int_str": {1: "1", 2: "2"},
}


class ExampleConfig(ConfigValidator):
    boolean: bool
    integer: int
    string: str
    tuple_attr: Tuple[int]
    set_attr: Set[int]
    list_int: List[int]
    list_str: List[str]
    dict_str_int: Dict[str, int]
    dict_int_str: Dict[int, str]
    opt_boolean: Optional[bool]
    opt_integer: Optional[int]
    opt_string: Optional[str]
    opt_tuple_attr: Optional[Tuple[int]]
    opt_set_attr: Optional[Set[int]]
    opt_list_int: Optional[List[int]]
    opt_list_str: Optional[List[str]]
    opt_dict_str_int: Optional[Dict[str, int]]
    opt_dict_int_str: Optional[Dict[int, str]]


class ExampleCustomValidationConfig(ConfigValidator):
    log_level: str

    @validator("log_level")
    def validate_log_level(self, v):
        if v not in {"INFO", "DEBUG"}:
            raise ValueError("value must be INFO or DEBUG")
        return v


class ExampleMissingOptionalAttribute(ConfigValidator):
    optional: Optional[str]


def test_validator_all_success():
    data = {attr: VALUES[attr] for attr in MANDATORY_ATTRS}
    data.update({f"opt_{attr}": VALUES[attr] for attr in MANDATORY_ATTRS})
    config = ExampleConfig(**data)
    for attr, value in data.items():
        assert config.__getattribute__(attr) == value


def test_validator_mandatory_success():
    data = {attr: VALUES[attr] for attr in MANDATORY_ATTRS}
    config = ExampleConfig(**data)
    for attr, value in data.items():
        assert config.__getattribute__(attr) == value


def test_validator_mandatory_with_dash_success():
    data = VALUES
    config = ExampleConfig(**data)
    for attr, value in data.items():
        assert config.__getattribute__(attr.replace("-", "_")) == value


def test_validator_wrong():
    testing_data = {attr: None for attr in MANDATORY_ATTRS}
    testing_data.update({f"opt_{attr}": None for attr in MANDATORY_ATTRS})
    for testing_key in testing_data:
        testing_data[testing_key] = [
            wrong_value
            for key, wrong_value in VALUES.items()
            if key != testing_key and f"opt_{key}" != testing_key
        ]

    for i in range(len(VALUES) - 1):
        data = {k: v.pop() for k, v in testing_data.items()}
        raised = False
        try:
            ExampleConfig(**data)
        except ValidationError as e:
            raised = True
            assert all(
                key in e.attribute_errors
                and e.attribute_errors[key] == _AttributeErrorTypes.INVALID_TYPE
                for key in data
                if not ("integer" in key and isinstance(data[key], bool))
            )
        assert raised


def test_validator_missing():
    data = {}
    raised = False
    try:
        ExampleConfig(**data)
    except ValidationError as e:
        raised = True
        assert all(
            key in e.attribute_errors and e.attribute_errors[key] == _AttributeErrorTypes.MISSING
            for key in data
        )
    assert raised


def test_custom_validator_success():
    data = {"log_level": "INFO"}
    ExampleCustomValidationConfig(**data)


def test_custom_validator_exception():
    raised = False
    wrong_data = {"log_level": "WRONG"}
    expected_error = "value must be INFO or DEBUG"
    try:
        ExampleCustomValidationConfig(**wrong_data)
    except ValidationError as e:
        raised = True
        assert expected_error == e.attribute_errors["log_level"]
    assert raised


def test_missing_optional_attr():
    ExampleMissingOptionalAttribute(**{})


def test_attribute_error_exception():
    exception = _AttributeError("name", "message")
    assert f"{exception}" == "name\n    message\n"


def test_validation_error():
    exception = ValidationError([_AttributeError("n1", "m1"), _AttributeError("n2", "m2")])
    assert f"{exception}" == "2 validation errors.\nn1\n    m1\nn2\n    m2\n"
