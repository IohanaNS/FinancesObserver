from ports import BankingPort


class BillsService:
    def __init__(self, banking: BankingPort):
        self._banking = banking

    def load_cached_cards(self) -> dict | None:
        return self._banking.load_bills_cache()

    def fetch_cards(self) -> list[dict]:
        return self._banking.fetch_credit_card_info()
