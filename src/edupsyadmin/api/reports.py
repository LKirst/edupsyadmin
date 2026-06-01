import os
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from statistics import NormalDist

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
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

ResultsItem = str | tuple[str, str]


@dataclass
class TestReportData:
    __test__ = False
    heading: str
    client_name_or_id: str
    grade: str | int | None
    test_date: date
    birthday: date
    age_str: str
    results: list[ResultsItem]
    plot_path: str | os.PathLike[str]


class BasePDFReport:
    """Base class for PDF reports with shared styles and infrastructure."""

    def __init__(self) -> None:
        self.styles = getSampleStyleSheet()
        self._setup_styles()

    def _setup_styles(self) -> None:
        """Initialize custom styles for reports."""
        self.styles.add(
            ParagraphStyle(
                name="SectionHeader",
                parent=self.styles["Normal"],
                fontName="Helvetica-Bold",
                fontSize=11,
                spaceBefore=12,
                spaceAfter=6,
            ),
        )
        self.styles.add(
            ParagraphStyle(
                name="MainHeading",
                parent=self.styles["Normal"],
                fontName="Helvetica-Bold",
                fontSize=14,
                alignment=TA_CENTER,
                spaceAfter=20,
            ),
        )
        self.styles.add(
            ParagraphStyle(
                name="NormalRight",
                parent=self.styles["Normal"],
                alignment=TA_RIGHT,
            ),
        )
        self.styles.add(
            ParagraphStyle(
                name="NormalCenter",
                parent=self.styles["Normal"],
                alignment=TA_CENTER,
            ),
        )

    def _header_footer(self, canvas: Canvas, _doc: BaseDocTemplate) -> None:
        """Draw header and footer on the page."""
        canvas.saveState()
        self._draw_footer(canvas)
        self._draw_header(canvas)
        canvas.restoreState()

    def _draw_footer(self, canvas: Canvas) -> None:
        """Draw the default footer."""
        canvas.setFont("Helvetica-Oblique", 8)
        canvas.setStrokeColor(colors.grey)
        canvas.drawCentredString(A4[0] / 2.0, 1 * cm, f"Seite {canvas.getPageNumber()}")

    def _draw_header(self, canvas: Canvas) -> None:
        """Draw the header (to be overridden if needed)."""
        pass

    def _scale_image(self, img: Image, available_width: float) -> Image:
        """
        Scale an image to fit within the available width while maintaining
        aspect ratio.
        """
        aspect = img.imageHeight / float(img.imageWidth)
        img.drawWidth = available_width
        img.drawHeight = available_width * aspect
        return img

    def _df_to_table(
        self,
        df: pd.DataFrame,
        col_widths: list[float] | None = None,
        float_precision: int = 1,
    ) -> Table:
        """
        Convert a pandas DataFrame to a ReportLab Table with proper alignment.

        Float columns are right-aligned for visual alignment of decimal points.
        Integer and text columns remain left-aligned. The index column is
        always left-aligned.

        :param df: DataFrame to convert
        :param col_widths: Optional column widths; enables text wrapping via Paragraphs
        :param float_precision: Decimal places for float formatting (default: 1)
        :return: Configured ReportLab Table
        """
        # Detect float columns (excluding index)
        float_cols = self._get_float_column_indices(df)

        # Build table data
        header = ["", *df.columns.tolist()]
        data = self._build_table_data(
            df, header, col_widths, float_precision, float_cols
        )

        # Create and style table
        table = Table(data, colWidths=col_widths)
        table.setStyle(self._create_table_style(float_cols))

        return table

    def _get_float_column_indices(self, df: pd.DataFrame) -> set[int]:
        """
        Identify column indices containing float data.

        :param df: DataFrame to analyze
        :return: Set of 1-based column indices (accounting for index column at 0)
        """
        float_cols = set()
        for col_idx, col_name in enumerate(df.columns, start=1):
            if pd.api.types.is_float_dtype(df[col_name]):
                float_cols.add(col_idx)
        return float_cols

    def _build_table_data(
        self,
        df: pd.DataFrame,
        header: list[str],
        col_widths: list[float] | None,
        float_precision: int,
        float_cols: set[int] | None = None,
    ) -> list[list[str | Paragraph]]:
        """
        Build table data with optional Paragraph wrapping.

        :param df: Source DataFrame
        :param header: Header row including index column
        :param col_widths: If provided, wrap cells in Paragraphs
        :param float_precision: Decimal places for floats
        :param float_cols: Indices of columns containing floats
        :return: 2D list of table cells
        """
        use_paragraphs = col_widths is not None
        float_cols = float_cols or set()

        # Initialize with proper type
        data: list[list[str | Paragraph]] = []

        # Header row
        if use_paragraphs:
            data.append(
                [
                    Paragraph(f"<b>{h}</b>", self.styles["Normal"]) if h else ""
                    for h in header
                ]
            )
        else:
            data.append(list(header))

        # Data rows
        for index, row in df.iterrows():
            formatted_row: list[str | Paragraph] = [
                self._format_cell(str(index), use_paragraphs)
            ]

            for col_idx, val in enumerate(row, start=1):
                cell_value = self._format_value(val, float_precision)
                alignment = TA_RIGHT if col_idx in float_cols else TA_LEFT
                formatted_row.append(
                    self._format_cell(cell_value, use_paragraphs, alignment=alignment)
                )

            data.append(formatted_row)

        return data

    def _format_value(self, val: object, precision: int) -> str:
        """
        Format a cell value with appropriate precision for numerics.

        :param val: Value to format
        :param precision: Decimal places for floats
        :return: Formatted string
        """
        if val is None or val is pd.NA:
            return ""
        if isinstance(val, int | np.integer):
            return str(val)
        if isinstance(val, float | np.floating):
            return f"{val:.{precision}f}"
        return str(val)

    def _format_cell(
        self, value: str, use_paragraph: bool, alignment: int = TA_LEFT
    ) -> str | Paragraph:
        """
        Wrap cell value in Paragraph if needed.

        :param value: Cell content
        :param use_paragraph: Whether to wrap in Paragraph for text wrapping
        :param alignment: Alignment (TA_LEFT, TA_RIGHT, TA_CENTER)
        :return: Raw string or Paragraph object
        """
        if not use_paragraph:
            return value

        style = self.styles["Normal"]
        if alignment == TA_RIGHT:
            style = self.styles["NormalRight"]
        elif alignment == TA_CENTER:
            style = self.styles["NormalCenter"]

        return Paragraph(value, style)

    def _create_table_style(self, float_cols: set[int]) -> TableStyle:
        """
        Create TableStyle with right-alignment for float columns.

        :param float_cols: Set of column indices to right-align
        :return: Configured TableStyle
        """
        style_commands = [
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            # Default left alignment for all columns
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ]

        # Right-align float columns (data rows only, not header)
        style_commands.extend(
            ("ALIGN", (col_idx, 1), (col_idx, -1), "RIGHT") for col_idx in float_cols
        )

        return TableStyle(style_commands)


