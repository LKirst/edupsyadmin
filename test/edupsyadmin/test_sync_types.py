import ast
import types
from pathlib import Path
from typing import Union, get_args, get_origin, get_type_hints

from sqlalchemy import inspect

from edupsyadmin.api.types import ClientData
from edupsyadmin.db.clients import Client
from edupsyadmin.utils.python_type import get_python_type


def test_client_data_typeddict_synced_with_client_orm_model() -> None:
    """
    Ensures that every field defined in the Client ORM model exists in the
    ClientData TypedDict and has a compatible type.
    """
    mapper = inspect(Client)
    orm_columns = mapper.columns

    # get_type_hints resolves types and handles Required/NotRequired
    # by returning the inner type
    typed_dict_hints = get_type_hints(ClientData)

    missing_in_typeddict = []
    type_mismatches = []

    for column in orm_columns:
        field_name = column.key
        if field_name not in typed_dict_hints:
            missing_in_typeddict.append(field_name)
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
                f"{expected_python_type.__name__}, TypedDict has {actual_hint}"
            )

        # Check nullability
        if column.nullable and type(None) not in actual_types:
            type_mismatches.append(
                f"Field '{field_name}': ORM is nullable, "
                f"but TypedDict doesn't allow None"
            )

    assert not missing_in_typeddict, (
        f"The following fields from the Client ORM model are missing in "
        f"ClientData TypedDict: {sorted(missing_in_typeddict)}. "
        "Please add them to src/edupsyadmin/api/types.py."
    )

    assert not type_mismatches, (
        "Type mismatches found between Client ORM model and ClientData TypedDict:\n"
        + "\n".join(type_mismatches)
    )


def _extract_assigned_keys(node: ast.AST) -> set[str]:
    """Helper to extract keys assigned to the 'data' dict or via dates_to_convert."""
    keys = set()
    # Look for data["key"] = ...
    if (
        isinstance(node, ast.Assign)
        and isinstance(node.targets[0], ast.Subscript)
        and isinstance(node.targets[0].value, ast.Name)
        and node.targets[0].value.id == "data"
    ):
        slc = node.targets[0].slice
        if isinstance(slc, ast.Constant):
            keys.add(slc.value)

    # Look for gdate in dates_to_convert list (Assign or AnnAssign)
    is_dates_conv = False
    val = None
    if (
        isinstance(node, ast.Assign)
        and any(
            isinstance(t, ast.Name) and t.id == "dates_to_convert" for t in node.targets
        )
    ) or (
        isinstance(node, ast.AnnAssign)
        and isinstance(node.target, ast.Name)
        and node.target.id == "dates_to_convert"
    ):
        is_dates_conv = True
        val = node.value

    if is_dates_conv and isinstance(val, ast.List):
        for elt in val.elts:
            if (
                isinstance(elt, ast.Tuple)
                and len(elt.elts) == 2
                and isinstance(elt.elts[1], ast.Constant)
            ):
                keys.add(elt.elts[1].value)
    return keys


def test_client_data_typeddict_synced_with_convenience_data() -> None:
    """
    Statically analyzes add_convenience_data.py to ensure all keys assigned
    to the data dict are present in ClientData TypedDict.
    """
    api_dir = Path(__file__).parent.parent.parent / "src" / "edupsyadmin" / "api"
    conv_file = api_dir / "add_convenience_data.py"

    tree = ast.parse(conv_file.read_text())

    assigned_keys = set()
    for node in ast.walk(tree):
        assigned_keys.update(_extract_assigned_keys(node))

    typed_dict_hints = get_type_hints(ClientData)
    missing_in_typeddict = assigned_keys - set(typed_dict_hints.keys())

    assert not missing_in_typeddict, (
        f"The following keys are assigned in add_convenience_data.py but "
        f"are missing in ClientData TypedDict: {sorted(missing_in_typeddict)}"
    )

    # Check for fields in TypedDict that aren't in ORM and aren't assigned
    mapper = inspect(Client)
    orm_fields = {column.key for column in mapper.columns}
    convenience_fields_in_td = set(typed_dict_hints.keys()) - orm_fields

    extra_in_typeddict = convenience_fields_in_td - assigned_keys
    assert not extra_in_typeddict, (
        f"The following fields in ClientData TypedDict are neither in the "
        f"ORM model nor assigned in add_convenience_data.py: "
        f"{sorted(extra_in_typeddict)}"
    )
