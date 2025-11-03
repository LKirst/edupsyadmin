"""Benchmark the encryption functions."""

import pytest

from edupsyadmin.core.encrypt import Encryption

SECRET_MESSAGE = "This is a secret message"


@pytest.fixture
def encryption_service(tmp_path):
    """Set up encryption service."""
    encr = Encryption()
    salt_path = tmp_path / "salt.txt"
    encr.set_fernet(
        "test_user_do_not_use",
        salt_path=salt_path,
        uid="example.com",
    )
    return encr


def test_encrypt_benchmark(benchmark, encryption_service):
    """Benchmark the encrypt function."""
    benchmark(encryption_service.encrypt, SECRET_MESSAGE)


def test_decrypt_benchmark(benchmark, encryption_service):
    """Benchmark the decrypt function."""
    token = encryption_service.encrypt(SECRET_MESSAGE)
    benchmark(encryption_service.decrypt, token)
