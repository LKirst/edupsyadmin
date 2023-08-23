import pandas as pd


possible_keywords = {
        'slbb.slb.wchslbundesl', # B. z. Schullaufbahn: Wechsel aus anderem Bundesland
        'slbb.slb.wchslstaat', # B. z. Schullaufbahn: Wechsel aus einem anderen Bundesland
        'slbb.slb.sonstige', # B. z. Schullaufbahn: Schullwahl, Wechsel, Abschlüsse
        'slbb.einsch', # Einschulung
        'slbb.uebertweiterf', # Übertritt an weiterführende Schulen
        'slbb.berufustudienw', # Berufs- und Studienwahlorientierung
        'slbb.sonstiges', # Schullaufbahnberatung: Sonstiges
        'ppb.besbeg', # Besondere Begabungen
        'ppb.inkl', # Inklusion
        'ppb.integrmigr', # Integration / Migration
        'ppb.lrst', # LRST Beratung
        'sl.lrststllngn.erstm', # Erst. einer schulpsy. Stellungn.: erstmalig
        'sl.lrststllngn.erneut', # Erst. einer schulpsy. Stellungn.: erneut
        'sl.lrststllngn.facharzt', # Erst. einer schulpsy. Stellungn.: aufgr. fachärztl. Zeugnisses
        'sl.dyskalkulie', # Dyskalkulie
        'sl.sonstige', # Weitere Lern- und Leistungsprobleme
        'schulabsentismus', # Schulabsentismus
        'subkl.a.pruefungs',
        'subkl.a.schulangst',
        'subkl.allgverhaltenspr',
        'subkl.gewaltaggr',
        'subkl.mobbing',
        'geschlechterdys',
        'konfl.peer',
        'pubertaet',
        'kl.angstst',
        'kl.depr',
        'kl.essst',
        'kl.sucht',
        'kl.suiz',
        'kl.trauma',
        'kl.zwang',
        'kl.adhs',
        'kl.autism',
        'kl.sonst',
        'chronischeerkr',
        'konfl.lehrkr',
        'sonstiges'
        }


def validate_taetigkeitsbericht_keyword(keyword:str) -> bool:
    return keyword in possible_keywords

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
        return askyn(prompt)

if __name__ == "__main__":
    data = []
    while askyn(f'Continue (y|n)? '):
        client_id=input('client_id: ')
        last_name=input('last_name: ')
        keyword=input('keyword: ')
        while keyword not in possible_keywords:
            keyword=input('keyword (previous answer is not an option): ')
        nsitzungen=input('nsitzungen: ')
        data.append([
            client_id,
            last_name,
            keyword,
            nsitzungen
            ])
    df = pd.DataFrame(data)
    df.to_csv('archivierung.csv')
