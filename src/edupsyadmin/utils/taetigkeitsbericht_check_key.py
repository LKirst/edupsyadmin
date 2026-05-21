import csv
from importlib.resources import files


def get_taet_categories() -> set[str]:
    """
    Retrieve the set of taetigkeitsbericht categories from the CSV file.

    :return: A set containing the categories.
    """
    with (
        files("edupsyadmin.data")
        .joinpath("taetigkeitsbericht_categories.csv")
        .open("r", encoding="utf-8") as categoryfile
    ):
        reader = csv.DictReader(categoryfile)
        return {row["taetkey"] for row in reader if row.get("taetkey")}


def check_keyword(keyword: str | None) -> str | None:
    """
    Check if the provided keyword is a valid taetigkeitsbericht category.

    :param keyword: The keyword to be checked.
    :return: The valid keyword or None if the keyword is empty.
    """
    possible_keywords = get_taet_categories()
    if (not keyword) or (keyword in possible_keywords):
        return keyword
    raise ValueError(
        f"Invalid keyword: '{keyword}'. Possible keywords are: "
        f"{', '.join(sorted(possible_keywords))}",
    )
