# FILE
import config
# MODULE
import pandas as pd
from collections import Iterable


def pre_processing(df: pd.DataFrame, column_names: Iterable[str], use_Edge: bool = False) -> pd.DataFrame:
    if use_Edge:
        for col_name in column_names:
            df[col_name] = df[col_name].astype(str)
    else:
        for col_name in column_names:
            df[col_name] = df[col_name].astype(str)
    return df


def processing(df: pd.DataFrame) -> pd.DataFrame:
    return


def post_processing(df: pd.DataFrame, column_names: Iterable[str], use_Edge: bool = False) -> pd.DataFrame:
    return