from datetime import date
from io import BytesIO
from typing import Sequence

import pandas as pd

from core.constants import CATEGORY_INVESTMENTS, CATEGORY_SALARY, CATEGORY_SUBSCRIPTIONS
from core.models import FinanceKpis, SavingsSimulation
from ports import BankingPort, RulesDataPort, TransactionsDataPort


class FinanceService:
    def __init__(
        self,
        transactions: TransactionsDataPort,
        rules: RulesDataPort,
        banking: BankingPort,
    ):
        self._transactions = transactions
        self._rules = rules
        self._banking = banking

    def load_dataframe(self) -> pd.DataFrame:
        return self._transactions.load_dataframe()

    def get_fontes(self) -> list[str]:
        return self._banking.get_fontes()

    def get_categorias_list(self) -> list[str]:
        return self._rules.get_categorias_list()

    def get_category_icons(self) -> dict[str, str]:
        return self._rules.get_category_icons()

    def apply_filters(
        self,
        df: pd.DataFrame,
        date_range: Sequence[date],
        categories: list[str],
        fontes: list[str],
    ) -> pd.DataFrame:
        filtered = df.copy()
        if len(date_range) == 2:
            filtered = filtered[
                (filtered["Data"].dt.date >= date_range[0])
                & (filtered["Data"].dt.date <= date_range[1])
            ]
        if categories:
            filtered = filtered[filtered["Categoria"].isin(categories)]
        if fontes:
            filtered = filtered[filtered["Fonte"].isin(fontes)]
        return filtered

    def calculate_kpis(self, filtered_df: pd.DataFrame) -> FinanceKpis:
        real_expenses = self._transactions.get_real_expenses(filtered_df)
        total_income = filtered_df[filtered_df["Categoria"] == CATEGORY_SALARY]["Valor"].sum()
        total_real_expenses = real_expenses["Valor"].sum()
        total_invested = filtered_df[filtered_df["Categoria"] == CATEGORY_INVESTMENTS]["Valor"].sum()
        pct_salary = abs(total_real_expenses / total_income * 100) if total_income > 0 else 0
        return FinanceKpis(
            total_income=total_income,
            total_real_expenses=total_real_expenses,
            pct_salary=pct_salary,
            total_invested=total_invested,
        )

    def sync_transactions(
        self,
        df: pd.DataFrame,
        sync_from: date,
        sync_to: date,
    ) -> tuple[pd.DataFrame, int]:
        rules = self._rules.load_rules()
        transactions = self._banking.sync_all(
            date_from=sync_from.strftime("%Y-%m-%d"),
            date_to=sync_to.strftime("%Y-%m-%d"),
            categorize=lambda description: self._rules.classify(description, rules),
        )
        return self._transactions.add_synced_transactions(df, transactions)

    def fetch_account_balances(self) -> list[dict]:
        return self._banking.fetch_account_balances()

    def load_cached_balances(self) -> dict | None:
        return self._banking.load_balances_cache()

    def fetch_investments(self) -> list[dict]:
        return self._banking.fetch_investments()

    def load_cached_investments(self) -> dict | None:
        return self._banking.load_investments_cache()

    def save_investments_goal(self, goal: float, months: int | None = None) -> None:
        self._banking.save_investments_goal(goal, months)

    def estimate_investments_from_transactions(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Build an estimated investments snapshot from classified transactions.
        Useful when Pluggy does not expose dedicated investment accounts.
        """
        required_columns = {"Categoria", "Valor", "Fonte"}
        if df.empty or not required_columns.issubset(df.columns):
            return pd.DataFrame(columns=["Fonte", "Aportes", "Resgates", "Saldo Estimado"])

        investment_categories = {"Investimentos", "Investimento"}
        rescue_categories = {"Resgate Investimento"}
        mask = df["Categoria"].isin(investment_categories | rescue_categories)
        selected = df[mask].copy()
        if selected.empty:
            return pd.DataFrame(columns=["Fonte", "Aportes", "Resgates", "Saldo Estimado"])

        selected["Aporte"] = selected.apply(
            lambda row: abs(float(row["Valor"])) if row["Categoria"] in investment_categories else 0.0,
            axis=1,
        )
        selected["Resgate"] = selected.apply(
            lambda row: abs(float(row["Valor"])) if row["Categoria"] in rescue_categories else 0.0,
            axis=1,
        )

        grouped = (
            selected.groupby("Fonte", as_index=False)
            .agg(
                Aportes=("Aporte", "sum"),
                Resgates=("Resgate", "sum"),
            )
            .sort_values("Fonte")
        )
        grouped["Saldo Estimado"] = grouped["Aportes"] - grouped["Resgates"]
        return grouped.sort_values("Saldo Estimado", ascending=False)

    def get_summary_by_category(self, df: pd.DataFrame) -> pd.DataFrame:
        return self._transactions.get_summary_by_category(df)

    def get_summary_by_fonte(self, df: pd.DataFrame) -> pd.DataFrame:
        return self._transactions.get_summary_by_fonte(df)

    def get_daily_expenses(self, df: pd.DataFrame) -> pd.DataFrame:
        return self._transactions.get_daily_expenses(df)

    def get_export_columns(self, df: pd.DataFrame) -> list[str]:
        return [column for column in df.columns if column != "pluggy_id"]

    def build_csv_export(self, df: pd.DataFrame) -> bytes:
        export_columns = self.get_export_columns(df)
        return df[export_columns].to_csv(index=False).encode("utf-8")

    def build_excel_export(self, df: pd.DataFrame) -> bytes:
        export_columns = self.get_export_columns(df)
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            df[export_columns].to_excel(writer, index=False, sheet_name="Transações")
        return buffer.getvalue()

    def get_subscription_expenses(self, df: pd.DataFrame) -> pd.DataFrame:
        return df[df["Categoria"] == CATEGORY_SUBSCRIPTIONS].copy()

    def calculate_savings_simulation(
        self,
        summary_by_category: pd.DataFrame,
        selected_categories: list[str],
        cut_pct: int,
        travel_goal: float,
        saved_so_far: float,
    ) -> SavingsSimulation | None:
        if not selected_categories or summary_by_category.empty:
            return None

        potential = summary_by_category[
            summary_by_category["Categoria"].isin(selected_categories)
        ]["Total"].sum()
        monthly_saving = potential * cut_pct / 100
        yearly_saving = monthly_saving * 12

        months_to_goal: float | None = None
        if travel_goal > 0 and monthly_saving > 0:
            months_to_goal = (travel_goal - saved_so_far) / monthly_saving

        return SavingsSimulation(
            monthly_saving=monthly_saving,
            yearly_saving=yearly_saving,
            months_to_goal=months_to_goal,
        )

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
        return self._transactions.add_manual_transaction(
            df=df,
            transaction_date=transaction_date,
            description=description,
            value=value,
            tx_type=tx_type,
            category=category,
            source=source,
        )

    def delete_manual_transaction(self, df: pd.DataFrame, index: int) -> pd.DataFrame:
        return self._transactions.delete_manual_transaction(df, index)

    def load_rules(self) -> dict:
        return self._rules.load_rules()

    def add_rule(self, keyword: str, category: str) -> dict:
        return self._rules.add_rule(keyword, category)

    def remove_rule(self, keyword: str) -> dict:
        return self._rules.remove_rule(keyword)

    def reclassify_all(self, df: pd.DataFrame) -> pd.DataFrame:
        return self._rules.reclassify_all(df)

    def classify(self, description: str) -> str | None:
        return self._rules.classify(description)

    def save_dataframe(self, df: pd.DataFrame) -> None:
        self._transactions.save_dataframe(df)

    def add_categoria(self, name: str, icon: str, gasto_real: bool) -> None:
        self._rules.add_categoria(name, icon, gasto_real)
