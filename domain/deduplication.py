from collections.abc import Hashable

import pandas as pd


def deduplicate_cross_bank_transactions(
    df: pd.DataFrame,
    categories: set[str],
) -> pd.DataFrame:
    """
    Remove cross-bank duplicates: same date + same absolute value + different sources.
    Only applies to internal movement categories (card payments, transfers, etc.).
    Keeps the first occurrence and drops the rest.
    """
    if df.empty:
        return df

    result = df.copy()
    result["_date_str"] = result["Data"].dt.strftime("%Y-%m-%d")
    result["_abs_val"] = result["Valor"].abs()

    to_drop: list[Hashable] = []
    seen: set[tuple[str, float]] = set()

    for idx, row in result.iterrows():
        if row["Categoria"] not in categories:
            continue

        key = (str(row["_date_str"]), float(row["_abs_val"]))
        if key in seen:
            to_drop.append(idx)
        else:
            seen.add(key)

    if to_drop:
        result = result.drop(index=to_drop).reset_index(drop=True)
    return result.drop(columns=["_date_str", "_abs_val"])
