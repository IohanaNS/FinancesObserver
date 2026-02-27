import os

import pandas as pd

from core.constants import CROSS_BANK_CATEGORIES, TRANSACTION_COLUMNS
from domain.analytics import (
    filter_real_expenses,
    summarize_by_source,
    summarize_daily_expenses,
    summarize_expenses_by_category,
)
from domain.classification import (
    classify_description,
    classify_exact_description,
    normalize_text,
    reclassify_dataframe,
)
from domain.deduplication import deduplicate_cross_bank_transactions
from repositories.config_repository import ConfigRepository

COLUMNS = TRANSACTION_COLUMNS


class TransactionsRepository:
    def __init__(self, data_file: str, config_repository: ConfigRepository):
        self._data_file = data_file
        self._config_repository = config_repository

    def _normalize(self, text: str) -> str:
        return normalize_text(text)

    def classify(self, description: str, rules: dict | None = None) -> str | None:
        if rules is None:
            rules = self._config_repository.load_rules()
        return classify_description(description, rules)

    def _classify_exact(self, description: str, rules: dict) -> str | None:
        return classify_exact_description(description, rules)

    def reclassify_all(self, df: pd.DataFrame) -> pd.DataFrame:
        rules = self._config_repository.load_rules()
        df = reclassify_dataframe(df, rules)
        self.save_data(df)
        return df

    def _ensure_dtypes(self, df: pd.DataFrame) -> pd.DataFrame:
        """Ensure Data column is datetime even on empty DataFrames."""
        if not pd.api.types.is_datetime64_any_dtype(df["Data"]):
            df["Data"] = pd.to_datetime(df["Data"])
        if "pluggy_id" not in df.columns:
            df["pluggy_id"] = None
        return df

    def load_data(self) -> pd.DataFrame:
        if os.path.exists(self._data_file):
            df = pd.read_csv(self._data_file, parse_dates=["Data"])
            return self._ensure_dtypes(df)
        # First run: create empty CSV
        df = pd.DataFrame(columns=COLUMNS)
        df["Data"] = pd.to_datetime(df["Data"])
        self.save_data(df)
        return df

    def save_data(self, df: pd.DataFrame) -> None:
        df.to_csv(self._data_file, index=False)

    def add_transaction(
        self,
        df: pd.DataFrame,
        transaction_date: str,
        descricao: str,
        valor: float,
        tipo: str,
        categoria: str,
        fonte: str,
    ) -> pd.DataFrame:
        if not categoria or categoria == "Outros":
            auto_cat = self.classify(descricao)
            if auto_cat:
                categoria = auto_cat

        new_row = pd.DataFrame(
            [
                {
                    "Data": pd.to_datetime(transaction_date),
                    "Descrição": descricao,
                    "Valor": valor if tipo == "Entrada" else -abs(valor),
                    "Tipo": tipo,
                    "Categoria": categoria,
                    "Fonte": fonte,
                }
            ]
        )
        df = pd.concat([df, new_row], ignore_index=True)
        df = df.sort_values("Data").reset_index(drop=True)
        self.save_data(df)
        return df

    def delete_transaction(self, df: pd.DataFrame, index: int) -> pd.DataFrame:
        df = df.drop(index).reset_index(drop=True)
        self.save_data(df)
        return df

    def get_real_expenses(self, df: pd.DataFrame) -> pd.DataFrame:
        categories = self._config_repository.get_real_expense_categories()
        return filter_real_expenses(df, categories)

    def get_summary_by_category(self, df: pd.DataFrame) -> pd.DataFrame:
        expenses = self.get_real_expenses(df)
        return summarize_expenses_by_category(expenses)

    def get_summary_by_fonte(self, df: pd.DataFrame) -> pd.DataFrame:
        return summarize_by_source(df)

    def get_daily_expenses(self, df: pd.DataFrame) -> pd.DataFrame:
        expenses = self.get_real_expenses(df)
        return summarize_daily_expenses(expenses)

    def add_synced_transactions(
        self,
        df: pd.DataFrame,
        transactions: list[dict],
    ) -> tuple[pd.DataFrame, int]:
        """
        Merge Pluggy transactions into the DataFrame, deduplicating by pluggy_id.
        Returns (updated_df, count_of_new_transactions).
        """
        if not transactions:
            return df, 0

        if "pluggy_id" not in df.columns:
            df["pluggy_id"] = None

        existing_ids = set(df["pluggy_id"].dropna().astype(str))
        new_rows = [tx for tx in transactions if tx["pluggy_id"] not in existing_ids]

        if not new_rows:
            return df, 0

        new_df = pd.DataFrame(new_rows)
        new_df["Data"] = pd.to_datetime(new_df["Data"])
        df = pd.concat([df, new_df], ignore_index=True)
        df = self.deduplicate_cross_bank(df)
        df = df.sort_values("Data").reset_index(drop=True)
        self.save_data(df)
        return df, len(new_rows)

    def deduplicate_cross_bank(self, df: pd.DataFrame) -> pd.DataFrame:
        return deduplicate_cross_bank_transactions(df, CROSS_BANK_CATEGORIES)
