"""Custom exceptions for the edupsyadmin API."""


class ClientNotFoundError(Exception):
    """Raised when a client is not found in the database."""

    def __init__(self, client_id: int) -> None:
        self.client_id = client_id
        super().__init__(f"Client with ID {client_id} not found.")


class MigrationError(Exception):
    """Raised when migration encounters an error."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message
