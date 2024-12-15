from keyring import get_keyring

from . import __version__


def info(app_uid, app_username, database_url, config_path):
    print(f"edupsyadmin version: {__version__}")
    print(f"app_username: {app_username}")
    print(f"database_url: {database_url}")
    print(f"config_path: {config_path}")
    print(f"keyring backend: {get_keyring()}")
