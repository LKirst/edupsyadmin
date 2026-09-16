import inspect as py_inspect
import logging  # just for interaction with the sqlalchemy logger
from typing import Any

from sqlalchemy import create_engine, func, inspect, or_, select
from sqlalchemy.orm import sessionmaker

from edupsyadmin.api.client_view import ClientView
from edupsyadmin.api.exceptions import ClientNotFoundError
from edupsyadmin.api.types import ClientRecord
from edupsyadmin.core.config import config
from edupsyadmin.core.logger import logger
from edupsyadmin.db import clients as clients_db


class ClientsManager:
    def __init__(
        self,
        database_url: str,
    ) -> None:
        # set up logging for sqlalchemy
        logging.getLogger("sqlalchemy.engine").setLevel(config.core.logging)

        # connect to database
        logger.debug(f"trying to connect to database at {database_url}")
        self.database_url = database_url
        self.engine = create_engine(database_url, echo=False)
        self.Session = sessionmaker(bind=self.engine)

        # Cache mapper and column metadata
        self._mapper = inspect(clients_db.Client)
        self._colmap = {
            col.key: getattr(clients_db.Client, col.key) for col in self._mapper.columns
        }
        self._valid_keys = {c.key for c in self._mapper.column_attrs}

        logger.debug(f"created connection to database at {database_url}")

    def add_client(self, **client_data: Any) -> int:
        logger.debug("trying to add client")
        with self.Session() as session:
            with session.begin():
                new_client = clients_db.Client(**client_data)
                session.add(new_client)
            # Accessing client_id after commit (end of begin block)
            logger.info(f"added client: {new_client}")
            return new_client.client_id

    def get_decrypted_client(self, client_id: int) -> ClientRecord:
        logger.debug(f"trying to access client (client_id = {client_id})")
        with self.Session() as session:
            client = session.get(clients_db.Client, client_id)
            if client is None:
                raise ClientNotFoundError(client_id)
            return ClientRecord.model_validate(client)

    def get_client_view(self, client_id: int) -> ClientView:
        """Get a ClientView for the given client_id."""
        logger.debug(f"trying to access client view (client_id = {client_id})")
        with self.Session() as session:
            client = session.get(clients_db.Client, client_id)
            if client is None:
                raise ClientNotFoundError(client_id)
            return ClientView.model_validate(client)

    def get_clients_overview(
        self,
        nta_nos: bool = False,
        schools: list[str] | None = None,
        columns: list[str] | str | None = None,
        academic_years: list[str] | str | None = None,
    ) -> list[dict[str, Any]]:
        logger.debug("trying to query client data for overview")

        # Always-present base columns
        required_columns = [
            "client_id",
            "case_active",
            "school",
            "last_name_encr",
            "first_name_encr",
            "class_name_encr",
            "record_academic_year",
        ]

        if columns in ("all", ["all"]):
            final_columns = list(self._colmap.keys())
        else:
            # Defaults for extra columns when none provided
            default_extras = [
                "notenschutz",
                "nachteilsausgleich",
                "min_sessions",
                "lrst_diagnosis_encr",
                "keyword_taet_encr",
            ]

            if columns is None or (isinstance(columns, list) and not columns):
                extras = default_extras
            elif isinstance(columns, str):
                extras = [columns]
            else:
                extras = columns

            # Validate extras against available columns
            invalid = set(extras) - set(self._colmap.keys())
            if invalid:
                allowed = ", ".join(sorted(self._colmap.keys()))
                raise ValueError(
                    f"Invalid column names: {', '.join(sorted(invalid))}. "
                    f"Allowed: {allowed}",
                )

            # Merge required + extras, de-duplicate while preserving order
            final_columns = list(dict.fromkeys(required_columns + extras))

        # Build SELECT
        selected_cols = [self._colmap[name].label(name) for name in final_columns]
        stmt = select(*selected_cols)

        # Optional filters
        conditions = []
        if nta_nos:
            conditions.append(
                or_(
                    clients_db.Client.notenschutz.is_(True),
                    clients_db.Client.nachteilsausgleich.is_(True),
                ),
            )
        if schools:
            conditions.append(clients_db.Client.school.in_(schools))
        if academic_years and academic_years not in ("all", ["all"]):
            if isinstance(academic_years, str):
                academic_years = [academic_years]
            conditions.append(
                clients_db.Client.record_academic_year.in_(academic_years)
            )
        if conditions:
            stmt = stmt.where(*conditions)

        with self.Session() as session:
            result = session.execute(stmt, execution_options={"yield_per": 100})
            return [dict(row) for row in result.mappings()]

    def copy_client(
        self,
        client_id: int,
        target_academic_year: str,
        reset_sessions: bool = True,
    ) -> int:
        """Copy a client record to a specified academic year.

        :param client_id: The ID of the client to copy.
        :param target_academic_year: The target academic year (e.g. '2026/27').
        :param reset_sessions: Whether to reset min_sessions and n_sessions to 0.
        :return: The client_id of the newly created client copy.
        """
        logger.debug(
            f"trying to copy client {client_id} "
            f"to academic year {target_academic_year}",
        )
        with self.Session() as session:
            client = session.get(clients_db.Client, client_id)
            if client is None:
                raise ClientNotFoundError(client_id)

            init_params = set(
                py_inspect.signature(clients_db.Client.__init__).parameters.keys(),
            )
            data: dict[str, Any] = {
                k: getattr(client, k)
                for k in init_params
                if k not in ("self", "client_id") and hasattr(client, k)
            }
            data["record_academic_year"] = target_academic_year
            if reset_sessions:
                data["min_sessions"] = 0
                data["n_sessions"] = 0

            new_client = clients_db.Client(**data)
            session.add(new_client)
            session.commit()

            logger.info(
                f"copied client {client_id} to {new_client.client_id} "
                f"for academic year {target_academic_year}",
            )
            return new_client.client_id

    def edit_client(self, client_ids: list[int], new_data: dict[str, Any]) -> None:
        logger.debug(f"editing clients (ids = {client_ids})")

        # Validate keys
        invalid_keys = set(new_data.keys()) - self._valid_keys
        if invalid_keys:
            raise ValueError(f"Invalid keys found: {', '.join(invalid_keys)}")

        with self.Session() as session, session.begin():
            stmt = select(clients_db.Client).where(
                clients_db.Client.client_id.in_(client_ids),
            )
            clients = session.scalars(stmt).all()

            found_ids = {client.client_id for client in clients}
            not_found_ids = set(client_ids) - found_ids

            if not_found_ids:
                logger.warning(
                    f"clients with following ids could not be found: {not_found_ids}",
                )

            for client in clients:
                for key, value in new_data.items():
                    logger.debug(
                        f"changing value for key: {key} for client: {client.client_id}",
                    )
                    setattr(client, key, value)

    def delete_client(self, client_id: int) -> None:
        logger.debug(f"deleting client {client_id}")
        with self.Session() as session, session.begin():
            client = session.get(clients_db.Client, client_id)
            if not client:
                raise ClientNotFoundError(client_id)
            session.delete(client)

    def get_total_count(self) -> int:
        """Get the total number of clients in the database."""
        logger.debug("querying total client count from database")
        with self.Session() as session:
            return (
                session.scalar(select(func.count()).select_from(clients_db.Client)) or 0
            )
