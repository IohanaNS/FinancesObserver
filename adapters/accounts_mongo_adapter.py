from pymongo.database import Database


class AccountsMongoAdapter:
    """MongoDB-backed implementation of AccountsPort."""

    COLLECTION = "accounts"

    def __init__(self, db: Database):
        self._col = db[self.COLLECTION]

    def list_accounts(self) -> list[dict[str, str]]:
        return [
            {"pluggy_item_id": doc["pluggy_item_id"], "nome": doc["nome"]}
            for doc in self._col.find({}, {"_id": 0})
        ]

    def add_account(self, pluggy_item_id: str, nome: str) -> None:
        pluggy_item_id = pluggy_item_id.strip()
        nome = nome.strip()
        if not pluggy_item_id or not nome:
            raise ValueError("pluggy_item_id e nome são obrigatórios.")
        if self._col.find_one({"pluggy_item_id": pluggy_item_id}):
            raise ValueError(f"Conta com ID '{pluggy_item_id}' já existe.")
        self._col.insert_one({"pluggy_item_id": pluggy_item_id, "nome": nome})

    def remove_account(self, pluggy_item_id: str) -> None:
        self._col.delete_one({"pluggy_item_id": pluggy_item_id})
