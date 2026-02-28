# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

```bash
pip install -r requirements.txt              # Install dependencies
streamlit run app.py                         # Run app (opens http://localhost:8501)
python -m unittest discover -s tests -p "test_*.py" -v   # Run all tests
python -m py_compile app.py application/*.py core/*.py domain/*.py services/*.py adapters/*.py repositories/*.py ports/*.py presentation/*.py presentation/tabs/*.py tests/*.py data.py pluggy_integration.py   # Syntax check
```

## Architecture

Hexagonal (Ports & Adapters) architecture. The data flow is:

```
app.py → application/bootstrap.py (wires dependencies)
       → presentation/main_screen.py → presentation/tabs/ (6 tabs)
       → services/ (FinanceService, BillsService) — use-case orchestration
       → ports/ (Protocol interfaces: RulesDataPort, TransactionsDataPort, BankingPort, AccountsPort)
       → adapters/ (concrete implementations bridging ports to repositories/API)
       → repositories/ (ConfigRepository for JSON rules, TransactionsRepository for CSV data)
       → domain/ (pure logic: classification, deduplication, analytics — no I/O)
```

`pluggy_integration.py` is the HTTP client for the Pluggy banking API. It handles auth, transaction fetching with pagination, credit card bills, and local JSON caching. Supports any number of bank accounts configured via `contas.json`.

`data.py` is a legacy compatibility facade delegating to repositories — do not expand it.

## Layer Rules

- **presentation/**: Streamlit UI only. No business logic in tabs or components.
- **services/**: Depend on `ports/` (Protocols), never on concrete adapters or repositories.
- **domain/**: Pure functions. No I/O, no imports from other app layers.
- **application/bootstrap.py**: The only place that wires concrete adapters into services (Composition Root).

## Coding Conventions

- PEP 8, 4-space indentation, type hints on public functions.
- `snake_case` for functions/variables/files, `PascalCase` for classes.
- All UI text and category names are in Portuguese (pt-BR).
- Classification rules use Unicode-normalized matching (case/accent/whitespace insensitive) — see `domain/classification.py`.

## Data Files

- `dados_financeiros.csv`: Transaction ledger (columns: Data, Descrição, Valor, Tipo, Categoria, Fonte, pluggy_id).
- `regras_classificacao.json`: Categories (with icons and `gasto_real` flag) + keyword→category rules.
- `faturas_cache.json`: Cached credit card bills from Pluggy API.
- `contas.json`: Bank account configuration (array of `{pluggy_item_id, nome}`). Manageable via sidebar UI or manual edit. See `contas.json.example`. Falls back to legacy `.env` vars if absent.
- `.env`: Pluggy API credentials (`PLUGGY_CLIENT_ID`, `PLUGGY_CLIENT_SECRET`). Legacy bank item IDs (`PLUGGY_ITEM_ID_NUBANK`, `PLUGGY_ITEM_ID_SANTANDER`) still supported as fallback.

## Testing

- Framework: built-in `unittest`. Test files in `tests/` named `test_*.py`.
- Prioritize tests for `domain/` logic, `services/` behavior, and categorization/deduplication regressions.
- For bug fixes, add a failing test first when possible.
