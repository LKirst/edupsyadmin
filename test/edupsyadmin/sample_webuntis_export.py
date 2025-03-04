import argparse
from pathlib import Path

# ruff: noqa: E501
webuntis_content = """name	longName	foreName	gender	birthDate	klasse.name	entryDate	address.email	address.mobile	address.phone	address.city	address.postCode	address.street
MustermMax1	Mustermann	Max	m	01.01.2000	11TKKG	12.09.2023	max.mustermann@example.de	+491713920000	02214710000	Augsburg	86150	Beispielweg 99
MustermErika1	Mustermann	Erika	f	24.12.2000	11TKKG	12.09.2023	rika.mustermann@example.de	+491713920001	08999998000	Augsburg	86150	Beispielweg 99
NovácJan	Novác	Jan	m	18.11.2000	11TKKG	12.09.2023	jan.novac@example.de	+491713920002	02214710001	München	80331	Platzhalter 42
LießMüller1	Müller	Ließchen	f	30.12.2000	11TKKG	12.09.2023	lieschen.mueller@example.de	+491713920003	08999998001	München	80331	Eine Straße 1
"""


def create_sample_webuntis_export(path: Path | str) -> None:
    if isinstance(path, str):
        path = Path(path)
    path.write_text(webuntis_content, encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create a sample webuntis export.")
    parser.add_argument("output_file", type=str, help="Path to the output csv file.")
    args = parser.parse_args()
    create_sample_webuntis_export(args.output_file)
