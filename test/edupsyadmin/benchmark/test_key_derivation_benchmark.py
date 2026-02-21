"""Benchmark the key derivation function."""

import pytest

from edupsyadmin.core.encrypt import derive_key_from_password


@pytest.mark.parametrize("iterations", [480_000, 800_000, 1_200_000])
def test_key_derivation_benchmark(benchmark, iterations):
    """Benchmark the derive_key_from_password function with varying iterations."""
    password = "test_password"
    salt = b"\x00" * 16  # Constant salt for the benchmark

    def run_derivation():
        derive_key_from_password(
            password=password,
            salt=salt,
            iterations=iterations,
        )

    benchmark(run_derivation)
