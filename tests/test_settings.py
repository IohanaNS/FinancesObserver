import json
import os
import tempfile
import unittest
from unittest.mock import patch

from core.settings import PluggySettings, _load_item_map_from_json, load_pluggy_settings


class LoadItemMapFromJsonTest(unittest.TestCase):
    def test_returns_none_when_file_missing(self):
        self.assertIsNone(_load_item_map_from_json("/nonexistent/path.json"))

    def test_loads_accounts_from_json(self):
        data = {
            "contas": [
                {"pluggy_item_id": "id-1", "nome": "Nubank"},
                {"pluggy_item_id": "id-2", "nome": "Inter"},
            ]
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            path = f.name
        try:
            result = _load_item_map_from_json(path)
            self.assertEqual(result, {"id-1": "Nubank", "id-2": "Inter"})
        finally:
            os.unlink(path)

    def test_skips_entries_with_missing_fields(self):
        data = {
            "contas": [
                {"pluggy_item_id": "id-1", "nome": "Nubank"},
                {"pluggy_item_id": "", "nome": "Invalid"},
                {"pluggy_item_id": "id-3", "nome": ""},
            ]
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            path = f.name
        try:
            result = _load_item_map_from_json(path)
            self.assertEqual(result, {"id-1": "Nubank"})
        finally:
            os.unlink(path)

    def test_empty_contas_returns_empty_dict(self):
        data = {"contas": []}
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            path = f.name
        try:
            result = _load_item_map_from_json(path)
            self.assertEqual(result, {})
        finally:
            os.unlink(path)


class GetConfiguredFontesTest(unittest.TestCase):
    def test_returns_bank_names_plus_synthetic(self):
        settings = PluggySettings(
            base_url="https://api.pluggy.ai",
            client_id=None,
            client_secret=None,
            item_map={"id-1": "Nubank", "id-2": "Inter"},
            bills_cache_file="cache.json",
            balances_cache_file="saldos_cache.json",
            investments_cache_file="investimentos_cache.json",
        )
        fontes = settings.get_configured_fontes()
        self.assertEqual(fontes, ["Nubank", "Inter", "Cartão Crédito Nubank", "Cartão Crédito Inter", "Outro"])

    def test_no_accounts_returns_only_synthetic(self):
        settings = PluggySettings(
            base_url="https://api.pluggy.ai",
            client_id=None,
            client_secret=None,
            item_map={},
            bills_cache_file="cache.json",
            balances_cache_file="saldos_cache.json",
            investments_cache_file="investimentos_cache.json",
        )
        fontes = settings.get_configured_fontes()
        self.assertEqual(fontes, ["Cartão Crédito", "Outro"])

    def test_deduplicates_bank_names(self):
        settings = PluggySettings(
            base_url="https://api.pluggy.ai",
            client_id=None,
            client_secret=None,
            item_map={"id-1": "Nubank", "id-2": "Nubank"},
            bills_cache_file="cache.json",
            balances_cache_file="saldos_cache.json",
            investments_cache_file="investimentos_cache.json",
        )
        fontes = settings.get_configured_fontes()
        self.assertEqual(fontes, ["Nubank", "Cartão Crédito", "Outro"])


class LoadPluggySettingsFallbackTest(unittest.TestCase):
    @patch.dict(os.environ, {
        "PLUGGY_ITEM_ID_NUBANK": "legacy-nubank-id",
        "PLUGGY_ITEM_ID_SANTANDER": "legacy-santander-id",
    }, clear=False)
    @patch("core.settings.ACCOUNTS_FILE", "/nonexistent/contas.json")
    def test_falls_back_to_env_vars(self):
        settings = load_pluggy_settings()
        self.assertEqual(settings.item_map, {
            "legacy-nubank-id": "Nubank",
            "legacy-santander-id": "Santander",
        })


if __name__ == "__main__":
    unittest.main()
