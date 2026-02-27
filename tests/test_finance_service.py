from datetime import date
import unittest

import pandas as pd

from services.finance_service import FinanceService


class FakeFinanceRepository:
    def __init__(self):
        self.rules = {"uber": "Transporte"}
        self.last_synced_payload: list[dict] | None = None

    def load_dataframe(self) -> pd.DataFrame:
        return pd.DataFrame()

    def get_fontes(self) -> list[str]:
        return ["Nubank"]

    def get_categorias_list(self) -> list[str]:
        return ["Transporte", "Outros", "Salário", "Investimentos"]

    def get_category_icons(self) -> dict[str, str]:
        return {"Transporte": "🚗"}

    def get_real_expenses(self, df: pd.DataFrame) -> pd.DataFrame:
        return df[(df["Valor"] < 0) & (df["Categoria"] != "Investimentos")].copy()

    def get_summary_by_category(self, df: pd.DataFrame) -> pd.DataFrame:
        return pd.DataFrame()

    def get_summary_by_fonte(self, df: pd.DataFrame) -> pd.DataFrame:
        return pd.DataFrame()

    def get_daily_expenses(self, df: pd.DataFrame) -> pd.DataFrame:
        return pd.DataFrame()

    def add_synced_transactions(
        self,
        df: pd.DataFrame,
        transactions: list[dict],
    ) -> tuple[pd.DataFrame, int]:
        self.last_synced_payload = transactions
        return df, len(transactions)

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
        return df

    def delete_manual_transaction(self, df: pd.DataFrame, index: int) -> pd.DataFrame:
        return df

    def load_rules(self) -> dict:
        return self.rules

    def add_rule(self, keyword: str, category: str) -> dict:
        self.rules[keyword] = category
        return self.rules

    def remove_rule(self, keyword: str) -> dict:
        self.rules.pop(keyword, None)
        return self.rules

    def reclassify_all(self, df: pd.DataFrame) -> pd.DataFrame:
        return df

    def classify(self, description: str, rules: dict | None = None) -> str | None:
        active_rules = rules or self.rules
        desc = description.lower()
        for keyword, category in active_rules.items():
            if keyword in desc:
                return category
        return None

    def add_categoria(self, name: str, icon: str, gasto_real: bool) -> None:
        return None


class FakeBankingAdapter:
    def __init__(self):
        self.last_date_from: str | None = None
        self.last_date_to: str | None = None

    def sync_all(self, date_from: str, date_to: str, categorize):
        self.last_date_from = date_from
        self.last_date_to = date_to
        return [
            {"Descrição": "Uber Trip", "Categoria": categorize("Uber Trip") or "Outros"},
            {"Descrição": "Compra qualquer", "Categoria": categorize("Compra qualquer") or "Outros"},
        ]

    def fetch_credit_card_info(self) -> list[dict]:
        return []

    def load_bills_cache(self) -> dict | None:
        return None


class FinanceServiceTestCase(unittest.TestCase):
    def test_sync_transactions_applies_rules_before_merge(self):
        repository = FakeFinanceRepository()
        banking = FakeBankingAdapter()
        service = FinanceService(transactions=repository, rules=repository, banking=banking)

        df = pd.DataFrame()
        _, count = service.sync_transactions(df, date(2026, 1, 1), date(2026, 1, 31))

        self.assertEqual(count, 2)
        self.assertEqual(banking.last_date_from, "2026-01-01")
        self.assertEqual(banking.last_date_to, "2026-01-31")
        self.assertIsNotNone(repository.last_synced_payload)
        assert repository.last_synced_payload is not None
        self.assertEqual(repository.last_synced_payload[0]["Categoria"], "Transporte")
        self.assertEqual(repository.last_synced_payload[1]["Categoria"], "Outros")

    def test_calculate_kpis_uses_real_expenses_from_repository(self):
        repository = FakeFinanceRepository()
        service = FinanceService(
            transactions=repository,
            rules=repository,
            banking=FakeBankingAdapter(),
        )

        filtered_df = pd.DataFrame(
            [
                {"Categoria": "Salário", "Valor": 5000.0},
                {"Categoria": "Transporte", "Valor": -100.0},
                {"Categoria": "Investimentos", "Valor": -200.0},
            ]
        )

        kpis = service.calculate_kpis(filtered_df)

        self.assertEqual(kpis.total_income, 5000.0)
        self.assertEqual(kpis.total_real_expenses, -100.0)
        self.assertEqual(kpis.total_invested, -200.0)
        self.assertAlmostEqual(kpis.pct_salary, 2.0)

    def test_calculate_savings_simulation_returns_projection(self):
        repository = FakeFinanceRepository()
        service = FinanceService(
            transactions=repository,
            rules=repository,
            banking=FakeBankingAdapter(),
        )
        summary = pd.DataFrame(
            [
                {"Categoria": "Transporte", "Total": 300.0},
                {"Categoria": "Outros", "Total": 100.0},
            ]
        )

        simulation = service.calculate_savings_simulation(
            summary_by_category=summary,
            selected_categories=["Transporte"],
            cut_pct=30,
            travel_goal=1500.0,
            saved_so_far=300.0,
        )

        assert simulation is not None
        self.assertEqual(simulation.monthly_saving, 90.0)
        self.assertEqual(simulation.yearly_saving, 1080.0)
        self.assertAlmostEqual(simulation.months_to_goal or 0.0, 13.3333333333, places=4)

    def test_build_exports_excludes_pluggy_id(self):
        repository = FakeFinanceRepository()
        service = FinanceService(
            transactions=repository,
            rules=repository,
            banking=FakeBankingAdapter(),
        )
        df = pd.DataFrame(
            [
                {
                    "Data": pd.Timestamp("2026-02-01"),
                    "Descrição": "Teste",
                    "Valor": -10.0,
                    "Tipo": "Saída",
                    "Categoria": "Outros",
                    "Fonte": "Nubank",
                    "pluggy_id": "abc-123",
                }
            ]
        )

        csv_bytes = service.build_csv_export(df)
        csv_text = csv_bytes.decode("utf-8")
        self.assertIn("Descrição", csv_text)
        self.assertNotIn("pluggy_id", csv_text)

        excel_bytes = service.build_excel_export(df)
        self.assertTrue(excel_bytes.startswith(b"PK"))


if __name__ == "__main__":
    unittest.main()
