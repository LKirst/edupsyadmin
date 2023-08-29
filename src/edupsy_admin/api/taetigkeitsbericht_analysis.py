import os
import re
import argparse
import logging
from datetime import date

import pandas as pd
import numpy as np

import dataframe_image as dfi
from fpdf import FPDF

WD_WEEK = 5 # workdays per week
WD_YEAR = 251-30 # workdays per year
WW_YEAR = WD_YEAR / WD_WEEK # work weeks per year
ZSTD_WEEK = 40 # Zeitstunden per work week
ZSTD_DAY = ZSTD_WEEK / WD_WEEK # Zeitstunden per work day
ZSTD_YEAR = ZSTD_DAY * WD_YEAR # Zeitstunden per year


class Report(FPDF):
    def __init__(self):
        super().__init__()
        self.WIDTH = 210
        self.HEIGHT = 297
        self.header_text = f'Tätigkeitsbericht {date.today()}'

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


def read_csv(*args) -> pd.DataFrame:
    l = []
    for path in args:
        df = pd.read_csv(path, index_col=None, header=0)
        l.append(df)
    concat_df = pd.concat(l, axis=0, ignore_index=True)
    return concat_df

def get_subcategories(categorykey:str, extrcategories:list[str] = None) -> list[str]:
    if extrcategories is None:
        extrcategories = []
    extrcategories.append(categorykey)
    root, subcategory_suffix = os.path.splitext(categorykey)
    if not subcategory_suffix:
        return extrcategories
    else:
        return get_subcategories(root, extrcategories)


def add_categories_to_df(df: pd.DataFrame, category_colnm: str) -> pd.DataFrame:
    category_keys=sorted(set(df.loc[:,category_colnm].unique()))
    categories_all=[]
    for key in category_keys:
        subcategories = get_subcategories(key)
        df.loc[df[category_colnm]==key,subcategories] = df.loc[
                df[category_colnm]==key, 'nsitzungen']
        categories_all.extend(subcategories)

    categories_all_set = list(sorted(set(categories_all)))
    categories_df = df[categories_all_set]
    summary_categories = categories_df.describe()
    summary_categories.loc['sum',:]=categories_df.agg('sum', axis=0)
    summary_categories.loc['count_mt3_sessions',:] = (
        categories_df[categories_df>3].agg(
            'count', axis=0)
        )
    summary_categories.loc['count_1to3_sessions',:] = (
        categories_df[
                (categories_df<=3) &
                (categories_df>=1)
                    ].agg(
            'count', axis=0)
        )
    summary_categories.loc['count_einm_kurzkont',:] = (
         categories_df[categories_df<1].agg(
            'count', axis=0)
        )

    return df, summary_categories

def summary_statistics_nsitzungen(df: pd.DataFrame, min_per_ses=45) -> pd.DataFrame:
    nsitzungen = df.groupby('school')['nsitzungen'].describe()
    nsitzungen.loc[:,'sum']=df.groupby('school')['nsitzungen'].agg('sum')
    total = df['nsitzungen'].describe()
    total['sum']=df['nsitzungen'].agg('sum')
    nsitzungen.loc['all',:]=total
    nsitzungen['zeitstunden']=nsitzungen['sum'] * min_per_ses/60
    return nsitzungen

def wstd_in_zstd(wstd_spsy: int, wstd_total: int = 23) -> dict:
    logging.info("Arbeitszeitstunden werden unter folgenden Annahmen berechnet:")
    logging.info(f"- Arbeitstage/Jahr nach Abzug von 30 Urlaubstagen: {WD_YEAR}")
    logging.info(f"- Zeitstunden einer Arbeitswoche: {ZSTD_WEEK}")
    zstd_1wstd = ZSTD_YEAR / wstd_total
    zstd_jahr_spsy = zstd_1wstd * wstd_spsy
    wstd_s = {
            'wstd_total_target':wstd_total,
            'zstd_spsy_1wstd_target':zstd_1wstd,
            'zstd_spsy_year_target':zstd_jahr_spsy,
            'zstd_spsy_week_target':zstd_jahr_spsy/WW_YEAR
    }
    return wstd_s

