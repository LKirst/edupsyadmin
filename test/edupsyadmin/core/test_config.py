"""Test suite for the core.config module.

The script can be executed on its own or incorporated into a larger test suite.
However the tests are run, be aware of which version of the package is actually
being tested. If the package is installed in site-packages, that version takes
precedence over the version in this project directory. Use a virtualenv test
environment or setuptools develop mode to test against the development version.

"""

from os import environ

import pytest

from edupsyadmin.core.config import YamlConfig

conf1_content = """
str: $$str  # literal `$`, no substitution
env: ${env1}${env2}
var: ${var1}$var2
"""
conf2_content = """
var: ${var1}$var3  # override `var` in conf1.yml
"""


class YamlConfigTest(object):
    """Test suite for the YamlConfig class."""

    @classmethod
    @pytest.fixture
    def files(cls, tmp_path):
        """Create configuration files for testing."""
        # Create conf1.yml and conf2.yml in the temporary path
        conf1_path = tmp_path / "conf1.yml"
        conf2_path = tmp_path / "conf2.yml"
        conf1_path.write_text(conf1_content.strip())
        conf2_path.write_text(conf2_content.strip())

        return conf1_path, conf2_path

    @classmethod
    @pytest.fixture
    def params(cls):
        """Define configuration parameters."""
        environ.update({"env1": "ENV1", "env2": "ENV2"})
        return {"var1": "VAR1", "var2": "VAR2", "var3": "VAR3", "env2": "VAR2"}

    def test_item(self):
        """Test item access."""
        config = YamlConfig()
        config["root"] = {}
        config["root"]["key"] = "value"
        assert config["root"]["key"] == "value"
        return

    def test_attr(self):
        """Test attribute access."""
        config = YamlConfig()
        config.root = {}
        config.root.key = "value"
        assert config.root.key == "value"
        return

    @pytest.mark.parametrize("root", (None, "root"))
    def test_init(self, files, params, root):
        """Test the __init__() method for loading a file."""
        merged = {"str": "$str", "env": "ENV1VAR2", "var": "VAR1VAR3"}
        config = YamlConfig(files, root, params)
        if root:
            assert config == {root: merged}
        else:
            assert config == merged
        return

    @pytest.mark.parametrize("root", (None, "root"))
    def test_load(self, files, params, root):
        """Test the load() method."""
        merged = {"str": "$str", "env": "ENV1VAR2", "var": "VAR1VAR3"}
        config = YamlConfig()
        config.load(files, root, params)
        if root:
            assert config == {root: merged}
        else:
            assert config == merged
        return


# Make the module executable.

if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))