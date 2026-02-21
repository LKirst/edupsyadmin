from pathlib import Path

from platformdirs import user_config_dir, user_data_path

from edupsyadmin.__version__ import __version__

__all__ = (
    "APP_UID",
    "DEFAULT_CONFIG_DIR",
    "DEFAULT_CONFIG_PATH",
    "DEFAULT_DB_URL",
    "DEFAULT_SALT_PATH",
    "USER_DATA_DIR",
)

APP_UID = "liebermann-schulpsychologie.github.io"
USER_DATA_DIR = user_data_path(
    appname="edupsyadmin", version=__version__, ensure_exists=True
)
DEFAULT_DB_URL = "sqlite:///" + str(USER_DATA_DIR / "edupsyadmin.db")
DEFAULT_CONFIG_DIR = Path(
    user_config_dir(appname="edupsyadmin", version=__version__, ensure_exists=True)
)
DEFAULT_CONFIG_PATH = DEFAULT_CONFIG_DIR / "config.yml"
DEFAULT_SALT_PATH = DEFAULT_CONFIG_DIR / "salt.txt"
