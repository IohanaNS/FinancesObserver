from dataclasses import dataclass

from dotenv import load_dotenv
import os

from core.constants import BILLS_CACHE_FILE


@dataclass(frozen=True)
class PluggySettings:
    base_url: str
    client_id: str | None
    client_secret: str | None
    item_map: dict[str, str]
    bills_cache_file: str

    @property
    def has_credentials(self) -> bool:
        return bool(self.client_id and self.client_secret)


def load_pluggy_settings() -> PluggySettings:
    load_dotenv()

    item_map: dict[str, str] = {}
    nubank_item_id = os.getenv("PLUGGY_ITEM_ID_NUBANK", "").strip()
    if nubank_item_id:
        item_map[nubank_item_id] = "Nubank"

    santander_item_id = os.getenv("PLUGGY_ITEM_ID_SANTANDER", "").strip()
    if santander_item_id:
        item_map[santander_item_id] = "Santander"

    return PluggySettings(
        base_url=os.getenv("PLUGGY_BASE_URL", "https://api.pluggy.ai"),
        client_id=os.getenv("PLUGGY_CLIENT_ID"),
        client_secret=os.getenv("PLUGGY_CLIENT_SECRET"),
        item_map=item_map,
        bills_cache_file=os.getenv("PLUGGY_BILLS_CACHE_FILE", BILLS_CACHE_FILE),
    )
