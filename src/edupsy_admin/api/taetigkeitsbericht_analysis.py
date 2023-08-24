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
    concat_df = concat_df.astype('category')
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


def summary_statistics(df: pd.DataFrame) -> pd.DataFrame:
    summarystats = df.describe()
    summarystats.loc['sum',:]=df.agg(func='sum', axis=0, numeric_only=True)
    return summarystats

def nsessions_to_hours(nsessions:float) -> float:
    return nsessions*45/60

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

    summarystats = summary_statistics(df)
    summarystats.to_csv(args.out_basename + '_summary.csv')
    print(summarystats)
