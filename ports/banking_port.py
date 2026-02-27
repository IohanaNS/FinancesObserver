from collections.abc import Callable
from typing import Protocol


class BankingPort(Protocol):
    def sync_all(
        self,
        date_from: str,
        date_to: str,
        categorize: Callable[[str], str | None],
    ) -> list[dict]: ...

    def fetch_credit_card_info(self) -> list[dict]: ...

    def load_bills_cache(self) -> dict | None: ...
