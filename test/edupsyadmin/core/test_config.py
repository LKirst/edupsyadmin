"""Test suite for the core.config module."""

import pytest
from pydantic import ValidationError

from edupsyadmin.core.config import AppConfig, config

# A minimal, valid config
valid_config_content = """
core:
  app_username: "testuser"
schoolpsy:
  schoolpsy_name: "Test Psy"
  schoolpsy_street: "123 Street"
  schoolpsy_city: "Test City"
school:
  TestSchool:
    school_head_w_school: "Head"
    school_name: "Test School"
    school_street: "456 Avenue"
    school_city: "Test Town"
    end: 12
    nstudents: 500
"""

# An invalid config (missing required field `app_username`)
invalid_config_missing_field = """
core:
  logging: "INFO"
schoolpsy:
  schoolpsy_name: "Test Psy"
  schoolpsy_street: "123 Street"
  schoolpsy_city: "Test City"
school:
  TestSchool:
    school_head_w_school: "Head"
    school_name: "Test School"
    school_street: "456 Avenue"
    school_city: "Test Town"
    end: 12
    nstudents: 500
"""

# An invalid config (wrong type for `nstudents`)
invalid_config_wrong_type = """
core:
  app_username: "testuser"
schoolpsy:
  schoolpsy_name: "Test Psy"
  schoolpsy_street: "123 Street"
  schoolpsy_city: "Test City"
school:
  TestSchool:
    school_head_w_school: "Head"
    school_name: "Test School"
    school_street: "456 Avenue"
    school_city: "Test Town"
    end: 12
    nstudents: "five hundred"
"""


def test_successful_load(tmp_path):
    """Test that a valid config file is loaded correctly."""
    conf_path = tmp_path / "config.yml"
    conf_path.write_text(valid_config_content)

    config.load(str(conf_path))

    # Check that the loaded config is an instance of our Pydantic model
    assert isinstance(config._instance, AppConfig)
    # Check attribute access
    assert config.core.app_username == "testuser"
    assert config.school["TestSchool"].nstudents == 500
    # Check default value
    assert config.core.logging == "WARN"


def test_load_invalid_config_missing_field(tmp_path):
    """Test that loading a config with a missing required field
    raises ValidationError.
    """
    conf_path = tmp_path / "invalid.yml"
    conf_path.write_text(invalid_config_missing_field)

    with pytest.raises(ValidationError) as excinfo:
        config.load(str(conf_path))

    # Check that the error message is helpful
    assert "core.app_username" in str(excinfo.value)
    assert "Field required" in str(excinfo.value)


def test_load_invalid_config_wrong_type(tmp_path):
    """Test that loading a config with a wrong type raises ValidationError."""
    conf_path = tmp_path / "invalid.yml"
    conf_path.write_text(invalid_config_wrong_type)

    with pytest.raises(ValidationError) as excinfo:
        config.load(str(conf_path))

    # Check that the error message points to the right field
    assert "school.TestSchool.nstudents" in str(excinfo.value)
    assert "Input should be a valid integer" in str(excinfo.value)
