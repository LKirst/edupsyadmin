"""Benchmark the key derivation function."""

import pytest

from edupsyadmin.core.encrypt import Encryption


@pytest.mark.parametrize("iterations", [480_000, 800_000, 1_200_000])
def test_key_derivation_benchmark(benchmark, tmp_path, iterations):
    """Benchmark the set_fernet method with varying iterations."""
    encr = Encryption()
    salt_path = tmp_path / "salt.txt"

    def run_derivation():
        # Reset fernet before each call, as the method will return early
        # if it's already set, which would skew the benchmark results.
        encr.fernet = None
        encr.set_fernet(
            username="test_user_do_not_use",
            salt_path=salt_path,
            uid="example.com",
            iterations=iterations,
        )

    benchmark(run_derivation)
