"""Tests for filesystem migration logic."""

from edupsyadmin.api.migration_fs import (
    find_latest_versioned_dir,
    looks_like_version,
    migrate_to_stable_paths,
)


def test_looks_like_version():
    assert looks_like_version("1.0.0") is True
    assert looks_like_version("8.2.1") is True
    assert looks_like_version("10.0.12") is True
    assert looks_like_version("v1.0.0") is False
    assert looks_like_version("1.0") is False
    assert looks_like_version("abc") is False


def test_find_latest_versioned_dir(tmp_path):
    # No subdirs
    assert find_latest_versioned_dir(tmp_path) is None

    # Only non-version subdirs
    (tmp_path / "data").mkdir()
    assert find_latest_versioned_dir(tmp_path) is None

    # Multiple version subdirs
    (tmp_path / "1.0.0").mkdir()
    (tmp_path / "2.1.0").mkdir()
    (tmp_path / "1.2.3").mkdir()
    (tmp_path / "10.0.0").mkdir()

    latest = find_latest_versioned_dir(tmp_path)
    assert latest is not None
    assert latest.name == "10.0.0"


def test_migrate_to_stable_paths(tmp_path):
    # Setup mock paths
    config_dir = tmp_path / "config"
    data_dir = tmp_path / "data"
    config_dir.mkdir()
    data_dir.mkdir()

    # Create old versioned data
    old_version = "8.2.1"
    old_config_dir = config_dir / old_version
    old_data_dir = data_dir / old_version
    old_config_dir.mkdir()
    old_data_dir.mkdir()

    old_config_file = old_config_dir / "config.yml"
    old_config_file.write_text("old config")
    old_salt_file = old_config_dir / "salt.txt"
    old_salt_file.write_text("old salt")
    old_db_file = old_data_dir / "edupsyadmin.db"
    old_db_file.write_text("old db")

    migrate_to_stable_paths(
        config_file=config_dir / "config.yml",
        salt_file=config_dir / "salt.txt",
        db_file=data_dir / "edupsyadmin.db",
    )

    # Verify migration
    assert (config_dir / "config.yml").read_text() == "old config"
    assert (config_dir / "salt.txt").read_text() == "old salt"
    assert (data_dir / "edupsyadmin.db").read_text() == "old db"
    # Verify backup was created
    assert (data_dir / "edupsyadmin.db.bak").exists()
    assert (data_dir / "edupsyadmin.db.bak").read_text() == "old db"


def test_migrate_no_overwrite(tmp_path):
    # Setup mock paths
    config_dir = tmp_path / "config"
    data_dir = tmp_path / "data"
    config_dir.mkdir()
    data_dir.mkdir()

    # Create existing "new" data
    (config_dir / "config.yml").write_text("new config")

    # Create old versioned data
    old_version = "8.2.1"
    old_config_dir = config_dir / old_version
    old_config_dir.mkdir()
    (old_config_dir / "config.yml").write_text("old config")

    migrate_to_stable_paths(
        config_file=config_dir / "config.yml",
        salt_file=config_dir / "salt.txt",
        db_file=data_dir / "edupsyadmin.db",
    )

    # Should NOT overwrite existing config
    assert (config_dir / "config.yml").read_text() == "new config"
