from importlib.resources import files

import pandas as pd


def get_taet_categories() -> set[str]:
    """
    Retrieve the set of taetigkeitsbericht categories from the CSV file.

    :return: A set containing the categories.
    """
    with (
        files("edupsyadmin.data")
        .joinpath("taetigkeitsbericht_categories.csv")
        .open("r") as categoryfile
    ):
        categories = pd.read_csv(categoryfile)["taetkey"]
    return set(categories)


def check_keyword(keyword: str | None) -> str | None:
    """
    Check if the provided keyword is a valid taetigkeitsbericht category.

    :param keyword: The keyword to be checked.
    :return: The valid keyword or None if the keyword is empty.
    """
    possible_keywords = get_taet_categories()
    if (not keyword) or (keyword in possible_keywords):
        return keyword
    raise ValueError
