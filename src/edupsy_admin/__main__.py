""" Main application entry point.

    python -m edupsy_admin  ...

"""
from edupsy_admin.core import create_tbl_names
from edupsy_admin.core import utils_sql


def main():
    """Execute the application."""
    clients = create_tbl_names.Clients(utils_sql.DB_PATH)
    print("I have not implemented the app yet! This is where my code should go.")


# Make the script executable.

if __name__ == "__main__":
    raise SystemExit(main())
