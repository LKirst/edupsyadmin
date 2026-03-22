"""Filesystem migration utilities for moving to stable paths.

NOTE: This module acts as a migration bridge from versioned paths (used in
v8.2.1 and below) to stable, version-less paths (introduced in v9.0.0).
Maintain this logic through v9.x to support users upgrading from v8.
Consider deprecation in v10.0.0 and removal in v11.0.0.
"""

import re
import shutil
from pathlib import Path

from edupsyadmin.core.logger import logger


def looks_like_version(name: str) -> bool:
    """Check if a string looks like a version (e.g., '1.0.0')."""
    return bool(re.match(r"^\d+\.\d+\.\d+$", name))


def _sort_versions(version_strings: list[str]) -> list[str]:
    """Sort version strings numerically (simple semver-like sorting)."""

    def parse_version(v: str) -> tuple[int, ...]:
        return tuple(map(int, v.split(".")))

    return sorted(version_strings, key=parse_version)


def find_latest_versioned_dir(base_dir: Path) -> Path | None:
    """Find the latest versioned subdirectory in a base directory."""
    if not base_dir.exists():
        return None

    versions = [
        d.name for d in base_dir.iterdir() if d.is_dir() and looks_like_version(d.name)
    ]
    if not versions:
        return None

    sorted_versions = _sort_versions(versions)
    return base_dir / sorted_versions[-1]


def create_db_backup(db_path: Path) -> None:
    """Create a backup of the database file."""
    if not db_path.exists():
        return

    backup_path = db_path.with_suffix(".db.bak")
    logger.info(f"Creating database backup at {backup_path}")
    shutil.copy2(db_path, backup_path)


def _migrate_config(config_file: Path) -> None:
    """Migrate config file from versioned subdirectory."""
    if config_file.exists():
        return

    latest_config_dir = find_latest_versioned_dir(config_file.parent)
    if not latest_config_dir:
        return

    old_config = latest_config_dir / "config.yml"
    if old_config.exists():
        logger.info(f"Migrating config from {old_config} to {config_file}")
        shutil.copy2(old_config, config_file)


def _migrate_salt(salt_file: Path) -> None:
    """Migrate salt file from versioned subdirectory."""
    if salt_file.exists():
        return

    latest_salt_dir = find_latest_versioned_dir(salt_file.parent)
    if not latest_salt_dir:
        return

    old_salt = latest_salt_dir / "salt.txt"
    if old_salt.exists():
        logger.info(f"Migrating salt from {old_salt} to {salt_file}")
        shutil.copy2(old_salt, salt_file)


def _migrate_database(db_file: Path) -> None:
    """Migrate database file from versioned subdirectory."""
    if db_file.exists():
        return

    latest_data_dir = find_latest_versioned_dir(db_file.parent)
    if not latest_data_dir:
        return

    # Check for same name first, fallback to default name
    old_db = latest_data_dir / db_file.name
    if not old_db.exists():
        old_db = latest_data_dir / "edupsyadmin.db"

    if old_db.exists():
        logger.info(f"Migrating database from {old_db} to {db_file}")
        # Create backup of the OLD database just in case,
        # but place it in the NEW location
        create_db_backup(old_db)
        shutil.copy2(old_db, db_file)
        # Move the backup to the new location too if it was created
        # in the old one
        old_backup = old_db.with_suffix(".db.bak")
        if old_backup.exists():
            shutil.move(old_backup, db_file.with_suffix(".db.bak"))


def migrate_to_stable_paths(config_file: Path, salt_file: Path, db_file: Path) -> None:
    """Migrate data from versioned subdirectories to stable paths."""
    _migrate_config(config_file)
    _migrate_salt(salt_file)
    _migrate_database(db_file)
