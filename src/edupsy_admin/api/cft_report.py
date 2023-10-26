#!/usr/bin/env python3
import os
from fpdf import FPDF
import matplotlib.pyplot as plt
import numpy as np
import scipy.stats as stats
import math
import argparse

from datetime import datetime

from convert_measures import iq_to_z, iq_to_t
from datediff import mydatediff


class Report(FPDF):
    def __init__(self, text, plot, testdate, client_id):
        super().__init__()
        self.text = text
        self.plot = plot
        self.WIDTH = 210
        self.HEIGHT = 297
        self.header_text = f"CFT 20-R (Testdatum: {testdate}; Code: {client_id})"

    def header(self):
        self.set_font("Arial", "B", 11)
        self.cell(w=0, h=10, txt=self.header_text, border=0, ln=0, align="C")
        self.ln(20)

    def footer(self):
        # page numbers
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.set_text_color(128)
        self.cell(0, 10, "Page " + str(self.page_no()), border=0, ln=0, align="C")

    def page_body(self):
        for line in self.text:
            self.cell(w=15, h=9, border=0, txt=line)
            self.ln(h="")
        self.image(self.plot, 15, self.WIDTH / 2 + 50, self.WIDTH - 50)

    def print_page(self):
        self.add_page()
        self.page_body()


def create_report(path):
    client_id = int(input("Client ID: "))
    birthday = datetime.strptime(
        input("Geburtsdatum (YYYY-mm-dd): "), "%Y-%m-%d"
    ).date()
    testdate = datetime.strptime(input("Testdatum (YYYY-mm-dd): "), "%Y-%m-%d").date()

    age_str = f"Alter: {mydatediff(birthday, testdate)}"
    text = []
    text.append(age_str)

    raw_part1_min = int(input("Teil 1 min: "))
    raw_part1_max = int(input("Teil 1 max: "))
    raw_part2 = int(input("Teil 2: "))

    raw_total_min = raw_part1_min + raw_part2
    raw_total_max = raw_part1_max + raw_part2

    print(age_str)
    print("Rohwerte:")
    print(f"\tTeil 1 min\t = {raw_part1_min}")
    print(f"\tTeil 1 max\t = {raw_part1_max}")
    print(f"\tTeil 2\t\t = {raw_part2}")
    print(f"\tGes min\t\t = {raw_total_min}")
    print(f"\tGes max\t\t = {raw_total_max}")

    iq_part1_min = int(input("IQ Teil 1 min: "))
    iq_part1_max = int(input("IQ Teil 1 max: "))
    iq_part2 = int(input("IQ Teil 2: "))
    iq_total_min = int(input("IQ Total min: "))
    iq_total_max = int(input("IQ Total max: "))

    results = [
        f"Teil 1 min\t = {raw_part1_min}; \tIQ Teil 1 min\t = {iq_part1_min}; T = {iq_to_t(iq_part1_min):.2f}",
        f"Teil 1 max\t = {raw_part1_max}; \tIQ Teil 1 max\t = {iq_part1_max}; T = {iq_to_t(iq_part1_max):.2f}",
        f"Teil 2\t\t = {raw_part2}; \tIQ Teil 2\t = {iq_part2}; T = {iq_to_t(iq_part2):.2f}",
        f"Ges. min\t\t = {raw_total_min}; \tIQ Ges min\t = {iq_total_min}; T = {iq_to_t(iq_total_min):.2f}",
        f"Ges. max\t\t = {raw_total_max}; \tIQ Ges max\t = {iq_total_max}; T = {iq_to_t(iq_total_max):.2f}",
        f"Differenz IQ Teil 1 max - Teil 2 (sign. ist >= 12): IQ-Wert-Differenz = {iq_part1_max - iq_part2}",
    ]

    text += results

    # create a normal distribution plot and save it as a png
    iq_values = [iq_part1_min, iq_part1_max, iq_part2, iq_total_min, iq_total_max]
    z_values = [iq_to_z(iq) for iq in iq_values]
    fn_plot = "normal_distribution_plot.png"
    normal_distribution_plot(z_values, fn_plot)

    # create the pdf
    report = Report(text, fn_plot, testdate, client_id)
    report.print_page()
    report.output(os.path.join(path, "{client_id}_Auswertung.pdf"), "F")

    # remove the plot png
    os.remove(fn_plot)


def normal_distribution_plot(v_lines, plot_filename="plot.png"):
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


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-p",
        "--path",
        default=".",
        help="The directory where the output pdf should be saved",
    )
    args = parser.parse_args()
    create_report(args.path)
