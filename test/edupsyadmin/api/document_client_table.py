from sqlalchemy.inspection import inspect
from sqlalchemy.sql.schema import CheckConstraint

from edupsyadmin.api.clients import Client


def generate_markdown_table(model) -> str:
    """
    Generate a Markdown table containing field names, types, constraints, and
    default values from a SQLAlchemy model.

    :param model: The SQLAlchemy model class.
    :return: A string formatted as a Markdown table.
    """
    mapper = inspect(model)
    columns = mapper.columns

    # create markdown table
    markdown = "| Field Name | Type | Constraints | Default Value |\n"
    markdown += "|------------|------|-------------|---------------|\n"
    for column in columns:
        field_name = column.name
        field_type = str(column.type)
        constraints = []
        default_value = column.default
        if column.primary_key:
            constraints.append("Primary Key")
        if column.nullable is False:
            constraints.append("Not Null")
        if default_value is not None:
            if isinstance(default_value, str):
                constraints.append(f"Default: {default_value}")
            else:
                constraints.append(f"Default: {default_value.arg}")
        if column.constraints:
            for constraint in column.constraints:
                if isinstance(constraint, CheckConstraint):
                    constraints.append(f"Check: {constraint.sqltext}")

        constraints_str = ", ".join(constraints) if constraints else "None"
        markdown += (
            f"| {field_name} | {field_type} | "
            f"{constraints_str} | "
            f"{default_value if default_value else 'None'} |\n"
        )

    return markdown


def write_markdown_file(content: str, file_path: str) -> None:
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)


if __name__ == "__main__":
    markdown_content = generate_markdown_table(Client)
    write_markdown_file(markdown_content, "client_model_documentation.md")
