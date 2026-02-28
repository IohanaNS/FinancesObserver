import unittest

import pandas as pd

from presentation.tabs.transactions_tab import _apply_local_filters, _normalize_tipo_column


class TransactionsTabHelpersTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.base_df = pd.DataFrame(
            [
                {
                    "Data": pd.Timestamp("2026-02-01"),
                    "Descrição": "Mercado do mês",
                    "Valor": -300.0,
                    "Categoria": "Supermercado",
                    "Fonte": "Nubank",
                },
                {
                    "Data": pd.Timestamp("2026-02-02"),
                    "Descrição": "Salário",
                    "Valor": 5000.0,
                    "Categoria": "Salário",
                    "Fonte": "Santander",
                },
                {
                    "Data": pd.Timestamp("2026-02-03"),
                    "Descrição": "Compra aleatória",
                    "Valor": -50.0,
                    "Categoria": "Outros",
                    "Fonte": "Nubank",
                },
                {
                    "Data": pd.Timestamp("2026-02-04"),
                    "Descrição": "Pix ajuste",
                    "Valor": -120.0,
                    "Categoria": None,
                    "Fonte": "Inter",
                },
            ],
            index=[10, 11, 12, 13],
        )

    def test_normalize_tipo_derives_from_valor_when_column_missing(self):
        normalized = _normalize_tipo_column(self.base_df)

        self.assertEqual(normalized.loc[10, "Tipo"], "Saída")
        self.assertEqual(normalized.loc[11, "Tipo"], "Entrada")

    def test_normalize_tipo_replaces_invalid_values_and_keeps_valid(self):
        with_tipo = self.base_df.copy()
        with_tipo["Tipo"] = ["Inválido", "Entrada", "", "Saída"]

        normalized = _normalize_tipo_column(with_tipo)

        self.assertEqual(normalized.loc[10, "Tipo"], "Saída")
        self.assertEqual(normalized.loc[11, "Tipo"], "Entrada")
        self.assertEqual(normalized.loc[12, "Tipo"], "Saída")
        self.assertEqual(normalized.loc[13, "Tipo"], "Saída")

    def test_apply_local_filters_respects_query_filters_and_sort(self):
        normalized = _normalize_tipo_column(self.base_df)

        filtered = _apply_local_filters(
            normalized,
            query="compra",
            types=["Saída"],
            categories=["Outros", "Supermercado"],
            sources=["Nubank", "Inter"],
            min_abs_value=10.0,
            max_abs_value=400.0,
            uncategorized_only=False,
            sort_option="Maior valor absoluto",
        )

        self.assertEqual(filtered.index.tolist(), [12])
        self.assertEqual(filtered.iloc[0]["Descrição"], "Compra aleatória")

    def test_apply_local_filters_uncategorized_only_matches_outros_and_none(self):
        normalized = _normalize_tipo_column(self.base_df)

        filtered = _apply_local_filters(
            normalized,
            query="",
            types=["Entrada", "Saída"],
            categories=["Supermercado", "Salário", "Outros", "Sem categoria"],
            sources=["Nubank", "Santander", "Inter"],
            min_abs_value=0.0,
            max_abs_value=6000.0,
            uncategorized_only=True,
            sort_option="Data (mais antiga)",
        )

        self.assertEqual(filtered.index.tolist(), [12, 13])


if __name__ == "__main__":
    unittest.main()
