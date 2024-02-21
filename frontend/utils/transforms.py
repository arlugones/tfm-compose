import pandas as pd
import numpy as np
from typing import List, Dict
import base64
import io
import re
from janitor import clean_names
from sklearn.cluster import KMeans

# Commons
def parse_contents(contents: str) -> pd.DataFrame:
        _, content_string = contents.split(',')

        decoded = base64.b64decode(content_string)
        try:
            df = pd.read_csv(io.BytesIO(decoded), na_values=['N', 'NULL', 'P'], keep_default_na=False, sep=';')
        except:
            return None

        return df
    
def split_map(df: pd.DataFrame, group_col_list: str | List[str]) -> Dict[str, pd.DataFrame]:
    grouped_df = df.groupby(group_col_list)
    return [grouped_df.get_group(x) for x in grouped_df.groups]

def split_base(df: pd.DataFrame, group_col_list: str | List[str]) -> Dict[str, pd.DataFrame]:
    grouped_df = df.groupby(group_col_list, sort=False)
    return {f'{grado}_{instrumento}': datos for (grado, instrumento), datos in grouped_df}

def slice_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    
    append_cols = list(df.columns[df.columns.str.match(r'^[Pp]\d+')])
    const_cols = ['grado', 'instrumento']
    const_cols.extend(append_cols)
    return df.loc[:, const_cols]

def make_clean_string(value: str) -> str:
    value = value.lower().replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u").replace(" ", "_").strip()
    return re.sub(r'\W+', '', value)


def extract_grade(filename: List[str]):
    match = re.search("(?<=DAI_MapaSEST)\w+(?=\_)", filename) 
    if match:
        return match.group()
    else:
        return ''
    
def remove_empty_cols(map_df: pd.DataFrame) -> pd.DataFrame:
    return map_df.remove_empty()

def sort_col_values(map_df: pd.DataFrame) -> pd.DataFrame:
    sort_col = map_df.columns[map_df.columns.str.match('^f')].values[0]
    return map_df.sort_values(sort_col)

def map_col_select(map_file: pd.DataFrame) -> pd.DataFrame:
    _vect_col = ['codigo', 'nivel_1', 'piloto']
    _vect_col.extend([*filter(lambda x: re.match(r'^f\d+', x), map_file.clean_names().columns.tolist())])
    _map = map_file.clean_names().filter(_vect_col)
    return _map

def map_processing(map_dict: Dict[str, str]) -> Dict[str, pd.DataFrame]:
    
    mapas = {k: parse_contents(v) for k, v in map_dict.items()}
    mapas = {k: map_col_select(v) for k, v  in mapas.items()}

    mapas_clean = {k: v.loc[(v['piloto'] != 'SI') & (~v['nivel_1'].str.startswith('Prueba'))] for k, v in mapas.items()}
    for k in mapas_clean.keys():
        mapas_clean[k]['nivel_1'] = mapas_clean[k]['nivel_1'].replace(r'Matemática$', r'Matemáticas', regex=True)
        mapas_clean[k]['nivel_1'] = mapas_clean[k]['nivel_1'].replace(r'Ciencias Sociales$', r'Estudios Sociales', regex=True)


    mapas_clean = {k: split_map(v, 'nivel_1') for k, v in mapas_clean.items()}
    mapas_clean = {k: [remove_empty_cols(df) for df in v] for k, v in mapas_clean.items()}
    
    mapas_sorted = {k: [sort_col_values(df) for df in v] for k, v in mapas_clean.items()}
    result = {
        f"{k}_{df['nivel_1'].iloc[0]}": df['codigo'].tolist()
        for k, v in mapas_sorted.items()
        for df in v
    }

    return {make_clean_string(re.sub(r'_\d+', '', k)): [x.strip() for x in v] for k, v in result.items()}

def base_processing(base_file: pd.DataFrame) -> Dict[str, pd.DataFrame]:

    _base = parse_contents(base_file)
    
    ## Limpiando grado e instrumento
    conditions = [_base['grado'] == '3ro BGU', _base['grado'] == '5to', _base['grado'] == '8vo', _base['grado'] == '1ro BGU']
    choices = ['bachillerato', 'elemental', 'media', 'superior']
    _base['grado'] = np.select(conditions, choices, np.nan)
    _base['instrumento'] = _base['instrumento'].apply(lambda x: make_clean_string(x))

    _base = slice_dataframe(_base)
    _base = split_base(_base, ['grado', 'instrumento'])

    return _base

def clustering(df: pd.DataFrame, n_clusters: int, x: str, y: str) -> pd.DataFrame:
    df.set_index('id_item', inplace=True)
    df = df.loc[:, [x, y]]
    kmeans = KMeans(n_clusters=max(n_clusters, 1))
    kmeans.fit(df)
    df['cluster'] = kmeans.labels_
    return df

if __name__ == "__main__":
    raise ImportError("This module is not meant to be run!")