import asyncio
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
import yaml
from conftest import TEST_UID, TEST_USERNAME
from cryptography.fernet import Fernet

from edupsyadmin.api.migration import upgrade_db
from edupsyadmin.core.config import AppConfig
from edupsyadmin.core.encrypt import set_keys_in_keyring
from edupsyadmin.tui.editconfig_app import ConfigEditorApp, save_config

if TYPE_CHECKING:
    from pytest_benchmark.fixture import BenchmarkFixture

# Note: It doesn't make sense to test keyring retrieval here because
# I use a mock keyring


@pytest.fixture
def db_url(tmp_path: Path) -> str:
    """Create and migrate a fresh SQLite database, returning its URL."""
    db_path = tmp_path / "benchmark.db"
    url = f"sqlite:///{db_path}"
    upgrade_db(url)
    return url


def test_benchmark_save_config_yaml_dump(
    benchmark: BenchmarkFixture,
    mock_config: Path,
    tmp_path: Path,
) -> None:
    """Benchmark saving configuration to YAML disk storage."""
    with mock_config.open("r", encoding="utf-8") as f:
        config_data = yaml.safe_load(f)

    out_file = tmp_path / "out_benchmark.yml"

    def run_save() -> None:
        save_config(config_data, out_file)

    benchmark(run_save)


def test_benchmark_pydantic_model_validate(
    benchmark: BenchmarkFixture,
    mock_config: Path,
) -> None:
    """Benchmark Pydantic model validation of the full config dict."""
    with mock_config.open("r", encoding="utf-8") as f:
        config_data = yaml.safe_load(f)

    def run_model_validate() -> None:
        AppConfig.model_validate(config_data)

    benchmark(run_model_validate)


def test_benchmark_rebuild_config_from_ui(
    benchmark: BenchmarkFixture,
    mock_config: Path,
    db_url: str,
) -> None:
    """Benchmark DOM querying and dictionary extraction in _rebuild_config_from_ui."""

    async def setup_app() -> ConfigEditorApp:
        return ConfigEditorApp(
            mock_config, TEST_UID, TEST_USERNAME, database_url=db_url
        )

    app = asyncio.run(setup_app())

    async def run_in_pilot() -> None:
        async with app.run_test():

            def run_rebuild() -> None:
                app._rebuild_config_from_ui()

            benchmark(run_rebuild)

    asyncio.run(run_in_pilot())


def test_benchmark_validate_inputs_for_save(
    benchmark: BenchmarkFixture,
    mock_config: Path,
    db_url: str,
) -> None:
    """Benchmark full UI validation (_validate_inputs_for_save)."""

    async def run_in_pilot() -> None:
        app = ConfigEditorApp(mock_config, TEST_UID, TEST_USERNAME, database_url=db_url)
        async with app.run_test():

            def run_validate() -> None:
                app._validate_inputs_for_save()

            benchmark(run_validate)

    asyncio.run(run_in_pilot())


def test_benchmark_full_save_tui_flow_existing_keys(
    benchmark: BenchmarkFixture,
    mock_config: Path,
    db_url: str,
) -> None:
    """Benchmark the full TUI save flow when existing keys are in keyring."""
    with mock_config.open("r", encoding="utf-8") as f:
        conf_data = yaml.safe_load(f)
    uid = conf_data.get("core", {}).get("app_uid") or TEST_UID
    username = conf_data.get("core", {}).get("app_username") or TEST_USERNAME
    set_keys_in_keyring(uid, username, [Fernet.generate_key()])

    async def execute_save() -> None:
        app = ConfigEditorApp(mock_config, TEST_UID, TEST_USERNAME, database_url=db_url)
        async with app.run_test() as pilot:
            await pilot.click("#save")
            for _ in range(100):
                if not app._running:
                    break
                await asyncio.sleep(0.01)

    def run() -> None:
        asyncio.run(execute_save())

    benchmark.pedantic(run, rounds=5, iterations=1)
