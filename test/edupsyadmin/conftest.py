from unittest.mock import Mock

import keyring
import pytest


@pytest.fixture
def mock_keyring(monkeypatch):
    class MockCredential:
        def __init__(self, password: str):
            self.password = password

    mock_get_credential = Mock(
        side_effect=lambda service, username: MockCredential(password="mocked_password")
    )

    monkeypatch.setattr(keyring, "get_credential", mock_get_credential)

    return mock_get_credential
