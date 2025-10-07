# Copilot Instructions — D Mark II

## Project Overview

* **Name**: D Mark II
* **Type**: CLI for tracking and analyzing investments in **Stocks** and **REITs (FIIs)**
* **Language**: Python 3.11+ with **SQLite**
* **Domain**: Brazilian financial market (CVM, B3 integrations)
* **Data Sources**: CVM APIs, B3 files, manual imports (CSV/XLSX)
* **Key Features**: FCA/ITR/DFP imports, portfolio tracking, financial analysis, user authentication

## Style

* Quotes: **single quotes** in Python.
* Indentation: **TAB** (not spaces).
* Naming: `snake_case` (functions/vars), `PascalCase` (classes).
* Messages/CLI output: **Portuguese (PT-BR)**.
* Follow repo linting rules; **do not auto-convert tabs to spaces**.

## Architecture (MUST FOLLOW)

Use the current layered architecture and keep dependencies **one-directional**:

* **ui/** (CLI & presentation): argparse/typer handlers, formatting, user prompts.
  * Calls **services** only. **No DB or network** logic here.

* **services/** (business logic/use cases): portfolio math, PM/FIFO, validation, orchestration.
  * Calls **repositories** and **core**.

* **repositories/** (data access & gateways): SQLite DAOs, file loaders, HTTP clients.
  * No formatting, no CLI text. Use **parameterized SQL** only.

* **core/** (domain & utilities): entities, value objects, enums, errors, date/money utils.
  * **No imports from other layers.**

**Rules**

* UI → Services → Repositories → Core. Never import upward or sideways.
* Inject dependencies via constructors/factories (enable easy mocking).
* Prefer `typing.Protocol` for repository/service interfaces.
* Keep functions short; push branching to services; keep repositories thin.

**Current folder structure**

```
app/
	ui/
		backup/           # backup UI flows
		importacao/       # import UI flows
		widgets.py        # common UI components (header, pause, confirm)
		prompts.py        # input helpers (username, password)
		splash.py         # startup screen with pyfiglet
		menu.py           # main navigation loops
	services/
		importacao/       # CVM import services (FCA, ITR, DFP)
		auth_service.py   # login flow, password validation
		backup_service.py # backup/restore operations
		config_service.py # user preferences management
	db/
		connection.py     # SQLite connection factory
		bootstrap.py      # migrations runner + admin user seed
		repositories/
			importacao/   # CVM data repositories
			usuarios/     # user management repositories
		migrations/       # SQL migration files (####_description.sql)
	core/
		__init__.py       # domain models, errors, utils
		formatters.py     # tabulate/colorama helpers
		security.py       # bcrypt password hashing
		paths.py          # directory constants (DATA_DIR, BACKUP_DIR)
		utils.py          # CNPJ validation, date parsing, URL validation
		decimal_ctx.py    # precise money calculations with Decimal
		xlsx.py           # Excel file readers using openpyxl
```

## CLI CRUD Pattern (Typer + Rich)

* All CRUDs must be implemented as interactive commands using **Typer** (==0.9.0), grouped by domain (e.g., companies, users).
* Use **Rich** for prompts, tables, panels, and visual feedback. All messages and labels must be in **PT-BR** (Portuguese).
* The CLI should be accessible via the main menu and also directly through the Typer command.
* When only the main command is entered (e.g., `empresas`), display the available subcommands with descriptions.
* The `/help` command must be available in all command groups.
* The terminal must correctly restore its state after exiting the interactive CLI (no session lock or duplication).
* Error and validation messages must be clear, always in Portuguese.
* Follow the architecture pattern: UI (Typer/Rich) → Services → Repositories → Core. Never mix responsibilities.
* CRUDs must follow this template:
	- **Repository**: CRUD methods, parameterized SQL, no business logic.
	- **Service**: validation, business rules, orchestration, custom errors.
	- **UI/CLI**: Typer commands, Rich prompts, tables, visual feedback.


### Example CLI CRUD Structure

```
app/ui/cli/commands/empresas.py   # Typer commands for companies
app/services/empresas/empresa_config_service.py
app/db/repositories/empresas/empresa_config_repo.py
app/db/migrations/000X_empresas_config.sql
```

### Corrections and UX

* Always test the CLI after changes: commands, navigation, terminal state.
* Ensure `/help` works in all command groups.
* When only the command name is entered, show subcommands and descriptions.
* Fix any session lock or duplication in the terminal.


### Implementation Reference

* See examples and patterns in `app/ui/cli/commands/base.py` and `app/ui/cli/interactive_shell.py`.
* Always follow the architecture and UX pattern described above.

## Goals for Copilot

* Generate/refactor **Python CLI** code (data parsing, calculations, imports, downloads).
* Implement **Brazilian financial market** specific logic (CNPJ validation, CVM formats, B3 standards).
* Suggest proper **error handling**, **timeouts**, **retries**, and **progress indicators** (tqdm).
* Assist with **database migrations**, **SQLite optimizations**, and **data integrity**.
* Help with **GitHub Issues**, **commit messages**, and **PR reviews**.
* Focus on **user experience** with clear Portuguese messages and intuitive workflows.

## Database (SQLite)

* Use **parameters** in queries, never string interpolation.
* Follow migration pattern: `app/db/migrations/####_description.sql` with version control in `_migrations` table.
* Always close cursors/connections.
* Use `sqlite3.Row` factory for dict-like access to results.
* Implement upsert patterns for CVM data with duplicate handling.
* Repository pattern: one repo per domain entity (e.g., `CiaAbertaFcaRepo`, `UsuarioRepo`).

## Networking & I/O

* Validate **HTTP status**, **content-type**, **file size** when downloading CVM/B3 files.
* Handle **encoding** (UTF-8 + fallback to latin1 for CVM CSV files).
* Normalize dates (`yyyy-mm-dd` format internally) and CNPJ (14 digits with validation).
* Use **timeouts + retry with jitter** in API calls.
* Implement **progress bars** with `tqdm` for long-running imports.
* Clean up **temporary files** after ZIP extraction.
* Handle **CSV delimiters** correctly (`;` for CVM, `,` for B3).

## UI & Reports (tabulate + colorama)

* Tables/reports **must** use:

  * **tabulate** for tabular output (e.g., `tablefmt='fancy_grid'` or `github` when copying).
  * **colorama** for highlights (headers, totals, gains/losses).

* Keep all **formatting in `ui/`** (no colors/tables in services or repositories).
* Provide helpers in `ui/formatters.py`:

  * `render_table(rows, headers, tablefmt='fancy_grid')`
  * `paint_gain_loss(value)` → green/red using colorama
  * `paint_header(text)` → styled section headers
* Always include totals/summary rows where applicable.
* All CLI messages and labels **in PT-BR**.

## Domain-Specific Patterns

* **CNPJ handling**: Use `normalize_cnpj()` and `valid_cnpj()` from `core/utils.py`.
* **Date parsing**: Use `parse_date()` to convert CVM dates to ISO format.
* **URL validation**: Use `validate_url()` and `parse_url()` for web addresses.
* **Money calculations**: Use `decimal_ctx.py` with `money()` and `qty()` for precision.
* **CVM imports**: Follow consolidation pattern (latest document_id wins per CNPJ).
* **Progress tracking**: Use `tqdm` for all long-running operations.

## Authentication & Security

* User login with **bcrypt** password hashing.
* Account lockout after 5 failed attempts.
* Force password change on first login.
* Environment variables for sensitive configuration.
* Input validation for all user data.

## Error Handling

* Use custom `ValidationError` for business rule violations.
* Handle network timeouts gracefully with user-friendly messages.
* Provide detailed error reports for import failures.
* Log errors but show clean messages to users in Portuguese.

## Testing Considerations

* Mock HTTP calls in service tests.
* Use temporary databases for repository tests.
* Test CNPJ validation edge cases.
* Verify CSV parsing with malformed data.
* Test authentication flows and lockout scenarios.

## Commits & PRs

* Commit types: `feature`, `bug`, `chore`, `spike`.
* Format: `<type> : short description`

  * Ex: `feature : import monthly CVM positions`
* PR checklist:

  * [ ] Tested CLI locally
  * [ ] Handled network errors/timeouts
  * [ ] No secrets committed
  * [ ] Respects **UI/Services/Repositories/Core** layering
  * [ ] Tables use **tabulate**; colors via **colorama** in `ui/`
  * [ ] CNPJ validation implemented where needed
  * [ ] Progress bars for long operations
  * [ ] Portuguese messages for users

## Code Review focus

* Enforce **single quotes + TAB**.
* Suggest simplifications (short funcs, avoid deep nesting).
* Check I/O safety (file exists, encoding, permissions).
* SQL must use **parameters**.
* Normalize dates and currency explicitly.
* Validate architecture boundaries (no UI in services; no DB in UI).
* Ensure reports use `ui/formatters` with **tabulate** and **colorama**.
* Verify CNPJ normalization and validation.
* Check for proper error handling in imports.

## Environment Setup

* Python 3.11+ required.
* Dependencies: see `requirements.txt` (bcrypt, colorama, pyfiglet, pandas, openpyxl, tabulate, requests, tqdm).
* Environment variables via `.env` file (see `.env.example`).
* SQLite database auto-created on first run.
* Default admin user: `admin/admin` (must change on first login).

## Security

* Never expose secrets.
* Recommend **environment variables** for credentials.
* Validate/sanitize CLI user input.
* Use parameterized SQL queries only.
* Hash passwords with bcrypt + salt.

---
