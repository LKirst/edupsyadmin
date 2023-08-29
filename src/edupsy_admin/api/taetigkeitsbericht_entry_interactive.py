from importlib.resources import files
import pandas as pd

def get_taet_categories():
    categoryfile = files('edupsy_admin.data').joinpath('taetigkeitsbericht_categories_SJ202223.ods')
    return pd.read_excel(categoryfile)

def askyn(prompt):
    yes = {"yes", "ye", "y"}
    no = {"no", "n"}
    answ = input(prompt).lower()
    if answ in yes:
        return 1
    elif answ in no:
        return 0
    else:
        print('Only "y" or "n" are allowed as responses.')
        return askyn(prompt) # ask recursively until the answer is correct

def interactive_collect_taet(categories):
    possible_keywords = set(categories)
    data = []
    while askyn(f'Continue (y|n)? '):
        school=input('school: ')
        client_id=input('client_id: ')
        keyword=input('keyword: ')
        while keyword not in possible_keywords:
            keyword=input('keyword (previous answer is not an option): ')
        nsitzungen=input('nsitzungen: ')
        data.append([
            school,
            client_id,
            keyword,
            nsitzungen
            ])
    df = pd.DataFrame(data)
    df.to_csv('archivierung.csv')

if __name__ == "__main__":
    df = get_taet_categories()
    interactive_collect_taet(df['taetkey'])