class TestReport(BasePDFReport):
    """Report class for psychological tests like CFT and LGVT."""

    __test__ = False

    def __init__(self, data: TestReportData) -> None:
        super().__init__()
        self.data = data

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
            ["Name / ID:", self.data.client_name_or_id],
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
                ],
            ),
        )
        flowables.extend((t, Spacer(1, 12)))

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
                        ],
                    ),
                )
                flowables.append(res_t)

        flowables.append(Spacer(1, 20))

        # Plot
        if Path(self.data.plot_path).exists():
            img = Image(str(self.data.plot_path))
            img = self._scale_image(img, available_width=A4[0] - 3 * cm)
            flowables.append(img)

        doc.build(
            flowables,
            onFirstPage=self._header_footer,
            onLaterPages=self._header_footer,
        )


class TaetigkeitsberichtReport(BasePDFReport):
    """Report class for activity reports."""

    def __init__(self, name: str, report_date: date | None = None) -> None:
        super().__init__()
        self.name = name
        report_date = report_date or date.today()
        self.header_text = f"Tätigkeitsbericht {report_date} ({name})"

    def _draw_header(self, canvas: Canvas) -> None:
        canvas.setFont("Helvetica-Bold", 11)
        canvas.drawCentredString(A4[0] / 2.0, A4[1] - 1.5 * cm, self.header_text)

    def build(
        self,
        output_path: str | os.PathLike[str],
        summary_wstd: pd.DataFrame,
        summary_h_sessions: pd.DataFrame | None = None,
        summary_categories: pd.DataFrame | None = None,
    ) -> None:
        left_margin = right_margin = 1.5 * cm
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=A4,
            rightMargin=right_margin,
            leftMargin=left_margin,
            topMargin=2.5 * cm,
            bottomMargin=2 * cm,
        )
        avail_width = A4[0] - left_margin - right_margin
        flowables = []

        if summary_categories is not None:
            for nm, val in summary_categories.items():
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
                        ],
                    ),
                )
                flowables.extend(
                    (
                        Paragraph(f"<b>{nm}:</b>", self.styles["Normal"]),
                        Spacer(1, 6),
                        t,
                        Spacer(1, 18),
                    ),
                )

        if summary_h_sessions is not None:
            n_cols = len(summary_h_sessions.columns) + 1
            col_w = avail_width / (n_cols + 1)
            h_sessions_colwidths = [col_w * 2] + [col_w] * (n_cols - 1)
            flowables.extend(
                (
                    Paragraph("<b>Zeitstunden:</b>", self.styles["Normal"]),
                    Spacer(1, 6),
                    self._df_to_table(
                        summary_h_sessions, col_widths=h_sessions_colwidths
                    ),
                    Spacer(1, 18),
                )
            )

        flowables.extend(
            (
                Paragraph("<b>Wochenstunden:</b>", self.styles["Normal"]),
                Spacer(1, 6),
                self._df_to_table(
                    summary_wstd,
                    col_widths=[3.5 * cm, 2.0 * cm, avail_width - 5.5 * cm],
                ),
                Spacer(1, 18),
            )
        )

        doc.build(
            flowables,
            onFirstPage=self._header_footer,
            onLaterPages=self._header_footer,
        )


def normal_distribution_plot(
    v_lines: list[int | float],
    plot_filename: str | os.PathLike[str] = "plot.png",
) -> None:
    mu = 0
    variance = 1
    sigma = np.sqrt(variance)
    dist = NormalDist(mu, sigma)
    x = np.linspace(mu - 3 * sigma, mu + 3 * sigma, 100)
    plt.figure(figsize=(8, 4))
    plt.plot(x, [dist.pdf(val) for val in x])

    normal_area = np.arange(-1, 1, 1 / 20)
    plt.fill_between(
        normal_area,
        [dist.pdf(val) for val in normal_area],
        alpha=0.3,
        color="grey",
    )

    for value in v_lines:
        plt.vlines(x=value, ymin=0, ymax=0.45)
    plt.tight_layout()
    plt.savefig(plot_filename)
    plt.close()
