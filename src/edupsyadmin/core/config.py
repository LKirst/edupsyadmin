"""Global application configuration.

This module defines a global configuration object. Other modules should use
this object to store application-wide configuration values.

"""

from os import PathLike
from re import compile
from string import Template
from typing import Any

from yaml import SafeLoader, ScalarNode, safe_load

from .logger import logger

__all__ = "YamlConfig", "config"


class _AttrDict(dict[str, Any]):
    """A dict-like object with attribute access."""

    def __getitem__(self, key: str) -> Any:
        """Access dict values by key.

        :param key: key to retrieve
        """
        value = super().__getitem__(key)
        if isinstance(value, dict):
            # For mixed recursive assignment (e.g. `a["b"].c = value` to work
            # as expected, all dict-like values must themselves be _AttrDicts.
            # The "right way" to do this would be to convert to an _AttrDict on
            # assignment, but that requires overriding both __setitem__
            # (straightforward) and __init__ (good luck). An explicit type
            # check is used here instead of EAFP because exceptions would be
            # frequent for hierarchical data with lots of nested dicts.
            self[key] = value = _AttrDict(value)
        return value

    def __getattr__(self, key: str) -> object:
        """Get dict values as attributes.

        :param key: key to retrieve
        """
        return self[key]

    def __setattr__(self, key: str, value: object) -> None:
        """Set dict values as attributes.

        :param key: key to set
        :param value: new value for key
        """
        self[key] = value


class YamlConfig(_AttrDict):
    """Store YAML configuration data.

    After loading, data can be accessed as dict values or object attributes.

    """

    def __init__(
        self,
        path: list[str | PathLike[str]] | str | PathLike[str] | None = None,
        root: str | None = None,
        params: dict[str, Any] | None = None,
    ) -> None:
        """Initialize this object.

        :param path: config file path to load
        :param root: place config values at this root
        :param params: macro substitutions
        """
        super().__init__()
        if path:
            self.load(path, root, params)

    def load(
        self,
        path: list[str | PathLike[str]] | str | PathLike[str],
        root: str | None = None,
        params: dict[str, Any] | None = None,
    ) -> None:
        """Load data from YAML configuration files.

        Configuration values are read from a sequence of one or more YAML
        files. Files are read in the given order, and a duplicate value will
        overwrite the existing value. If a root is specified the config data
        will be loaded under that attribute.

        :param path: config file path(s) to load
        :param root: place config values at this root
        :param params: mapping of parameter substitutions
        """
        if isinstance(path, str | PathLike):
            path = [path]

        tag = _ParameterTag(params)
        tag.add(SafeLoader)
        for p in path:
            with open(p, encoding="UTF-8") as stream:
                logger.info(f"reading config data from '{p}'")
                data = safe_load(stream)
            try:
                if root:
                    self.setdefault(root, {}).update(data)
                else:
                    self.update(data)
            except TypeError:  # data is None
                logger.warning(f"config file {p} is empty")


class _ParameterTag:
    """YAML tag for performing parameter substitution on a scalar node.

    Enable this tag by calling add_constructor() for the SafeLoader class.

    """

    NAME = "param"

    def __init__(self, params: dict[str, Any] | None = None) -> None:
        """Initialize this object.

        :param params: key-value replacement mapping
        """
        self._params = {}
        if params:
            self._params.update(params)

    def __call__(self, loader: SafeLoader, node: ScalarNode) -> str:
        """Implement the tag constructor interface.

        :param loader: YAML loader
        :param node: YAML node to process
        :return: final value
        """
        value = loader.construct_scalar(node)
        return Template(value).substitute(self._params)

    def add(self, loader: type[SafeLoader]) -> None:
        """Add this tag to the SafeLoader class.

        This adds a the tag constructor and an implicit resolver to the
        loader

        :param loader: loader class
        """
        loader.add_implicit_resolver(self.NAME, compile(r"(?=.*$)"), None)  # type: ignore [no-untyped-call]
        loader.add_constructor(self.NAME, self)


def convert_config_to_dict(conf: dict[str, Any] | _AttrDict) -> dict[str, Any]:
    if isinstance(conf, dict):
        conf = dict(conf)
    for key, value in conf.items():
        if isinstance(value, dict):
            conf[key] = dict(convert_config_to_dict(value))
    return conf


config = YamlConfig()
