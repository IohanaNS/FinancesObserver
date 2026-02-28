import unittest

import pandas as pd

from domain.classification import classify_description
from domain.deduplication import deduplicate_cross_bank_transactions
from core.constants import CROSS_BANK_CATEGORIES


class DataLogicTestCase(unittest.TestCase):
    def test_classify_prefers_longest_keyword_match(self):
        rules = {
            "Resgate": "Resgate Investimento",
            "Dinheiro guardado com resgate planejado": "Investimentos",
        }

        category = classify_description("Dinheiro guardado com resgate planejado", rules)

        self.assertEqual(category, "Investimentos")

    def test_deduplicate_cross_bank_removes_only_internal_duplicates(self):
        df = pd.DataFrame(
            [
                {
                    "Data": pd.Timestamp("2026-02-10"),
                    "Descrição": "Transferência A",
                    "Valor": -500.0,
                    "Tipo": "Saída",
                    "Categoria": "Transferência Entre Contas",
                    "Fonte": "Nubank",
                    "pluggy_id": "1",
                },
                {
                    "Data": pd.Timestamp("2026-02-10"),
                    "Descrição": "Transferência B",
                    "Valor": 500.0,
                    "Tipo": "Entrada",
                    "Categoria": "Transferência Entre Contas",
                    "Fonte": "Santander",
                    "pluggy_id": "2",
                },
                {
                    "Data": pd.Timestamp("2026-02-10"),
                    "Descrição": "Mercado",
                    "Valor": -500.0,
                    "Tipo": "Saída",
                    "Categoria": "Supermercado",
                    "Fonte": "Nubank",
                    "pluggy_id": "3",
                },
            ]
        )

        deduped = deduplicate_cross_bank_transactions(df, CROSS_BANK_CATEGORIES)

        self.assertEqual(len(deduped), 2)
        self.assertIn("Supermercado", deduped["Categoria"].tolist())
        self.assertNotIn("_date_str", deduped.columns)
        self.assertNotIn("_abs_val", deduped.columns)


if __name__ == "__main__":
    unittest.main()
