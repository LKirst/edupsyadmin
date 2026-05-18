import types
from typing import Union, get_args, get_origin, get_type_hints

from sqlalchemy import inspect

from edupsyadmin.api.types import ClientRecord
from edupsyadmin.db.clients import Client
from edupsyadmin.utils.python_type import get_python_type


def test_client_record_pydantic_synced_with_client_orm_model() -> None:
    """
    Ensures that every field defined in the Client ORM model exists in the
    ClientRecord Pydantic model and has a compatible type.
    """
    mapper = inspect(Client)
    orm_columns = mapper.columns

    # get_type_hints resolves types
    typed_dict_hints = get_type_hints(ClientRecord)

    missing_in_pydantic = []
    type_mismatches = []

    for column in orm_columns:
        field_name = column.key
        if field_name not in typed_dict_hints:
            missing_in_pydantic.append(field_name)
            continue

        expected_python_type = get_python_type(column.type)
        actual_hint = typed_dict_hints[field_name]

        # Extract base types from the hint (e.g., str | None -> [str, NoneType])
        origin = get_origin(actual_hint)
        if origin is Union or origin is types.UnionType:
            actual_types = get_args(actual_hint)
        else:
            actual_types = (actual_hint,)

        # Check if the expected python type is among the actual types
        if expected_python_type not in actual_types:
            type_mismatches.append(
                f"Field '{field_name}': ORM expects "
                f"{expected_python_type.__name__}, Pydantic has {actual_hint}"
            )

        # Check nullability
        if column.nullable and type(None) not in actual_types:
            type_mismatches.append(
                f"Field '{field_name}': ORM is nullable, "
                f"but Pydantic doesn't allow None"
            )

    assert not missing_in_pydantic, (
        f"The following fields from the Client ORM model are missing in "
        f"ClientRecord Pydantic model: {sorted(missing_in_pydantic)}. "
        "Please add them to src/edupsyadmin/api/types.py."
    )

    assert not type_mismatches, (
        "Type mismatches found between Client model and ClientRecord:\n"
        + "\n".join(type_mismatches)
    )
