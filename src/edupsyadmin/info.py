import os

from keyring import get_keyring

from .__version__ import __version__


def info(
    app_uid: str | os.PathLike[str],  # noqa : ARG001
    app_username: str,
    database_url: str,
    config_path: str | os.PathLike[str],
    salt_path: os.PathLike[str],
) -> None:
    print(f"edupsyadmin version: {__version__}")
    print(f"app_username: {app_username}")
    print(f"database_url: {database_url}")
    print(f"config_path: {config_path}")
    print(f"keyring backend: {get_keyring()}")
    print(f"salt_path: {salt_path}")
