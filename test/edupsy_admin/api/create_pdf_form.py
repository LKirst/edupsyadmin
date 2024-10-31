from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


def create_pdf_with_single_text_field(pdf_filename):
    # Set up the canvas
    c = canvas.Canvas(pdf_filename, pagesize=letter)
    page_width, page_height = letter

    # Define the position and size of the text field
    x = 100  # x position
    y = 700  # y position
    width = 400  # width of the text field
    height = 30  # height of the text field

    # Create a text field
    c.acroForm.textfield(
        name="myTextField",
        tooltip="Enter text here",
        x=x,
        y=y,
        width=width,
        height=height,
        borderColor=colors.black,
        fillColor=colors.white,
        textColor=colors.black,
        forceBorder=True,
        maxlen=100,
        value="",
    )

    # Add some text above the form field
    c.drawString(100, 740, "Please fill in the text field below:")

    c.save()


# Specify the output PDF filename
pdf_filename = "output_form.pdf"
create_pdf_with_single_text_field(pdf_filename)
