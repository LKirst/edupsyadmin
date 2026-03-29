"""Benchmark the encryption functions."""

import pytest
from cryptography.fernet import Fernet

from edupsyadmin.core.encrypt import Encryption

SECRET_MESSAGE = "This is a secret message"


@pytest.fixture
def encryption_service():
    """Set up encryption service."""
    encr = Encryption()
    # Generate a random Fernet key for benchmarking
    key = Fernet.generate_key()
    encr.set_keys([key])
    return encr


def test_core_encrypt_string(benchmark, encryption_service):
    """Benchmark the encrypt function."""
    benchmark(encryption_service.encrypt, SECRET_MESSAGE)


def test_core_decrypt_string(benchmark, encryption_service):
    """Benchmark the decrypt function."""
    token = encryption_service.encrypt(SECRET_MESSAGE)
    benchmark(encryption_service.decrypt, token)
