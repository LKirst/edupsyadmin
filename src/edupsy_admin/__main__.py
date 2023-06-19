""" Main application entry point.

    python -m edupsy_admin  ...

"""
from .api import Clients, utils_sql


def main():
    """Execute the application."""
    clients = Clients(utils_sql.DB_PATH)
    print("I have not implemented the app yet!")


# Make the script executable.

if __name__ == "__main__":
    raise SystemExit(main())
