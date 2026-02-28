import json
import os
import tempfile
import unittest

from adapters.accounts_file_adapter import AccountsFileAdapter


class TestAccountsFileAdapter(unittest.TestCase):
    def setUp(self):
        self.tmpfile = tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        )
        self.tmpfile.write(json.dumps({"contas": []}))
        self.tmpfile.close()
        self.adapter = AccountsFileAdapter(path=self.tmpfile.name)

    def tearDown(self):
        os.unlink(self.tmpfile.name)

    def test_list_empty(self):
        self.assertEqual(self.adapter.list_accounts(), [])

    def test_add_and_list(self):
        self.adapter.add_account("id-1", "Nubank")
        contas = self.adapter.list_accounts()
        self.assertEqual(len(contas), 1)
        self.assertEqual(contas[0]["pluggy_item_id"], "id-1")
        self.assertEqual(contas[0]["nome"], "Nubank")

    def test_add_multiple(self):
        self.adapter.add_account("id-1", "Nubank")
        self.adapter.add_account("id-2", "Santander")
        self.assertEqual(len(self.adapter.list_accounts()), 2)

    def test_add_duplicate_raises(self):
        self.adapter.add_account("id-1", "Nubank")
        with self.assertRaises(ValueError):
            self.adapter.add_account("id-1", "Outro nome")

    def test_add_empty_fields_raises(self):
        with self.assertRaises(ValueError):
            self.adapter.add_account("", "Nubank")
        with self.assertRaises(ValueError):
            self.adapter.add_account("id-1", "")
        with self.assertRaises(ValueError):
            self.adapter.add_account("  ", "  ")

    def test_remove_account(self):
        self.adapter.add_account("id-1", "Nubank")
        self.adapter.add_account("id-2", "Santander")
        self.adapter.remove_account("id-1")
        contas = self.adapter.list_accounts()
        self.assertEqual(len(contas), 1)
        self.assertEqual(contas[0]["pluggy_item_id"], "id-2")

    def test_remove_nonexistent_no_error(self):
        self.adapter.add_account("id-1", "Nubank")
        self.adapter.remove_account("id-inexistente")
        self.assertEqual(len(self.adapter.list_accounts()), 1)

    def test_file_not_exists_returns_empty(self):
        adapter = AccountsFileAdapter(path="/tmp/nao_existe_abc123.json")
        self.assertEqual(adapter.list_accounts(), [])

    def test_add_creates_file(self):
        path = self.tmpfile.name + "_new.json"
        try:
            adapter = AccountsFileAdapter(path=path)
            adapter.add_account("id-1", "Nubank")
            self.assertTrue(os.path.exists(path))
            self.assertEqual(len(adapter.list_accounts()), 1)
        finally:
            if os.path.exists(path):
                os.unlink(path)

    def test_strips_whitespace(self):
        self.adapter.add_account("  id-1  ", "  Nubank  ")
        contas = self.adapter.list_accounts()
        self.assertEqual(contas[0]["pluggy_item_id"], "id-1")
        self.assertEqual(contas[0]["nome"], "Nubank")

    def test_persists_to_file(self):
        self.adapter.add_account("id-1", "Nubank")
        with open(self.tmpfile.name, encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(len(data["contas"]), 1)
        self.assertEqual(data["contas"][0]["pluggy_item_id"], "id-1")


if __name__ == "__main__":
    unittest.main()
