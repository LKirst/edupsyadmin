from sqlalchemy import text


def test_get_all_clients_df_returns_decrypted_data(
    clients_manager, client_dict_set_by_user
):
    """
    Verifies that get_all_clients_df() returns decrypted plaintext,
    not encrypted ciphertext.
    """
    # 1. Add a client using the manager
    client_id = clients_manager.add_client(**client_dict_set_by_user)

    # 2. Retrieve data via get_all_clients_df()
    df = clients_manager.get_all_clients_df()

    # 3. Check if the value in the DataFrame is decrypted
    # We use .iloc[0] because we only added one client to the fresh test DB
    retrieved_name = df.loc[df["client_id"] == client_id, "first_name_encr"].iloc[0]
    expected_name = client_dict_set_by_user["first_name_encr"]

    assert retrieved_name == expected_name, (
        f"Expected decrypted name '{expected_name}', but got '{retrieved_name}'"
    )

    # 4. Double check against the ACTUAL raw database content
    # (which should be encrypted)
    with clients_manager.engine.connect() as conn:
        # We use a raw SQL string to bypass SQLAlchemy's TypeDecorators
        stmt = text("SELECT first_name_encr FROM clients WHERE client_id = :client_id")
        result = conn.execute(stmt, {"client_id": client_id}).fetchone()
        actual_raw_ciphertext = result[0]

        assert actual_raw_ciphertext != expected_name, (
            "The raw database value should be encrypted ciphertext"
        )
        assert isinstance(actual_raw_ciphertext, str)
        # Fernet tokens usually start with 'gAAAAA'
        assert actual_raw_ciphertext.startswith("gAAAA")
