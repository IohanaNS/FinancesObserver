from datetime import timedelta

import pandas as pd
from pymongo.database import Database

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
from repositories.mongo_config_repository import MongoConfigRepository

COLUMNS = TRANSACTION_COLUMNS


class MongoTransactionsRepository:
    """MongoDB-backed replacement for TransactionsRepository (CSV file)."""

    COLLECTION = "transactions"

    def __init__(self, db: Database, config_repository: MongoConfigRepository):
        self._col = db[self.COLLECTION]
        self._config_repository = config_repository
        self._ensure_indexes()

    def _ensure_indexes(self) -> None:
        self._col.create_index("pluggy_id", sparse=True)
        self._col.create_index("Data")

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
        if "categoria_manual" not in df.columns:
            df["categoria_manual"] = False
        return df

    def _docs_to_dataframe(self, docs: list[dict]) -> pd.DataFrame:
        """Convert MongoDB documents to a DataFrame with correct types."""
        for doc in docs:
            doc.pop("_id", None)
        if not docs:
            df = pd.DataFrame(columns=COLUMNS)
            df["Data"] = pd.to_datetime(df["Data"])
            return df
        df = pd.DataFrame(docs)
        for col in COLUMNS:
            if col not in df.columns:
                df[col] = None
        return self._ensure_dtypes(df)

    def _dataframe_to_docs(self, df: pd.DataFrame) -> list[dict]:
        """Convert DataFrame rows to MongoDB documents."""
        records = df.copy()
        records["Data"] = records["Data"].dt.strftime("%Y-%m-%d %H:%M:%S")
        return records.to_dict(orient="records")

    def load_data(self) -> pd.DataFrame:
        docs = list(self._col.find())
        return self._docs_to_dataframe(docs)

    def save_data(self, df: pd.DataFrame) -> None:
        """Replace all transactions with the current DataFrame contents."""
        docs = self._dataframe_to_docs(df)
        self._col.delete_many({})
        if docs:
            self._col.insert_many(docs)

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
        Merge Pluggy transactions into the DataFrame.
        - Skips transactions whose pluggy_id already exists.
        - If a manual entry (no pluggy_id) with same date and exact value exists,
          links it to the Pluggy transaction instead of creating a duplicate.
        Returns (updated_df, count_of_new_rows_added).
        """
        if not transactions:
            return df, 0

        if "pluggy_id" not in df.columns:
            df["pluggy_id"] = None

        existing_ids = set(df["pluggy_id"].dropna().astype(str))
        new_rows: list[dict] = []

        linked_manual_indices: set[int] = set()

        for tx in transactions:
            if tx["pluggy_id"] in existing_ids:
                continue

            tx_date = pd.to_datetime(tx["Data"])
            tx_valor = round(float(tx["Valor"]), 2)
            date_lo = tx_date - timedelta(days=2)
            date_hi = tx_date + timedelta(days=2)

            manual_mask = (
                df["pluggy_id"].isna()
                & (df["Data"] >= date_lo)
                & (df["Data"] <= date_hi)
                & (df["Valor"].round(2) == tx_valor)
                & ~df.index.isin(linked_manual_indices)
            )
            if manual_mask.any():
                match_idx = df[manual_mask].index[0]
                df.at[match_idx, "pluggy_id"] = tx["pluggy_id"]
                existing_ids.add(tx["pluggy_id"])
                linked_manual_indices.add(match_idx)
            else:
                new_rows.append(tx)
                existing_ids.add(tx["pluggy_id"])

        if new_rows:
            new_df = pd.DataFrame(new_rows)
            new_df["Data"] = pd.to_datetime(new_df["Data"])
            df = pd.concat([df, new_df], ignore_index=True)

        df = self.deduplicate_cross_bank(df)
        df = df.sort_values("Data").reset_index(drop=True)
        self.save_data(df)
        return df, len(new_rows)

    def deduplicate_cross_bank(self, df: pd.DataFrame) -> pd.DataFrame:
        return deduplicate_cross_bank_transactions(df, CROSS_BANK_CATEGORIES)
