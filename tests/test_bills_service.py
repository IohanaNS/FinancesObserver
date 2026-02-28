import unittest

from services.bills_service import BillsService


class FakeBankingAdapter:
    def __init__(self):
        self.fetch_called = False
        self.cache_called = False

    def sync_all(self, date_from: str, date_to: str, categorize):
        return []

    def fetch_credit_card_info(self) -> list[dict]:
        self.fetch_called = True
        return [{"banco": "Nubank"}]

    def load_bills_cache(self) -> dict | None:
        self.cache_called = True
        return {"cards": []}

    def load_balances_cache(self) -> dict | None:
        return None

    def fetch_account_balances(self) -> list[dict]:
        return []

    def fetch_investments(self) -> list[dict]:
        return []

    def load_investments_cache(self) -> dict | None:
        return None

    def save_investments_goal(self, goal: float) -> None:
        return None

    def get_fontes(self) -> list[str]:
        return []


class BillsServiceTestCase(unittest.TestCase):
    def test_fetch_cards_delegates_to_banking_port(self):
        banking = FakeBankingAdapter()
        service = BillsService(banking=banking)

        result = service.fetch_cards()

        self.assertTrue(banking.fetch_called)
        self.assertEqual(result, [{"banco": "Nubank"}])

    def test_load_cached_cards_delegates_to_banking_port(self):
        banking = FakeBankingAdapter()
        service = BillsService(banking=banking)

        result = service.load_cached_cards()

        self.assertTrue(banking.cache_called)
        self.assertEqual(result, {"cards": []})


if __name__ == "__main__":
    unittest.main()
