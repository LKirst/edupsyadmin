"""Test execution time of functions in the core.encrypt module."""

import os
import timeit
from pathlib import Path

from edupsyadmin.core.encrypt import Encryption

SECRET_MESSAGE = b"This is a secret message"


def setup():
    encr = Encryption()
    encr.set_fernet("test_user_do_not_use", "test/data/testconfig.yml", "example.com")
    return encr


def encrypt(encr):
    token = encr.encrypt(SECRET_MESSAGE)
    return token


def decrypt(encr, token):
    data = encr.decrypt(token)
    return data


if __name__ == "__main__":
    print(f"CWD: {os.getcwd()}")
    cfg_path = Path("test/data/testconfig.yml")
    if not cfg_path.parent.exists():
        os.makedirs(cfg_path.parent)
    open(cfg_path, mode="a").close()

    number_calls = 10

    time_setup = timeit.timeit("setup()", globals=globals(), number=number_calls)
    print(f"setup: {time_setup / number_calls}")

    time_encrypt = timeit.timeit(
        "encrypt(encr)", setup="encr=setup()", globals=globals(), number=number_calls
    )
    print(f"decrypt: {time_encrypt / number_calls}")

    time_decrypt = timeit.timeit(
        "decrypt(encr,token)",
        setup="encr=setup();token=encrypt(encr)",
        globals=globals(),
        number=number_calls,
    )
    print(f"decrypt: {time_decrypt / number_calls}")

    os.remove(cfg_path)
