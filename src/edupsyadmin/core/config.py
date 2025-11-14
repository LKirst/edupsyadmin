"""Global application configuration.

This module defines a global configuration object based on Pydantic models.
Other modules should use this object to access application-wide configuration
values.

"""

from os import PathLike
from typing import Any

import yaml
from pydantic import BaseModel, Field

from edupsyadmin.core.logger import logger

__all__ = ("AppConfig", "CoreConfig", "SchoolConfig", "SchoolpsyConfig", "config")


class CoreConfig(BaseModel):
    """Pydantic model for the 'core' section of the config."""

    logging: str = "WARN"
    app_uid: str = "liebermann-schulpsychologie.github.io"
    app_username: str
    config: str | None = None  # This is added at runtime


class SchoolpsyConfig(BaseModel):
    """Pydantic model for the 'schoolpsy' section of the config."""

    schoolpsy_name: str
    schoolpsy_street: str
    schoolpsy_city: str


class SchoolConfig(BaseModel):
    """Pydantic model for a single school's configuration."""

    school_head_w_school: str
    school_name: str
    school_street: str
    school_city: str
    end: int
    nstudents: int


class CsvImportConfig(BaseModel):
    """Pydantic model for a single csv import configuration."""

    separator: str
    column_mapping: dict[str, str]


class LgvtConfig(BaseModel):
    Rosenkohl: str | None = None
    Laufbursche: str | None = None
    Toechter: str | None = None


class AppConfig(BaseModel):
    """The main Pydantic model for the entire configuration."""

    core: CoreConfig
    schoolpsy: SchoolpsyConfig
    school: dict[str, SchoolConfig]
    form_set: dict[str, list[str]] = Field(default_factory=dict)
    csv_import: dict[str, CsvImportConfig] = Field(default_factory=dict)
    lgvtcsv: LgvtConfig | None = None


class Settings:
    """
    A wrapper class to manage loading the configuration and providing a
    global access point.
    """

    _instance: AppConfig | None = None

    def load(self, path: str | PathLike[str]) -> None:
        """
        Load data from a YAML configuration file.

        The file is read and validated against the Pydantic models.
        """
        with open(path, encoding="UTF-8") as stream:
            logger.debug(f"reading config data from '{path}'")
            data = yaml.safe_load(stream)

        if not data:
            raise ValueError("Configuration could not be loaded or is empty.")

        self._instance = AppConfig(**data)

    def __getattr__(self, name: str) -> Any:
        """Delegate attribute access to the loaded AppConfig instance."""
        if self._instance is None:
            raise RuntimeError("Configuration not loaded. Call config.load() first.")
        return getattr(self._instance, name)

    def __setattr__(self, name: str, value: Any) -> None:
        """
        Set attributes on the wrapper or the loaded AppConfig instance.
        """
        if name == "_instance":
            super().__setattr__(name, value)
        elif self._instance is not None:
            # Allow modifying attributes on the loaded Pydantic model
            # (e.g., for runtime values like `config.core.config`).
            # This will raise a validation error if the type is wrong.
            setattr(self._instance, name, value)
        else:
            # This case should ideally not be hit after loading.
            super().__setattr__(name, value)


config = Settings()
