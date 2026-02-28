import json
import os

from core.constants import ACCOUNTS_FILE


class AccountsFileAdapter:
    def __init__(self, path: str = ACCOUNTS_FILE) -> None:
        self._path = path

    def _load(self) -> list[dict[str, str]]:
        if not os.path.exists(self._path):
            return []
        with open(self._path, encoding="utf-8") as f:
            data = json.load(f)
        return data.get("contas", [])

    def _save(self, contas: list[dict[str, str]]) -> None:
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump({"contas": contas}, f, ensure_ascii=False, indent=2)

    def list_accounts(self) -> list[dict[str, str]]:
        return self._load()

    def add_account(self, pluggy_item_id: str, nome: str) -> None:
        pluggy_item_id = pluggy_item_id.strip()
        nome = nome.strip()
        if not pluggy_item_id or not nome:
            raise ValueError("pluggy_item_id e nome são obrigatórios.")
        contas = self._load()
        if any(c.get("pluggy_item_id") == pluggy_item_id for c in contas):
            raise ValueError(f"Conta com ID '{pluggy_item_id}' já existe.")
        contas.append({"pluggy_item_id": pluggy_item_id, "nome": nome})
        self._save(contas)

    def remove_account(self, pluggy_item_id: str) -> None:
        contas = self._load()
        contas = [c for c in contas if c.get("pluggy_item_id") != pluggy_item_id]
        self._save(contas)
