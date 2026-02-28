# Repository Guidelines

## Project Structure & Module Organization

This is a Python Streamlit app with layered architecture:

- `app.py`: application entrypoint.
- `application/`: dependency wiring/bootstrap.
- `presentation/` and `presentation/tabs/`: Streamlit UI and tab rendering.
- `services/`: use-case/business orchestration.
- `ports/`: dependency contracts (`RulesDataPort`, `TransactionsDataPort`, `BankingPort`).
- `adapters/`: concrete implementations for ports.
- `repositories/`: data access (`ConfigRepository`, `TransactionsRepository`).
- `domain/`: pure domain logic (classification, analytics, deduplication).
- `tests/`: unit tests.
- `data.py`: legacy compatibility facade (do not expand this layer).

## Build, Test, and Development Commands

- `pip install -r requirements.txt`: install dependencies.
- `streamlit run app.py`: run the app locally.
- `python -m unittest discover -s tests -p "test_*.py" -v`: run all tests.
- `python -m py_compile app.py application/*.py core/*.py domain/*.py services/*.py adapters/*.py repositories/*.py ports/*.py presentation/*.py presentation/tabs/*.py tests/*.py data.py pluggy_integration.py`: quick syntax/type-safety sanity check.

## Coding Style & Naming Conventions

- Use 4-space indentation and PEP 8 conventions.
- Prefer explicit type hints on public functions.
- Use `snake_case` for functions/variables/files and `PascalCase` for classes/dataclasses.
- Keep UI concerns in `presentation/`; avoid business logic in tabs/components.
- Keep domain logic pure in `domain/` (no I/O there).
- Prefer small, focused functions over monolithic methods.

## Testing Guidelines

- Test framework: built-in `unittest`.
- Test files must be named `test_*.py`.
- Prioritize tests for:
  - domain rules (`domain/*`)
  - service behavior (`services/*`)
  - regressions for categorization/deduplication.
- For bug fixes, add a failing test first when possible.

## Commit & Pull Request Guidelines

Git history is not available in this workspace, so use this standard:

- Commit message format: imperative, concise, optionally scoped.
  - Example: `refactor(domain): extract deduplication logic`
- PRs should include:
  - what changed and why,
  - impacted layers/files,
  - validation commands run,
  - screenshots/GIFs for UI changes (theme, layout, tab behavior).

## Security & Configuration Tips

- Store Pluggy credentials only in `.env` (`PLUGGY_*` vars).
- Never commit secrets.
- Treat `dados_financeiros.csv` and cached billing data as sensitive local data.
