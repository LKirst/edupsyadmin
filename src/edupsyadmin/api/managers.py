import logging  # just for interaction with the sqlalchemy logger
import os
from datetime import datetime
from typing import Any

import pandas as pd
from sqlalchemy import create_engine, inspect, or_, select
from sqlalchemy.orm import sessionmaker

from edupsyadmin.core.config import config
from edupsyadmin.core.encrypt import encr
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
        app_uid: str,
        app_username: str,
        salt_path: str | os.PathLike[str],
    ):
        # set up logging for sqlalchemy
        logging.getLogger("sqlalchemy.engine").setLevel(config.core.logging)

        # connect to database
        logger.debug(f"trying to connect to database at {database_url}")
        self.database_url = database_url
        self.engine = create_engine(database_url)
        self.Session = sessionmaker(bind=self.engine)

        # set fernet for encryption
        encr.set_fernet(app_username, salt_path, app_uid)

        # create the table if it doesn't exist
        Base.metadata.create_all(self.engine, tables=[clients_db.Client.__table__])  # type: ignore[list-item]
        logger.debug(f"created connection to database at {database_url}")

    def add_client(self, **client_data: Any) -> int:
        logger.debug("trying to add client")
        with self.Session() as session:
            new_client = clients_db.Client(encr, **client_data)
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

    def get_clients_overview(self, nta_nos: bool = True) -> pd.DataFrame:
        logger.debug("trying to query client data for overview")

        # Build the query statement outside the session context.
        stmt = select(clients_db.Client)
        if nta_nos:
            stmt = stmt.where(
                or_(
                    clients_db.Client.notenschutz == 1,
                    clients_db.Client.nachteilsausgleich == 1,
                )
            )

        # Use the session only to execute the query.
        with self.Session() as session:
            clients = session.scalars(stmt).all()

        # Process the results after the session is closed.
        if not clients:
            return pd.DataFrame()

        data = [
            {
                "client_id": c.client_id,
                "school": c.school,
                "last_name_encr": c.last_name_encr,
                "first_name_encr": c.first_name_encr,
                "class_name": c.class_name,
                "notenschutz": c.notenschutz,
                "nachteilsausgleich": c.nachteilsausgleich,
                "lrst_diagnosis_encr": c.lrst_diagnosis_encr,
                "min_sessions": c.min_sessions,
                "keyword_taet_encr": c.keyword_taet_encr,
            }
            for c in clients
        ]

        return pd.DataFrame(data)

    def get_data_raw(self) -> pd.DataFrame:
        """
        Get the entire database.
        """
        logger.debug("trying to query the entire database")
        with self.Session() as session:
            query = session.query(clients_db.Client).statement
            return pd.read_sql_query(query, self.engine)

    def edit_client(self, client_ids: list[int], new_data: dict[str, Any]) -> None:
        logger.debug(f"editing clients (ids = {client_ids})")

        # Validate keys
        valid_keys = {c.key for c in inspect(clients_db.Client).column_attrs}
        invalid_keys = set(new_data.keys()) - valid_keys
        if invalid_keys:
            raise ValueError(f"Invalid keys found: {', '.join(invalid_keys)}")

        with self.Session() as session:
            clients = (
                session.query(clients_db.Client)
                .filter(clients_db.Client.client_id.in_(client_ids))
                .all()
            )

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