def summary_statistics_wstd(
        wstd_spsy: int,
        wstd_total: int,
        zstd_spsy_year_actual: float,
        *schools:str
        ) -> pd.Series:
    """Calculate Wochenstunden summary statistics

    Parameters
    ----------
    wstd_spsy : int
        n Wochenstunden school psychology
    wstd_total : int, optional
        total n Wochenstunden (not just school psychology), by default 23
    zst_spsy_year_actual: float, optional
        actual Zeitstunden school psychology
    *schools : str
        strings with name of the school and n students for the respective school,
        e.g. 'Schulname625'

    Returns
    -------
    pd.Series
        Wochenstunden summary statistics
    """
    summarystats_wstd = wstd_in_zstd(wstd_spsy,wstd_total)

    pattern = re.compile("([^\d]+)(\d+)")
    nstudents = {
            pattern.match(school).groups()[0] : int(pattern.match(school).groups()[1])
            for school in schools
            }

    for schoolnm, schoolnstudents in nstudents.items():
        summarystats_wstd['nstudents_' + schoolnm] = schoolnstudents
    summarystats_wstd['nstudents_all'] = sum(nstudents.values())
    summarystats_wstd['ratio_nstudens_wstd_spsy'] = sum(nstudents.values())/wstd_spsy

    if zstd_spsy_year_actual is not None:
        summarystats_wstd['zstd_spsy_year_actual'] = zstd_spsy_year_actual
        summarystats_wstd['zstd_spsy_week_actual'] = zstd_spsy_year_actual/WW_YEAR
        summarystats_wstd['perc_spsy_year_actual'] = (
            zstd_spsy_year_actual/summarystats_wstd['zstd_spsy_year_target']
            )*100
    return pd.Series(summarystats_wstd)

def create_taetigkeitsbericht_report(
        basename_out:str,
        name:str,
        summary_wstd: pd.Series,
        summary_categories: pd.DataFrame,
        summary_nsitzungen: pd.DataFrame
        ) -> None:

    if not os.path.exists('resources'):
        os.makedirs('resources')
    wstd_img = 'resources/summary_wstd.png'
    dfi.export(summarystats_wstd.to_frame(name='values'),
            wstd_img,
            table_conversion='matplotlib')
    nsitzungen_img='resources/summary_nsitzungen.png'
    dfi.export(summary_nsitzungen, nsitzungen_img,
            table_conversion='matplotlib')

    categorycols=summary_categories.columns
    chunks = [categorycols[x:x+8] for x in range(0, len(categorycols), 8)]

    report = Report()
    report.add_page()
    for nm, val in summary_categories.items():
        report.cell(w=15, h=9, border=0, txt=f"{nm}:")
        report.ln(6)
        for text in [
                "einmaliger Kurzkontakt",
                "1-3 Sitzungen",
                "mehr als 3 Sitzungen"]:
            report.cell(w=50, h=9, border=0, txt=text)
        report.ln(6) # linebreak
        for colnm in [
                'count_einm_kurzkont',
                'count_1to3_sessions',
                'count_mt3_sessions']:
            report.cell(w=50, h=9, border=0,txt=f"{val[colnm]:.0f}")
        report.ln(18) # linebreak
    report.add_page()
    report.image(nsitzungen_img, x=15, y=report.HEIGHT * 1/4, w=180)
    report.image(wstd_img, x=15, y=report.HEIGHT * 1/2, w=90)
    report.output(basename_out+'_report.pdf')

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
            'wstd_psy', type=int, help="Anrechnungsstunden in Wochenstunden")
    parser.add_argument('nstudents', nargs='+',
            help=(
                'list of strings with item containing the name of the school '
                'and the number of students at that school, e.g. Schulname625'))
    parser.add_argument('--out_basename', type=str, default='Taetigkeitsbericht_Out')
    parser.add_argument('--min_per_ses', type=int, default=45)
    parser.add_argument('--wstd_total', type=int, default=23,
            help="total Wochstunden (depends on your school)")
    parser.add_argument('--csvfiles', nargs='+', type=str, help='list of files')
    parser.add_argument('--name', type=str, default='Schulpsychologie',
        help='Name for the subheading of the pdf report')
    args = parser.parse_args()

    if args.csvfiles is not None:
        # Read in the csv-files and create a summary for categories
        df = read_csv(*args.csvfiles)
        df, summary_categories = add_categories_to_df(df, 'taetkey')
        df.to_csv(args.out_basename + '_df.csv')
        print(df)
        summary_categories.to_csv(args.out_basename + '_categories.csv')
        print(summary_categories)

        # Summary statistics for nsitzungen
        summarystats_nsitzungen = summary_statistics_nsitzungen(
                df, min_per_ses=args.min_per_ses)
        summarystats_nsitzungen.to_csv(args.out_basename + '_nsitzungen.csv')
        print(summarystats_nsitzungen)

        zstd_spsy_year_actual = summarystats_nsitzungen.loc['all','zeitstunden']
    else:
        zstd_spsy_year_actual = None


    # Summary statistics for Wochenstunden
    summarystats_wstd = summary_statistics_wstd(
            args.wstd_psy,
            args.wstd_total,
            zstd_spsy_year_actual,
            *args.nstudents
            )
    summarystats_wstd.to_csv(args.out_basename + '_wstd.csv')
    print(summarystats_wstd)

    create_taetigkeitsbericht_report(
            args.out_basename,
            args.name,
            summarystats_wstd,
            summary_categories,
            summarystats_nsitzungen
            )
