import pandas as pd


def filter_real_expenses(df: pd.DataFrame, real_categories: set[str]) -> pd.DataFrame:
    return df[
        (df["Categoria"].isin(real_categories))
        & (df["Valor"] < 0)
    ].copy()


def summarize_expenses_by_category(expenses: pd.DataFrame) -> pd.DataFrame:
    if expenses.empty:
        return pd.DataFrame(columns=["Categoria", "Total", "Percentual"])
    summary = (
        expenses.groupby("Categoria")["Valor"]
        .sum()
        .abs()
        .sort_values(ascending=False)
        .reset_index()
    )
    summary.columns = ["Categoria", "Total"]
    summary["Percentual"] = summary["Total"] / summary["Total"].sum()
    return summary


def summarize_by_source(df: pd.DataFrame) -> pd.DataFrame:
    entradas = df[df["Valor"] > 0].groupby("Fonte")["Valor"].sum()
    saidas = df[df["Valor"] < 0].groupby("Fonte")["Valor"].sum().abs()
    summary = pd.DataFrame({"Entradas": entradas, "Saídas": saidas}).fillna(0)
    summary["Saldo"] = summary["Entradas"] - summary["Saídas"]
    return summary.reset_index()


def summarize_daily_expenses(expenses: pd.DataFrame) -> pd.DataFrame:
    if expenses.empty:
        return pd.DataFrame(columns=["Data", "Total"])
    daily = expenses.groupby(expenses["Data"].dt.date)["Valor"].sum().abs().reset_index()
    daily.columns = ["Data", "Total"]
    return daily
