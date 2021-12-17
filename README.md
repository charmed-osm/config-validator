# Config Validator

Basic config validator for Python.

Python version: >= 3.8

## Install

```shell
python3 -m pip install git+https://github.com/charmed-osm/config-validator
```

## Example

```python
from typing import List, Optional
from config_validator import ConfigValidator, validator

class MyConfig(ConfigValidator):
    enable_debug: bool  # check is boolean
    debug_level: str  # check is string
    users: List[str]  # check is a list of strings
    projects: Optional[List[str]]  # if set, check is a list of strings
    # Validate debug_level value
    @validator("debug_level")
    def validate_debug_level(self, value):
        valid_options = ("debug", "info", "warning", "error")
        lowercase_value = value.lower()
        if lowercase_value not in valid_options:
            raise ValueError("invalid value for debug_options.")
        return lowercase_value

my_config_object = MyConfig(**{
    "enable_debug": True,
    "debug_level": "info",
    "users": ["admin", "guess"],
})
```