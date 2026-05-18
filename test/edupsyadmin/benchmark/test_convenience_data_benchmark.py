import pytest

from edupsyadmin.api.client_view import ClientView
from edupsyadmin.api.types import ClientRecord


@pytest.fixture
def sample_client_data() -> ClientRecord:
    return ClientRecord.model_validate(
        {
            "client_id": 1,
            "first_name_encr": "Erika",
            "last_name_encr": "Mustermann",
            "street_encr": "Teststraße 1",
            "city_encr": "12345 Teststadt",
            "school": "FirstSchool",
            "birthday_encr": "2010-01-01",
            "class_int_encr": 5,
            "nta_nos_end": True,
            "nta_nos_end_grade": 10,
            "lrst_diagnosis_encr": "lrst",
            "lrst_last_test_by_encr": "schpsy",
            "lrst_last_test_date_encr": "2023-01-01",
            "entry_date_encr": "2022-09-01",
            "document_shredding_date_encr": "2030-01-01",
        }
    )


def test_benchmark_client_view_model_dump(benchmark, mock_config, sample_client_data):
    """Benchmark ClientView.model_dump()."""

    def run():
        view = ClientView.model_validate(sample_client_data)
        view.model_dump()

    benchmark(run)


def test_benchmark_client_view_property_access(
    benchmark, mock_config, sample_client_data
):
    """Benchmark repeated property access on ClientView (caching effect)."""
    view = ClientView.model_validate(sample_client_data)
    # Warm up cache
    _ = view.school_year
    _ = view.schoolpsy_addr_s_wname
    _ = view.schoolpsy_name

    def run():
        # Accessing cached properties
        _ = view.school_year
        _ = view.schoolpsy_addr_s_wname
        _ = view.schoolpsy_name

    benchmark(run)
