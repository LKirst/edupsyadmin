import os
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# The module under test
from edupsyadmin.utils.path_utils import normalize_path

# Path where the `Path` object is actually looked up by `normalize_path`
PATH_MODULE_TARGET = "edupsyadmin.utils.path_utils.Path"


def test_normalize_path_home_directory_expansion(monkeypatch):
    """Test that normalize_path correctly expands the user home directory (~)."""
    mock_home = Path("/mock/home/user")
    final_resolved_path = mock_home / "some_file"

    # Mock the Path object returned by Path(path_str)
    mock_initial_path_instance = MagicMock(spec=Path)

    # The expanduser method of mock_initial_path_instance should return another mock
    mock_expanded_path_instance = MagicMock(spec=Path)
    mock_expanded_path_instance.resolve.return_value = final_resolved_path
    mock_initial_path_instance.expanduser.return_value = mock_expanded_path_instance

    # Monkeypatch the Path class itself to be a MagicMock
    mock_path_class = MagicMock(return_value=mock_initial_path_instance)
    monkeypatch.setattr(PATH_MODULE_TARGET, mock_path_class)

    path_str = "~/some_file"
    normalized_path = normalize_path(path_str)
    assert normalized_path == final_resolved_path
    mock_path_class.assert_called_once_with(path_str)
    mock_initial_path_instance.expanduser.assert_called_once()
    mock_expanded_path_instance.resolve.assert_called_once()


def test_normalize_path_relative_path_resolution(monkeypatch):
    """Test that normalize_path correctly resolves relative paths to absolute paths."""
    mock_cwd = Path("/mock/current/working/dir")
    final_resolved_path = mock_cwd / "relative_dir" / "file.txt"

    mock_initial_path_instance = MagicMock(spec=Path)
    mock_expanded_path_instance = MagicMock(spec=Path)
    mock_expanded_path_instance.resolve.return_value = final_resolved_path
    mock_initial_path_instance.expanduser.return_value = mock_expanded_path_instance

    mock_path_class = MagicMock(return_value=mock_initial_path_instance)
    monkeypatch.setattr(PATH_MODULE_TARGET, mock_path_class)

    path_str = "relative_dir/file.txt"
    normalized_path = normalize_path(path_str)
    assert normalized_path == final_resolved_path
    mock_path_class.assert_called_once_with(path_str)
    mock_initial_path_instance.expanduser.assert_called_once()
    mock_expanded_path_instance.resolve.assert_called_once()


def test_normalize_path_absolute_path_unchanged(monkeypatch):
    """Test that normalize_path returns an absolute path as is after resolving."""
    abs_path = Path("/an/absolute/path/to/file.pdf")

    mock_initial_path_instance = MagicMock(spec=Path)
    mock_expanded_path_instance = MagicMock(spec=Path)
    mock_expanded_path_instance.resolve.return_value = abs_path
    mock_initial_path_instance.expanduser.return_value = mock_expanded_path_instance

    mock_path_class = MagicMock(return_value=mock_initial_path_instance)
    monkeypatch.setattr(PATH_MODULE_TARGET, mock_path_class)

    path_str = "/an/absolute/path/to/file.pdf"
    normalized_path = normalize_path(path_str)
    assert normalized_path == abs_path
    mock_path_class.assert_called_once_with(path_str)
    mock_initial_path_instance.expanduser.assert_called_once()
    mock_expanded_path_instance.resolve.assert_called_once()


def test_normalize_path_empty_string_raises_value_error():
    """Test that normalize_path raises ValueError for an empty path string."""
    with pytest.raises(ValueError, match="Path cannot be empty"):
        normalize_path("")


def test_normalize_path_user_specific_home_expansion(monkeypatch):
    """Test that normalize_path handles '~user' expansion correctly."""
    mock_user_home_path = Path("/home/specific_user")
    final_resolved_path = mock_user_home_path

    # Mock os.path.expanduser as Path.expanduser internally uses it for ~user
    monkeypatch.setattr(os.path, "expanduser", lambda p: str(mock_user_home_path))

    mock_initial_path_instance = MagicMock(spec=Path)
    mock_expanded_path_instance = MagicMock(spec=Path)
    mock_expanded_path_instance.resolve.return_value = final_resolved_path
    mock_initial_path_instance.expanduser.return_value = mock_expanded_path_instance

    mock_path_class = MagicMock(return_value=mock_initial_path_instance)
    monkeypatch.setattr(PATH_MODULE_TARGET, mock_path_class)

    path_str = "~specific_user"
    normalized_path = normalize_path(path_str)
    assert normalized_path == final_resolved_path
    mock_path_class.assert_called_once_with(path_str)
    mock_initial_path_instance.expanduser.assert_called_once()
    mock_expanded_path_instance.resolve.assert_called_once()
