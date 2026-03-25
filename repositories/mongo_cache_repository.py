from datetime import datetime

from pymongo.database import Database


class MongoCacheRepository:
    """MongoDB-backed storage for Pluggy API caches (bills, balances, investments)."""

    COLLECTION = "caches"
    BILLS_ID = "bills"
    BALANCES_ID = "balances"
    INVESTMENTS_ID = "investments"

    def __init__(self, db: Database):
        self._col = db[self.COLLECTION]

    # -- Bills --

    def load_bills(self) -> dict | None:
        doc = self._col.find_one({"_id": self.BILLS_ID})
        if doc is None:
            return None
        doc.pop("_id", None)
        return doc

    def save_bills(self, cards: list[dict]) -> None:
        data = {
            "_id": self.BILLS_ID,
            "updated_at": datetime.now().isoformat(),
            "cards": cards,
        }
        self._col.replace_one({"_id": self.BILLS_ID}, data, upsert=True)

    # -- Balances --

    def load_balances(self) -> dict | None:
        doc = self._col.find_one({"_id": self.BALANCES_ID})
        if doc is None:
            return None
        doc.pop("_id", None)
        return doc

    def save_balances(self, balances: list[dict]) -> None:
        data = {
            "_id": self.BALANCES_ID,
            "updated_at": datetime.now().isoformat(),
            "balances": balances,
        }
        self._col.replace_one({"_id": self.BALANCES_ID}, data, upsert=True)

    # -- Investments --

    def load_investments(self) -> dict | None:
        doc = self._col.find_one({"_id": self.INVESTMENTS_ID})
        if doc is None:
            return None
        doc.pop("_id", None)
        return doc

    def save_investments(self, investments: list[dict]) -> None:
        data: dict = {
            "_id": self.INVESTMENTS_ID,
            "updated_at": datetime.now().isoformat(),
            "investments": investments,
        }
        self._col.replace_one({"_id": self.INVESTMENTS_ID}, data, upsert=True)
