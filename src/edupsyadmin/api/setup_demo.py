import yaml

from edupsyadmin.api.managers import ClientsManager
from edupsyadmin.core.config import config
from edupsyadmin.core.logger import logger


def setup_demo() -> None:
    """Create a sandboxed demo environment."""
    demo_config_path = "demo-config.yml"
    demo_salt_path = "demo-salt.txt"
    demo_db_url = "sqlite:///demo.db"

    # Create demo-config.yml
    demo_config = {
        "core": {
            "logging": "INFO",
            "app_uid": "liebermann-schulpsychologie.github.io",
            "app_username": "demouser",
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
