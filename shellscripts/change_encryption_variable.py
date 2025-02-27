import argparse
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from edupsyadmin.api.clients import Client
from edupsyadmin.core.encrypt import Encryption


def setup_encryption(username: str, user_data_dir: str, uid: str) -> Encryption:
    encryption = Encryption()
    encryption.set_fernet(username=username, user_data_dir=user_data_dir, uid=uid)
    return encryption


def update_column(
    session, encryption: Encryption, column_name: str, encrypt: bool
) -> None:
    clients = session.query(Client).all()
    for client in clients:
        if encrypt:
            # Encrypt the specified column
            original_value = getattr(client, column_name)
            if original_value is not None:
                encrypted_value = encryption.encrypt(original_value)
                setattr(client, f"{column_name}_encr", encrypted_value)
        else:
            # Decrypt the specified column
            encrypted_value = getattr(client, f"{column_name}_encr")
            if encrypted_value is not None:
                decrypted_value = encryption.decrypt(encrypted_value)
                # Replace empty strings with None (NULL in the database)
                setattr(
                    client, column_name, decrypted_value if decrypted_value else None
                )

        session.add(client)
    session.commit()


def main():
    parser = argparse.ArgumentParser(
        description="Encrypt or decrypt a column in the database."
    )
    parser.add_argument(
        "column_name", help="The name of the column to process (without _encr suffix)."
    )
    parser.add_argument("salt_file", help="Path to the salt file.")
    parser.add_argument("username", help="Username for encryption.")
    parser.add_argument("database_path", help="Path to the SQLite database file.")
    parser.add_argument("--encrypt", action="store_true", help="Encrypt the column.")
    parser.add_argument("--decrypt", action="store_true", help="Decrypt the column.")

    args = parser.parse_args()

    if args.encrypt == args.decrypt:
        parser.error("You must specify either --encrypt or --decrypt, but not both.")
    print(
        "Add the new column with `ALTER TABLE clients ADD COLUMN column_name VARCHAR;`"
    )
    print(
        "Both the old and the new column need to be attributes in the sqlalchemy model"
    )
    print("Drop the old column with `ALTER TABLE clients DROP COLUMN column_name;`")

    database_url = f"sqlite:///{os.path.abspath(args.database_path)}"
    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    session = Session()

    encryption = setup_encryption(
        args.username, args.salt_file, "liebermann-schulpsychologie.github.io"
    )

    update_column(session, encryption, args.column_name, args.encrypt)

    session.close()


if __name__ == "__main__":
    main()
