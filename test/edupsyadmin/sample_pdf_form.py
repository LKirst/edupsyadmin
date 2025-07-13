import argparse

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


def create_pdf_form(pdf_filename: str) -> None:
    c = canvas.Canvas(pdf_filename, pagesize=A4)
    page_width, page_height = A4

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

    # Radio buttons for gender selection
    # TODO: test whether the correct value was set
    c.drawString(100, 500, "Gender:")
    c.acroForm.radio(
        name="gender",
        value="f",
        x=100,
        y=480,
        size=20,
        borderWidth=1,
        borderColor=colors.black,
        fillColor=colors.white,
        forceBorder=True,
    )
    c.drawString(130, 480, "f")
    c.acroForm.radio(
        name="gender",
        value="m",
        x=100,
        y=450,
        size=20,
        borderWidth=1,
        borderColor=colors.black,
        fillColor=colors.white,
        forceBorder=True,
    )
    c.drawString(130, 450, "m")

    # multiline text field
    c.drawString(100, 350, "address_multiline:")
    c.acroForm.textfield(
        name="address_multiline",
        x=100,
        y=150,
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
