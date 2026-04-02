import os
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import TYPE_CHECKING

import matplotlib.pyplot as plt
import numpy as np
import scipy.stats as stats
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import (
    BaseDocTemplate,
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

if TYPE_CHECKING:
    import pandas as pd

ResultsItem = str | tuple[str, str]


@dataclass
class TestReportData:
    heading: str
    client_name_or_id: str
    grade: str | int | None
    test_date: date
    birthday: date
    age_str: str
    results: list[ResultsItem]
    plot_path: str | os.PathLike[str]


class TestReport:
    def __init__(self, data: TestReportData) -> None:
        self.data = data
        self.styles = getSampleStyleSheet()
        self.styles.add(
            ParagraphStyle(
                name="SectionHeader",
                parent=self.styles["Normal"],
                fontName="Helvetica-Bold",
                fontSize=11,
                spaceBefore=12,
                spaceAfter=6,
            )
        )
        self.styles.add(
            ParagraphStyle(
                name="MainHeading",
                parent=self.styles["Normal"],
                fontName="Helvetica-Bold",
                fontSize=14,
                alignment=1,  # Centered
                spaceAfter=20,
            )
        )

    def _header_footer(self, canvas, _doc) -> None:
        canvas.saveState()
        # Footer
        canvas.setFont("Helvetica-Oblique", 8)
        canvas.setStrokeColor(colors.grey)
        canvas.drawCentredString(A4[0] / 2.0, 1 * cm, f"Seite {canvas.getPageNumber()}")
        canvas.restoreState()

    def build(self, output_path: str | os.PathLike[str]) -> None:
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=A4,
            rightMargin=2 * cm,
            leftMargin=2 * cm,
            topMargin=2 * cm,
            bottomMargin=2 * cm,
        )
        flowables = []

        # Heading
        flowables.append(Paragraph(self.data.heading, self.styles["MainHeading"]))

        # Client Metadata Table
        metadata = [
            ["Name / ID:", str(self.data.client_name_or_id)],
            ["Klasse:", str(self.data.grade) if self.data.grade is not None else ""],
            ["Testdatum:", self.data.test_date.strftime("%d.%m.%Y")],
            ["Geburtsdatum:", self.data.birthday.strftime("%d.%m.%Y")],
            ["Alter:", self.data.age_str],
        ]
        t = Table(metadata, colWidths=[4 * cm, 10 * cm])
        t.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                ]
            )
        )
        flowables.append(t)
        flowables.append(Spacer(1, 12))

        # Results
        for item in self.data.results:
            if isinstance(item, str):
                flowables.append(Paragraph(item, self.styles["SectionHeader"]))
            else:
                label, value = item
                res_t = Table([[label, value]], colWidths=[8 * cm, 6 * cm])
                res_t.setStyle(
                    TableStyle(
                        [
                            ("FONTNAME", (0, 0), (0, 0), "Helvetica"),
                            ("FONTNAME", (1, 0), (1, 0), "Helvetica"),
                            ("ALIGN", (0, 0), (0, 0), "LEFT"),
                            ("ALIGN", (1, 0), (1, 0), "LEFT"),
                        ]
                    )
                )
                flowables.append(res_t)

        flowables.append(Spacer(1, 20))

        # Plot
        if Path(self.data.plot_path).exists():
            img = Image(str(self.data.plot_path))
            img = _scale_image(img, available_width=A4[0] - 3 * cm)
            flowables.append(img)

        doc.build(
            flowables, onFirstPage=self._header_footer, onLaterPages=self._header_footer
        )


class TaetigkeitsberichtReport:
    def __init__(self, name: str) -> None:
        self.name = name
        self.styles = getSampleStyleSheet()
        self.header_text = f"Tätigkeitsbericht {date.today()} ({name})"

    def _header_footer(self, canvas: Canvas, _doc: BaseDocTemplate) -> None:
        canvas.saveState()
        # Header
        canvas.setFont("Helvetica-Bold", 11)
        canvas.drawCentredString(A4[0] / 2.0, A4[1] - 1.5 * cm, self.header_text)

        # Footer
        canvas.setFont("Helvetica-Oblique", 8)
        canvas.drawCentredString(A4[0] / 2.0, 1 * cm, f"Seite {canvas.getPageNumber()}")
        canvas.restoreState()

    def build(
        self,
        output_path: str | os.PathLike[str],
        summary_wstd_img: str,
        summary_h_sessions_img: str | None = None,
        summary_categories: pd.DataFrame | None = None,
    ) -> None:
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=A4,
            rightMargin=1.5 * cm,
            leftMargin=1.5 * cm,
            topMargin=2.5 * cm,
            bottomMargin=2 * cm,
        )
        flowables = []

        if summary_categories is not None:
            for nm, val in summary_categories.items():
                flowables.append(Paragraph(f"<b>{nm}:</b>", self.styles["Normal"]))
                flowables.append(Spacer(1, 6))

                data = [
                    ["einmaliger Kurzkontakt", "1-3 Sitzungen", "mehr als 3 Sitzungen"],
                    [
                        f"{val['count_1_session']:.0f}",
                        f"{val['count_2to3_sessions']:.0f}",
                        f"{val['count_mt3_sessions']:.0f}",
                    ],
                ]
                t = Table(data, colWidths=[5 * cm] * 3)
                t.setStyle(
                    TableStyle(
                        [
                            ("FONTNAME", (0, 0), (-1, 0), "Helvetica"),
                            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                        ]
                    )
                )
                flowables.append(t)
                flowables.append(Spacer(1, 18))

        if summary_h_sessions_img and Path(summary_h_sessions_img).exists():
            flowables.append(Spacer(1, 20))
            img = Image(summary_h_sessions_img)
            img = _scale_image(img, available_width=A4[0] - 3 * cm)
            flowables.append(img)

        if Path(summary_wstd_img).exists():
            flowables.append(Spacer(1, 20))
            img = Image(summary_wstd_img)
            img = _scale_image(img, available_width=A4[0] - 3 * cm)
            flowables.append(img)

        doc.build(
            flowables, onFirstPage=self._header_footer, onLaterPages=self._header_footer
        )


def _scale_image(img: Image, available_width: float) -> Image:
    aspect = img.imageHeight / float(img.imageWidth)
    img.drawWidth = available_width
    img.drawHeight = available_width * aspect
    return img


def normal_distribution_plot(
    v_lines: list[int | float], plot_filename: str | os.PathLike[str] = "plot.png"
) -> None:
    mu = 0
    variance = 1
    sigma = np.sqrt(variance)
    x = np.linspace(mu - 3 * sigma, mu + 3 * sigma, 100)
    plt.figure(figsize=(8, 4))
    plt.plot(x, stats.norm.pdf(x, mu, sigma))

    normal_area = np.arange(-1, 1, 1 / 20)
    plt.fill_between(
        normal_area, stats.norm.pdf(normal_area, mu, sigma), alpha=0.3, color="grey"
    )

    for value in v_lines:
        plt.vlines(x=value, ymin=0, ymax=0.45)
    plt.tight_layout()
    plt.savefig(plot_filename)
    plt.close()
