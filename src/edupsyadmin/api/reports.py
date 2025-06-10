import math
import os

import matplotlib.pyplot as plt
import numpy as np
import scipy.stats as stats
from fpdf import FPDF


class Report(FPDF):
    def __init__(self, heading: str, reporttext: str, plot: str | os.PathLike[str]):
        super().__init__()
        self.reporttext = reporttext
        self.plot = plot
        self.WIDTH = 210
        self.HEIGHT = 297
        self.header_text = heading

    def header(self) -> None:
        self.set_font("Arial", "B", 11)
        self.cell(w=0, h=10, text=self.header_text, border=0, ln=0, align="C")
        self.ln(20)  # line break

    def footer(self) -> None:
        # page numbers
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.set_text_color(128)
        self.cell(0, 10, "Page " + str(self.page_no()), border=0, ln=0, align="C")

    def page_body(self) -> None:
        for line in self.reporttext:
            self.cell(w=15, h=9, border=0, text=line)
            self.ln()  # line break
        self.image(self.plot, 15, self.WIDTH / 2 + 50, self.WIDTH - 50)

    def print_page(self) -> None:
        self.add_page()
        self.page_body()


def normal_distribution_plot(
    v_lines: list[int | float], plot_filename: str | os.PathLike[str] = "plot.png"
) -> None:
    mu = 0
    variance = 1
    sigma = math.sqrt(variance)
    x = np.linspace(mu - 3 * sigma, mu + 3 * sigma, 100)
    plt.plot(x, stats.norm.pdf(x, mu, sigma))

    normal_area = np.arange(-1, 1, 1 / 20)
    plt.fill_between(
        normal_area, stats.norm.pdf(normal_area, mu, sigma), alpha=0.3, color="grey"
    )

    for value in v_lines:
        plt.vlines(x=value, ymin=0, ymax=0.45)
    plt.savefig(plot_filename)
