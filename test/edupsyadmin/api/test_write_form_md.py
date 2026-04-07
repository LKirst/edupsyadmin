import textwrap
import unittest.mock as mock
from pathlib import Path

import pytest
from liquid.exceptions import LiquidError
from liquid.template import BoundTemplate

from edupsyadmin.api.add_convenience_data import add_convenience_data
from edupsyadmin.api.fill_form import fill_form, write_form_md
from edupsyadmin.api.types import ClientData


def test_write_form_md_success(
    tmp_path: Path, client_dict_internal: ClientData
) -> None:
    """Test successful rendering of a liquid template."""
    template_path = tmp_path / "template.md"
    output_path = tmp_path / "output.md"

    template_content = "Hello {{ first_name_encr }} {{ last_name_encr }}!"
    template_path.write_text(template_content, encoding="utf8")

    write_form_md(template_path, output_path, client_dict_internal)

    assert output_path.exists()
    fname = client_dict_internal["first_name_encr"]
    lname = client_dict_internal["last_name_encr"]
    expected_content = f"Hello {fname} {lname}!"
    assert output_path.read_text(encoding="utf8") == expected_content


def test_fill_form_md_integration(
    tmp_path: Path, client_dict_internal: ClientData, mock_config
) -> None:
    """End-to-end test for fill_form with a multiline markdown template."""
    # Prepare data with convenience fields
    client_data = add_convenience_data(client_dict_internal)

    # Create a multiline template
    template_path = tmp_path / "report.md"
    template_content = textwrap.dedent(
        """\
        # Report for {{ name }}

        - Date: {{ today_date_de }}
        - School: {{ school_name }}

        ## Details

        - Birthday: {{ birthday_de }}
        - Address: {{ addr_s_nname }}

        {% if notenschutz %}
        Notenschutz is active.
        {% endif %}
        """
    )
    template_path.write_text(template_content, encoding="utf8")
    print(f"markdown template: {template_path}")  # run with -s to see output

    # Call fill_form which calls write_form_md internally
    fill_form(client_data, [template_path], out_dir=tmp_path)

    # Verify output
    expected_output_path = tmp_path / f"{client_data['client_id']}_{template_path.name}"
    assert expected_output_path.exists()

    print(f"markdown output: {expected_output_path}")  # run with -s to see output

    output_text = expected_output_path.read_text(encoding="utf8")
    assert f"# Report for {client_data['name']}" in output_text
    assert f"Date: {client_data['today_date_de']}" in output_text
    assert f"School: {client_data['school_name']}" in output_text
    assert f"- Birthday: {client_data['birthday_de']}" in output_text
    assert f"- Address: {client_data['addr_s_nname']}" in output_text

    if client_data["notenschutz"]:
        assert "Notenschutz is active." in output_text
    else:
        assert "Notenschutz is active." not in output_text


def test_write_form_md_file_exists(tmp_path: Path, client_dict_internal: dict) -> None:
    """Test that FileExistsError is raised if the output file already exists."""
    template_path = tmp_path / "template.md"
    output_path = tmp_path / "output.md"

    template_path.write_text("template", encoding="utf8")
    output_path.write_text("already exists", encoding="utf8")

    with pytest.raises(FileExistsError, match="Output file already exists"):
        write_form_md(template_path, output_path, client_dict_internal)


def test_write_form_md_liquid_error_parse(
    tmp_path: Path, client_dict_internal: dict
) -> None:
    """Test that LiquidError is raised for invalid template syntax."""
    template_path = tmp_path / "template.md"
    output_path = tmp_path / "output.md"

    # Invalid liquid syntax: unclosed tag
    template_content = "Hello {{ first_name_encr "
    template_path.write_text(template_content, encoding="utf8")

    with pytest.raises(LiquidError):
        write_form_md(template_path, output_path, client_dict_internal)


def test_write_form_md_liquid_error_render(tmp_path: Path) -> None:
    """
    Test that LiquidError is caught and reraised with a note during rendering.

    Note: It's harder to trigger a render-time LiquidError with standard templates
    as liquid is quite permissive. One way is to use a filter that fails.
    """
    # Let's try to mock template.render to raise a LiquidError
    template_path = tmp_path / "template.md"
    output_path = tmp_path / "output.md"
    template_path.write_text("{{ test }}", encoding="utf8")

    with (
        mock.patch.object(
            BoundTemplate,
            "render",
            side_effect=LiquidError("Render failure", token=None),
        ),
        pytest.raises(LiquidError, match="Render failure"),
    ):
        write_form_md(template_path, output_path, {"test": "val"})
