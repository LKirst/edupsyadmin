from datetime import date, datetime

from sqlalchemy import (
    String,
)
from sqlalchemy.types import TypeDecorator

from edupsyadmin.core.encrypt import encr
from edupsyadmin.core.logger import logger


class EncryptedString(TypeDecorator):
    """Stores base-65 ciphertext in a TEXT/VARCHAR column;
    Presents plain str values to the application."""

    impl = String
    cache_ok = True

    @property
    def python_type(self) -> type:
        return str

    def process_bind_param(
        self,
        value: str | None,
        dialect,  # noqa: ARG002
    ) -> str | None:
        return encr.encrypt(value or "")

    def process_result_value(
        self,
        value: str | None,
        dialect,  # noqa: ARG002
    ) -> str | None:
        """
        Note to self: This should never receive value=None!
        I just handle it here to silence the type checker.
        """
        if value is None:
            return None
        return encr.decrypt(value)


class EncryptedInteger(TypeDecorator):
    """Stores base-64 ciphertext in a TEXT column;
    Presents plain int values to the application."""

    impl = String
    cache_ok = True

    @property
    def python_type(self) -> type:
        return int

    def process_bind_param(
        self,
        value: int | None,
        dialect,  # noqa: ARG002
    ) -> str | None:
        if value is None:
            return encr.encrypt("")
        return encr.encrypt(str(value))

    def process_result_value(
        self,
        value: str | None,
        dialect,  # noqa: ARG002
    ) -> int | None:
        if value is None:
            return None
        decrypted = encr.decrypt(value)
        try:
            return int(decrypted) if decrypted else None
        except ValueError, TypeError:
            logger.error(f"Could not convert decrypted value '{decrypted}' to int")
            return None


class EncryptedDate(TypeDecorator):
    """Stores base-64 ciphertext in a TEXT column;
    Presents plain date objects to the application."""

    impl = String
    cache_ok = True

    @property
    def python_type(self) -> type:
        return date

    def process_bind_param(
        self,
        value: date | None,
        dialect,  # noqa: ARG002
    ) -> str | None:
        if value is None:
            return encr.encrypt("")
        return encr.encrypt(value.isoformat())

    def process_result_value(
        self,
        value: str | None,
        dialect,  # noqa: ARG002
    ) -> date | None:
        if value is None:
            return None
        decrypted = encr.decrypt(value)
        if not decrypted:
            return None
        try:
            return datetime.strptime(decrypted, "%Y-%m-%d").date()
        except ValueError, TypeError:
            logger.error(f"Could not convert decrypted value '{decrypted}' to date")
            return None
