import os
from pathlib import Path

import keyring
import yaml

from edupsyadmin.api.managers import ClientsManager
from edupsyadmin.core.config import config
from edupsyadmin.core.logger import logger


def setup_demo() -> None:
    """Create a sandboxed demo environment."""
    demo_config_path = "demo-config.yml"
    demo_salt_path = "demo-salt.txt"
    demo_db_url = "sqlite:///demo.db"
    demo_db_path = "demo.db"
    demo_username = "demouser"
    demo_app_uid = "liebermann-schulpsychologie.github.io"

    # remove old demo files to have a clean slate
    if os.path.exists(demo_db_path):
        os.remove(demo_db_path)
    if os.path.exists(demo_salt_path):
        os.remove(demo_salt_path)

    # Create demo-config.yml
    demo_config = {
        "core": {
            "logging": "INFO",
            "app_uid": demo_app_uid,
            "app_username": demo_username,
        },
        "schoolpsy": {
            "schoolpsy_name": "DemoVornameSP DemoNachnameSP",
            "schoolpsy_street": "Demostr. 1",
            "schoolpsy_city": "12345 Demostadt",
        },
        "school": {
            "DemoSchule": {
                "school_head_w_school": "Schulleitung der Demoschule",
                "school_name": "Staatliche Demoschule für Demozwecke",
                "school_street": "Demoweg 2",
                "school_city": "12345 Demostadt",
                "end": 12,
                "nstudents": 500,
            }
        },
        "form_set": {},
        "csv_import": {},
    }
    with open(demo_config_path, "w", encoding="utf-8") as f:
        yaml.dump(demo_config, f)

    # Load the new demo config
    config.load(demo_config_path)

    # Set a password for the demo user
    if not keyring.get_password(demo_app_uid, demo_username):
        keyring.set_password(
            config.core.app_uid, config.core.app_username, "edupsyadmin-demo-password"
        )
        logger.info("Password for demo user set in keyring.")
    else:
        logger.info("Demo user already exists in keyring. Using existing password.")

    # Instantiate ClientsManager to create demo.db and demo-salt.txt
    clients_manager = ClientsManager(
        database_url=demo_db_url,
        app_uid=config.core.app_uid,
        app_username=config.core.app_username,
        salt_path=demo_salt_path,
    )

    # Define and add sample data
    sample_clients = [
        {
            "school": "DemoSchule",
            "first_name_encr": "Max",
            "last_name_encr": "Mustermann",
            "gender_encr": "m",
            "birthday_encr": "2008-05-10",
            "class_name": "10a",
            "keyword_taet_encr": "slbb.slb.sonstige",
            "min_sessions": 90,
        },
        {
            "school": "DemoSchule",
            "first_name_encr": "Erika",
            "last_name_encr": "Musterfrau",
            "gender_encr": "f",
            "birthday_encr": "2009-02-15",
            "class_name": "9b",
            "nos_rs": True,
            "nta_zeitv_vieltext": 25,
            "keyword_taet_encr": "lrst.sp.ern",
            "lrst_diagnosis_encr": "lrst",
            "lrst_last_test_by_encr": "schpsy",
            "min_sessions": 240,
        },
        {
            "school": "DemoSchule",
            "first_name_encr": "John",
            "last_name_encr": "Doe",
            "gender_encr": "x",
            "birthday_encr": "2007-11-20",
            "class_name": "11c",
            "keyword_taet_encr": "ppb.inkl",
            "min_sessions": 45,
        },
    ]

    for client_data in sample_clients:
        clients_manager.add_client(**client_data)

    logger.info("Demo environment created successfully!")
    print("\nThe following files have been created in your current directory:")
    print(f"  - {demo_config_path}")
    print(f"  - {demo_salt_path}")
    print("  - demo.db")
    print("\nTo use the demo environment, run commands like this:")
    print(
        "  edupsyadmin --config_path demo-config.yml "
        "--salt_path demo-salt.txt --database_url sqlite:///demo.db tui"
    )

    # Generate alias suggestions
    abs_config_path = Path(demo_config_path).resolve()
    abs_salt_path = Path(demo_salt_path).resolve()
    abs_db_path = Path("demo.db").resolve()

    bash_alias = (
        f"alias edupsyadmin_demo='edupsyadmin "
        f'--config_path "{abs_config_path}" '
        f'--salt_path "{abs_salt_path}" '
        f'--database_url "sqlite:///{abs_db_path}"\''
    )
    # A function is more common in PowerShell profiles and robustly passes arguments
    powershell_function = (
        f"function edupsyadmin_demo {{ "
        f'edupsyadmin --config_path \\"{abs_config_path}\\" '
        f'--salt_path \\"{abs_salt_path}\\" '
        f'--database_url \\"sqlite:///{abs_db_path}\\" $args '
        f"}}"
    )

    print("\nTo quickly use the demo environment, consider setting up a shortcut:")
    print("\n  For Bash/Zsh, add this alias to your .bashrc or .zshrc:")
    print(f"    {bash_alias}")
    print("    # Then, you can run: edupsyadmin_demo tui")
    print("\n  For PowerShell, add this function to your profile:")
    print(f"    {powershell_function}")
    print("    # Then, you can run: edupsyadmin_demo tui")
