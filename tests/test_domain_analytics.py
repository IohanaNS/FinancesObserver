import unittest

import pandas as pd

from domain.analytics import (
    filter_real_expenses,
    summarize_by_source,
    summarize_daily_expenses,
    summarize_expenses_by_category,
)


class DomainAnalyticsTestCase(unittest.TestCase):
    def test_filter_real_expenses_uses_categories_and_negative_values(self):
        df = pd.DataFrame(
            [
                {"Categoria": "Supermercado", "Valor": -100.0},
                {"Categoria": "Supermercado", "Valor": 100.0},
                {"Categoria": "Investimentos", "Valor": -200.0},
            ]
        )

        result = filter_real_expenses(df, {"Supermercado"})

        self.assertEqual(len(result), 1)
        self.assertEqual(result.iloc[0]["Valor"], -100.0)

    def test_summarize_expenses_by_category_returns_totals_and_percentage(self):
        expenses = pd.DataFrame(
            [
                {"Categoria": "Supermercado", "Valor": -100.0},
                {"Categoria": "Transporte", "Valor": -50.0},
            ]
        )

        summary = summarize_expenses_by_category(expenses)

        self.assertEqual(summary.iloc[0]["Categoria"], "Supermercado")
        self.assertEqual(summary.iloc[0]["Total"], 100.0)
        self.assertAlmostEqual(summary["Percentual"].sum(), 1.0)

    def test_summarize_by_source_calculates_balance(self):
        df = pd.DataFrame(
            [
                {"Fonte": "Nubank", "Valor": 1000.0},
                {"Fonte": "Nubank", "Valor": -300.0},
                {"Fonte": "Santander", "Valor": -100.0},
            ]
        )

        summary = summarize_by_source(df).set_index("Fonte")

        self.assertEqual(summary.loc["Nubank", "Entradas"], 1000.0)
        self.assertEqual(summary.loc["Nubank", "Saídas"], 300.0)
        self.assertEqual(summary.loc["Nubank", "Saldo"], 700.0)

    def test_summarize_daily_expenses_groups_by_day(self):
        expenses = pd.DataFrame(
            [
                {"Data": pd.Timestamp("2026-02-10"), "Valor": -100.0},
                {"Data": pd.Timestamp("2026-02-10"), "Valor": -50.0},
                {"Data": pd.Timestamp("2026-02-11"), "Valor": -20.0},
            ]
        )

        daily = summarize_daily_expenses(expenses)

        self.assertEqual(len(daily), 2)
        self.assertEqual(float(daily.iloc[0]["Total"]), 150.0)
        self.assertEqual(float(daily.iloc[1]["Total"]), 20.0)


if __name__ == "__main__":
    unittest.main()
