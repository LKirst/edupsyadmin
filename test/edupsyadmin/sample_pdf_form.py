import argparse

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


def create_pdf_form(pdf_filename: str) -> None:
    c = canvas.Canvas(pdf_filename, pagesize=A4)
    _page_width, _page_height = A4

    # a textfield widget
    c.drawString(100, 740, "first_name:")
    c.acroForm.textfield(
        name="first_name_encr",
        x=100,
        y=700,
        width=400,
        height=30,
        borderColor=colors.black,
        fillColor=colors.white,
        textColor=colors.black,
        forceBorder=True,
        maxlen=100,
        value="",
    )

    # two checkbox widgets (the value is either YES or OFF)
    c.drawString(130, 650, "notenschutz")
    c.acroForm.checkbox(
        name="notenschutz",
        x=100,
        y=650,
        size=20,
        borderWidth=3,
        borderColor=colors.black,
    )
    c.drawString(130, 550, "nachteilsausgleich")
    c.acroForm.checkbox(
        name="nachteilsausgleich",
        x=100,
        y=550,
        size=20,
        borderWidth=3,
        borderColor=colors.black,
    )

    # Radio buttons for lrst_schpsy selection
    c.drawString(100, 500, "lrst_schpsy:")
    options = [
        ("schpsy", "1", 450),
        ("psychia", "2", 420),
        ("psychoth", "3", 390),
        ("spz", "4", 360),
        ("other", "5", 330),
    ]
    for label, value, y_pos in options:
        c.acroForm.radio(
            name="lrst_schpsy",
            tooltip=label,
            value=value,
            selected=False,
            x=100,
            y=y_pos,
            size=20,
            borderWidth=1,
            borderColor=colors.black,
            fillColor=colors.white,
            forceBorder=True,
        )
        c.drawString(130, y_pos, label)

    # multiline text field
    c.drawString(100, 280, "address_multiline:")
    c.acroForm.textfield(
        name="addr_m_wname",
        x=100,
        y=60,
        width=400,
        height=200,
        borderColor=colors.black,
        fillColor=colors.white,
        textColor=colors.black,
        forceBorder=True,
        maxlen=1000,
        value="",
        fieldFlags="multiline",
    )

    c.save()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create a sample PDF form.")
    parser.add_argument("filename", help="The name of the PDF file to create.")
    args = parser.parse_args()

    create_pdf_form(args.filename)
