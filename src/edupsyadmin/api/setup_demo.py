import importlib.resources
from pathlib import Path

import yaml

from edupsyadmin.api.managers import ClientsManager
from edupsyadmin.core.config import config
from edupsyadmin.core.encrypt import (
    DEFAULT_KDF_ITERATIONS,
    derive_key_from_password,
    encr,
    get_keys_from_keyring,
    load_or_create_salt,
    set_keys_in_keyring,
)
from edupsyadmin.core.logger import logger


def setup_demo() -> None:
    """Create a sandboxed demo environment."""
    demo_config_path = Path("demo-config.yml")
    demo_salt_path = Path("demo-salt.txt")
    demo_db_url = "sqlite:///demo.db"
    demo_db_path = Path("demo.db")
    demo_username = "demouser"
    demo_app_uid = "liebermann-schulpsychologie.github.io.demo"

    # remove old demo files to have a clean slate
    demo_db_path.unlink(missing_ok=True)
    demo_salt_path.unlink(missing_ok=True)

    # Load default config and customize for demo
    template_path = importlib.resources.files("edupsyadmin.data") / "sampleconfig.yml"
    with template_path.open("r", encoding="utf-8") as f:
        demo_config = yaml.safe_load(f)

    # Customize for demo
    demo_config["core"]["app_uid"] = demo_app_uid
    demo_config["core"]["app_username"] = demo_username

    with demo_config_path.open("w", encoding="utf-8") as f:
        yaml.dump(demo_config, f)

    # Load the new demo config
    config.load(demo_config_path)

    # Define demo password
    demo_password = "edupsyadmin-demo-password"

    # Set an encryption key for the demo user
    # Check if a key already exists
    keys = get_keys_from_keyring(config.core.app_uid, config.core.app_username)
    if not keys:
        logger.info("No encryption key found for demo user. Generating a new one.")
        # Load or create salt for key derivation
        salt = load_or_create_salt(demo_salt_path)
        # Derive key from password and salt
        key = derive_key_from_password(demo_password, salt, DEFAULT_KDF_ITERATIONS)
        # Store the derived key in the keyring as a list
        set_keys_in_keyring(config.core.app_uid, config.core.app_username, [key])
        logger.info("Encryption key for demo user set in keyring.")
        keys = [key]  # Update keys variable for subsequent use
    else:
        logger.info(
            "Demo user already has an encryption key in keyring. Using existing key."
        )

    # Initialize encryption for this session
    if not keys:
        raise RuntimeError("Failed to get demo key from keyring after setting it.")
    encr.set_keys(keys)
    logger.info("Encryption initialized for demo session.")

    # Instantiate ClientsManager to create demo.db and demo-salt.txt
    clients_manager = ClientsManager(database_url=demo_db_url)

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
