from importlib.resources import files
import pandas as pd

def get_taet_categories():
    categoryfile = files('edupsy_admin.data').joinpath('taetigkeitsbericht_categories_SJ202223.ods')
    categories = pd.read_excel(categoryfile)['taetkey']
    return set(categories)

def check_keyword(categories):
    possible_keywords = get_taet_categories()
    if keyword:
        while keyword not in possible_keywords:
            keyword=input(f'keyword ("{keyword}" is not an option): ')
