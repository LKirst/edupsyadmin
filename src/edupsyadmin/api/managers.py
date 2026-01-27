import logging  # just for interaction with the sqlalchemy logger
from datetime import datetime
from typing import Any

import pandas as pd
from sqlalchemy import create_engine, inspect, or_, select
from sqlalchemy.orm import sessionmaker

from edupsyadmin.core.config import config
from edupsyadmin.core.logger import logger
from edupsyadmin.db import Base
from edupsyadmin.db import clients as clients_db


class ClientNotFoundError(Exception):
    def __init__(self, client_id: int):
        self.client_id = client_id
        super().__init__(f"Client with ID {client_id} not found.")


class ClientsManager:
    def __init__(
        self,
        database_url: str,
    ):
        # set up logging for sqlalchemy
        logging.getLogger("sqlalchemy.engine").setLevel(config.core.logging)

        # connect to database
        logger.debug(f"trying to connect to database at {database_url}")
        self.database_url = database_url
        self.engine = create_engine(database_url)
        self.Session = sessionmaker(bind=self.engine)

        # create the table if it doesn't exist
        Base.metadata.create_all(self.engine, tables=[clients_db.Client.__table__])  # type: ignore[list-item]
        logger.debug(f"created connection to database at {database_url}")

    def add_client(self, **client_data: Any) -> int:
        logger.debug("trying to add client")
        with self.Session() as session:
            new_client = clients_db.Client(**client_data)
            session.add(new_client)
            session.commit()
            logger.info(f"added client: {new_client}")
            return new_client.client_id

    def get_decrypted_client(self, client_id: int) -> dict[str, Any]:
        logger.debug(f"trying to access client (client_id = {client_id})")
        with self.Session() as session:
            client = session.get(clients_db.Client, client_id)
            if client is None:
                raise ClientNotFoundError(client_id)
            # Create a clean dictionary using the ORM mapper
            mapper = inspect(client.__class__)
            return {c.key: getattr(client, c.key) for c in mapper.column_attrs}

    def get_clients_overview(
        self,
        nta_nos: bool = False,
        schools: list[str] | None = None,
        columns: list[str] | None = None,
    ) -> pd.DataFrame:
        logger.debug("trying to query client data for overview")

        # Always-present base columns
        required_columns = [
            "client_id",
            "school",
            "last_name_encr",
            "first_name_encr",
            "class_name",
        ]

        # Defaults for extra columns when none provided
        default_extras = [
            "notenschutz",
            "nachteilsausgleich",
            "min_sessions",
            "lrst_diagnosis_encr",
            "keyword_taet_encr",
        ]

        # Map ORM/DB keys to column expressions
        mapper = inspect(clients_db.Client)
        colmap = {
            col.key: getattr(clients_db.Client, col.key) for col in mapper.columns
        }

        extras = default_extras if columns is None else columns

        # Validate extras against available columns
        invalid = set(extras) - set(colmap.keys())
        if invalid:
            allowed = ", ".join(sorted(colmap.keys()))
            raise ValueError(
                f"Invalid column names: {', '.join(sorted(invalid))}. "
                f"Allowed: {allowed}"
            )

        # Merge required + extras, de-duplicate while preserving order
        final_columns = list(dict.fromkeys(required_columns + extras))

        # Build SELECT
        selected_cols = [colmap[name].label(name) for name in final_columns]
        stmt = select(*selected_cols)

        # Optional filters
        conditions = []
        if nta_nos:
            conditions.append(
                or_(
                    clients_db.Client.notenschutz.is_(True),
                    clients_db.Client.nachteilsausgleich.is_(True),
                )
            )
        if schools:
            conditions.append(clients_db.Client.school.in_(schools))
        if conditions:
            stmt = stmt.where(*conditions)

        with self.Session() as session:
            result = session.execute(stmt, execution_options={"yield_per": 100})
            return pd.DataFrame(result.fetchall(), columns=list(result.keys()))

    def get_data_raw(self) -> pd.DataFrame:
        """
        Get the entire database.
        """
        logger.debug("trying to query the entire database")
        stmt = select(clients_db.Client)
        return pd.read_sql_query(stmt, self.engine)

    def edit_client(self, client_ids: list[int], new_data: dict[str, Any]) -> None:
        logger.debug(f"editing clients (ids = {client_ids})")

        # Validate keys
        valid_keys = {c.key for c in inspect(clients_db.Client).column_attrs}
        invalid_keys = set(new_data.keys()) - valid_keys
        if invalid_keys:
            raise ValueError(f"Invalid keys found: {', '.join(invalid_keys)}")

        with self.Session() as session:
            stmt = select(clients_db.Client).where(
                clients_db.Client.client_id.in_(client_ids)
            )
            clients = session.scalars(stmt).all()

            found_ids = {client.client_id for client in clients}
            not_found_ids = set(client_ids) - found_ids

            if not_found_ids:
                logger.warning(
                    f"clients with following ids could not be found: {not_found_ids}"
                )

            for client in clients:
                for key, value in new_data.items():
                    logger.debug(
                        f"changing value for key: {key} for client: {client.client_id}"
                    )
                    setattr(client, key, value)
                client.datetime_lastmodified = datetime.now()

            session.commit()

    def delete_client(self, client_id: int) -> None:
        logger.debug("deleting client")
        with self.Session() as session:
            client = session.get(clients_db.Client, client_id)
            if client:
                session.delete(client)
                session.commit()
