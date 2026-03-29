import pytest
from cryptography.fernet import Fernet

from edupsyadmin.api.managers import ClientsManager
from edupsyadmin.api.migration import upgrade_db
from edupsyadmin.core.encrypt import encr


@pytest.fixture
def benchmark_db(tmp_path, mock_config):
    """Set up a database with 80 clients for benchmarking."""
    database_path = tmp_path / "benchmark.sqlite"
    database_url = f"sqlite:///{database_path}"
    upgrade_db(database_url)

    # Set up encryption
    encr.set_keys([Fernet.generate_key()])

    manager = ClientsManager(database_url=database_url)

    # Add 80 clients
    for i in range(80):
        manager.add_client(
            school="FirstSchool",
            gender_encr="f",
            class_name_encr="1A",
            first_name_encr=f"Firstname_{i}",
            last_name_encr=f"Lastname_{i}",
            birthday_encr="2010-01-01",
            street_encr="Teststreet 1",
            city_encr="12345 Testcity",
            parent_encr="Parent Name",
            telephone1_encr="0123456789",
            email_encr="test@example.com",
            entry_date_encr="2020-09-01",
            keyword_taet_encr="slbb.slb.sonstige",
            notes_encr="Some encrypted notes for benchmarking decryption speed.",
        )
    return manager


def test_decrypt_single_client_benchmark(benchmark, benchmark_db):
    """Benchmark decrypting all fields of a single client."""

    def decrypt_one():
        # get_decrypted_client triggers decryption of all fields
        return benchmark_db.get_decrypted_client(1)

    benchmark(decrypt_one)


def test_decrypt_80_clients_benchmark(benchmark, benchmark_db):
    """Benchmark decrypting all fields of 80 clients."""

    def decrypt_80():
        # get_clients_overview triggers decryption of all fields for all
        # clients during the SQLAlchemy result processing.
        return benchmark_db.get_clients_overview(columns=["all"])

    benchmark(decrypt_80)
