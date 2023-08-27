import os
import argparse
import pandas as pd
import numpy as np

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
        df.loc[df[category_colnm]==key,subcategories] = 1
        categories_all.extend(subcategories)
    categories_all_set = list(set(categories_all))
    df[categories_all_set]=df[categories_all_set].astype('category')
    return df

def summary_statistics_nsitzungen(df: pd.DataFrame, min_per_ses=45) -> pd.DataFrame:
    nsitzungen = df.groupby('school')['nsitzungen'].describe()
    nsitzungen.loc[:,'sum']=df.groupby('school')['nsitzungen'].agg('sum')
    total = df['nsitzungen'].describe()
    total['sum']=df['nsitzungen'].agg('sum')
    nsitzungen.loc['all',:]=total
    nsitzungen['zeitstunden']=nsitzungen['sum'] * min_per_ses/60
    return nsitzungen

def summary_statistics_categories(df: pd.DataFrame) -> pd.DataFrame:
    pass

def wochenstunden_to_hoursperweek(ws: int) -> float:
    pass

def ratio_students_wochenstunden(ws:int, *args) -> float:
    nstudents = sum(args)
    return ws/nstudents

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--out_basename', type=str, default='Taetigkeitsbericht_Out')
    parser.add_argument('csvfiles', nargs='+', help='List of files')
    args = parser.parse_args()

    df = read_csv(*args.csvfiles)
    df = add_categories_to_df(df, 'taetkey')
    df.to_csv(args.out_basename + '_df.csv')
    print(df)

    summarystats = summary_statistics_nsitzungen(df)
    summarystats.to_csv(args.out_basename + '_summary.csv')
    print(summarystats)
