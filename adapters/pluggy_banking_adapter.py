from collections.abc import Callable

from core.settings import PluggySettings, load_pluggy_settings
from pluggy_integration import fetch_credit_card_info, load_bills_cache, sync_all


class PluggyBankingAdapter:
    def __init__(self, settings: PluggySettings | None = None):
        self._settings = settings or load_pluggy_settings()

    def sync_all(
        self,
        date_from: str,
        date_to: str,
        categorize: Callable[[str], str | None],
    ) -> list[dict]:
        return sync_all(
            date_from=date_from,
            date_to=date_to,
            categorize=categorize,
            settings=self._settings,
        )

    def fetch_credit_card_info(self) -> list[dict]:
        return fetch_credit_card_info(settings=self._settings)

    def load_bills_cache(self) -> dict | None:
        return load_bills_cache(cache_file=self._settings.bills_cache_file)

    def get_fontes(self) -> list[str]:
        return self._settings.get_configured_fontes()
