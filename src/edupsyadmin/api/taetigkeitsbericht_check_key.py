from importlib.resources import files

import pandas as pd

from ..core.logger import logger


def get_taet_categories():
    categoryfile = files("edupsyadmin.data").joinpath(
        "taetigkeitsbericht_categories_SJ202324.ods"
    )
    categories = pd.read_excel(categoryfile)["taetkey"]
    return set(categories)


def check_keyword(keyword):
    possible_keywords = get_taet_categories()
    if keyword:
        while keyword not in possible_keywords:
            keyword = input(f'keyword ("{keyword}" is not an option): ')
    else:
        logger.debug("taetigkeitsbericht keyword is empty")
    return keyword
