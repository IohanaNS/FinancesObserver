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

    def save_investments(self, investments: list[dict], goal: float | None = None, goal_months: int | None = None) -> None:
        existing = self.load_investments() or {}
        preserved_goal = goal if goal is not None else existing.get("goal")
        preserved_months = goal_months if goal_months is not None else existing.get("goal_months")

        data: dict = {
            "_id": self.INVESTMENTS_ID,
            "updated_at": datetime.now().isoformat(),
            "investments": investments,
        }
        if preserved_goal is not None:
            data["goal"] = preserved_goal
        if preserved_months is not None:
            data["goal_months"] = int(preserved_months)

        self._col.replace_one({"_id": self.INVESTMENTS_ID}, data, upsert=True)

    def save_investments_goal(self, goal: float, months: int | None = None) -> None:
        existing = self.load_investments() or {}
        investments = existing.get("investments", [])
        self.save_investments(
            investments=investments if isinstance(investments, list) else [],
            goal=float(goal),
            goal_months=months,
        )
