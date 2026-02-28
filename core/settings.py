import json
import os
from dataclasses import dataclass

from dotenv import load_dotenv

from core.constants import (
    ACCOUNTS_FILE,
    BALANCES_CACHE_FILE,
    BILLS_CACHE_FILE,
    FONTES_SINTETICAS,
    INVESTMENTS_CACHE_FILE,
)


@dataclass(frozen=True)
class PluggySettings:
    base_url: str
    client_id: str | None
    client_secret: str | None
    item_map: dict[str, str]
    bills_cache_file: str
    balances_cache_file: str
    investments_cache_file: str

    @property
    def has_credentials(self) -> bool:
        return bool(self.client_id and self.client_secret)

    def get_configured_fontes(self) -> list[str]:
        """Return dynamic list: bank names + credit card variants + synthetic sources."""
        bank_names = list(dict.fromkeys(self.item_map.values()))
        card_fontes = [f"Cartão Crédito {name}" for name in bank_names]
        return bank_names + card_fontes + FONTES_SINTETICAS


def _load_item_map_from_json(path: str) -> dict[str, str] | None:
    """Try to load account mapping from contas.json. Returns None if file missing."""
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    item_map: dict[str, str] = {}
    for conta in data.get("contas", []):
        item_id = conta.get("pluggy_item_id", "").strip()
        nome = conta.get("nome", "").strip()
        if item_id and nome:
            item_map[item_id] = nome
    return item_map


def _load_item_map_from_env() -> dict[str, str]:
    """Legacy fallback: read PLUGGY_ITEM_ID_NUBANK / PLUGGY_ITEM_ID_SANTANDER."""
    item_map: dict[str, str] = {}
    nubank_item_id = os.getenv("PLUGGY_ITEM_ID_NUBANK", "").strip()
    if nubank_item_id:
        item_map[nubank_item_id] = "Nubank"

    santander_item_id = os.getenv("PLUGGY_ITEM_ID_SANTANDER", "").strip()
    if santander_item_id:
        item_map[santander_item_id] = "Santander"

    return item_map


@dataclass(frozen=True)
class MongoSettings:
    uri: str
    database: str

    @property
    def is_configured(self) -> bool:
        return bool(self.uri and self.database)


def load_mongo_settings() -> MongoSettings:
    load_dotenv()
    return MongoSettings(
        uri=os.getenv("MONGO_URI", ""),
        database=os.getenv("MONGO_DATABASE", "finances_observer"),
    )


def load_pluggy_settings() -> PluggySettings:
    load_dotenv()

    accounts_file = os.getenv("PLUGGY_ACCOUNTS_FILE", ACCOUNTS_FILE)
    item_map = _load_item_map_from_json(accounts_file)
    if item_map is None:
        item_map = _load_item_map_from_env()

    return PluggySettings(
        base_url=os.getenv("PLUGGY_BASE_URL", "https://api.pluggy.ai"),
        client_id=os.getenv("PLUGGY_CLIENT_ID"),
        client_secret=os.getenv("PLUGGY_CLIENT_SECRET"),
        item_map=item_map,
        bills_cache_file=os.getenv("PLUGGY_BILLS_CACHE_FILE", BILLS_CACHE_FILE),
        balances_cache_file=os.getenv("PLUGGY_BALANCES_CACHE_FILE", BALANCES_CACHE_FILE),
        investments_cache_file=os.getenv(
            "PLUGGY_INVESTMENTS_CACHE_FILE",
            INVESTMENTS_CACHE_FILE,
        ),
    )
