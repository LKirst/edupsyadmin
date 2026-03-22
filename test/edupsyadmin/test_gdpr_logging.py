import argparse
from unittest.mock import MagicMock, patch

import edupsyadmin.cli


def test_scrubbing_sensitive_args_in_logs():
    """Test that sensitive CLI arguments are scrubbed from logs."""

    # Mock dependencies to avoid side effects (DB, encryption, keyring, etc.)
    with (
        patch("edupsyadmin.cli.migrate_to_stable_paths"),
        patch("edupsyadmin.cli._handle_config_and_logging"),
        patch("edupsyadmin.cli._determine_app_username", return_value=0),
        patch("edupsyadmin.cli._determine_app_uid"),
        patch("edupsyadmin.cli._run_db_migrations", return_value=0),
        patch("edupsyadmin.cli._setup_app_encryption"),
        patch("edupsyadmin.cli.logger") as mock_logger,
    ):
        # Create a mock command that does nothing
        mock_command = MagicMock()

        # Mock _args to return a namespace with sensitive data
        mock_args = argparse.Namespace(
            command=mock_command,
            command_name="new-client",
            name="John Doe",
            csv="sensitive.csv",
            app_username="testuser",
            app_uid="testuid",
            database_url="sqlite:///test.db",
            config_path="config.yml",
            salt_path="salt.txt",
            warn=None,
        )

        with patch("edupsyadmin.cli._args", return_value=mock_args):
            # Run main. It will use our mocked _args and then log them.
            edupsyadmin.cli.main(
                ["new-client", "--name", "John Doe", "--csv", "sensitive.csv"]
            )

            # Find the call that contains the arguments
            debug_calls = [
                call.args[0] for call in mock_logger.debug.call_args_list if call.args
            ]
            arg_log = next(
                (s for s in debug_calls if "Commandline arguments:" in s), None
            )

            assert arg_log is not None
            assert "'name': '[SCRUBBED]'" in arg_log
            assert "'csv': '[SCRUBBED]'" in arg_log
            assert "John Doe" not in arg_log
            assert "sensitive.csv" not in arg_log

            # Non-sensitive keys should still be there
            assert "'command_name': 'new-client'" in arg_log
            assert "'app_username': 'testuser'" in arg_log

            # 'command' itself should be excluded from the log dict
            assert "'command':" not in arg_log


def test_scrubbing_set_client_args_in_logs():
    """Test that set-client sensitive arguments are scrubbed."""

    with (
        patch("edupsyadmin.cli.migrate_to_stable_paths"),
        patch("edupsyadmin.cli._handle_config_and_logging"),
        patch("edupsyadmin.cli._determine_app_username", return_value=0),
        patch("edupsyadmin.cli._determine_app_uid"),
        patch("edupsyadmin.cli._run_db_migrations", return_value=0),
        patch("edupsyadmin.cli._setup_app_encryption"),
        patch("edupsyadmin.cli.logger") as mock_logger,
    ):
        mock_command = MagicMock()
        mock_args = argparse.Namespace(
            command=mock_command,
            command_name="set-client",
            key_value_pairs=["nta_font=1", "first_name_encr=SensitiveName"],
            client_id=[1],
            app_username="testuser",
            app_uid="testuid",
            database_url="sqlite:///test.db",
            config_path="config.yml",
            salt_path="salt.txt",
            warn=None,
        )

        with patch("edupsyadmin.cli._args", return_value=mock_args):
            edupsyadmin.cli.main(["set-client", "1", "--key_value_pairs", "nta_font=1"])

            debug_calls = [
                call.args[0] for call in mock_logger.debug.call_args_list if call.args
            ]
            arg_log = next(
                (s for s in debug_calls if "Commandline arguments:" in s), None
            )

            assert arg_log is not None
            assert "'key_value_pairs': '[SCRUBBED]'" in arg_log
            assert "SensitiveName" not in arg_log
            assert "'client_id': [1]" in arg_log
