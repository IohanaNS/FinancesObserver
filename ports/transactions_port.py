from datetime import date
from typing import Protocol

import pandas as pd


class TransactionsDataPort(Protocol):
    def load_dataframe(self) -> pd.DataFrame: ...

    def get_real_expenses(self, df: pd.DataFrame) -> pd.DataFrame: ...

    def get_summary_by_category(self, df: pd.DataFrame) -> pd.DataFrame: ...

    def get_summary_by_fonte(self, df: pd.DataFrame) -> pd.DataFrame: ...

    def get_daily_expenses(self, df: pd.DataFrame) -> pd.DataFrame: ...

    def add_synced_transactions(
        self,
        df: pd.DataFrame,
        transactions: list[dict],
    ) -> tuple[pd.DataFrame, int]: ...

    def add_manual_transaction(
        self,
        df: pd.DataFrame,
        transaction_date: date,
        description: str,
        value: float,
        tx_type: str,
        category: str,
        source: str,
    ) -> pd.DataFrame: ...

    def delete_manual_transaction(self, df: pd.DataFrame, index: int) -> pd.DataFrame: ...

    def save_dataframe(self, df: pd.DataFrame) -> None: ...
