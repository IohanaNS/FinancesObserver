from datetime import date

import pandas as pd

from core.constants import DATA_FILE, RULES_FILE
from repositories import ConfigRepository, TransactionsRepository


class TransactionsDataAdapter:
    def __init__(
        self,
        data_file: str = DATA_FILE,
        rules_file: str = RULES_FILE,
        config_repository: ConfigRepository | None = None,
        transactions_repository: TransactionsRepository | None = None,
    ):
        self._config_repository = config_repository or ConfigRepository(rules_file)
        self._transactions_repository = transactions_repository or TransactionsRepository(
            data_file,
            self._config_repository,
        )

    def load_dataframe(self) -> pd.DataFrame:
        return self._transactions_repository.load_data()

    def get_real_expenses(self, df: pd.DataFrame) -> pd.DataFrame:
        return self._transactions_repository.get_real_expenses(df)

    def get_summary_by_category(self, df: pd.DataFrame) -> pd.DataFrame:
        return self._transactions_repository.get_summary_by_category(df)

    def get_summary_by_fonte(self, df: pd.DataFrame) -> pd.DataFrame:
        return self._transactions_repository.get_summary_by_fonte(df)

    def get_daily_expenses(self, df: pd.DataFrame) -> pd.DataFrame:
        return self._transactions_repository.get_daily_expenses(df)

    def add_synced_transactions(
        self,
        df: pd.DataFrame,
        transactions: list[dict],
    ) -> tuple[pd.DataFrame, int]:
        return self._transactions_repository.add_synced_transactions(df, transactions)

    def add_manual_transaction(
        self,
        df: pd.DataFrame,
        transaction_date: date,
        description: str,
        value: float,
        tx_type: str,
        category: str,
        source: str,
    ) -> pd.DataFrame:
        return self._transactions_repository.add_transaction(
            df=df,
            transaction_date=str(transaction_date),
            descricao=description,
            valor=value,
            tipo=tx_type,
            categoria=category,
            fonte=source,
        )

    def delete_manual_transaction(self, df: pd.DataFrame, index: int) -> pd.DataFrame:
        return self._transactions_repository.delete_transaction(df, index)

    def save_dataframe(self, df: pd.DataFrame) -> None:
        self._transactions_repository.save_data(df)
