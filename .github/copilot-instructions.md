Aqui está o **copilot-instructions** atualizado com as diretivas de arquitetura e o uso de **tabulate** e **colorama** para relatórios:

---

# Copilot Instructions — D Mark I

## Project

* **Name**: D Mark I
* **Type**: CLI for tracking and analyzing investments in **Stocks** and **REITs (FIIs)**
* **Language**: Python with **SQLite**
* **Integrations**: external APIs + CVM file downloads (CSV/XLSX)

## Goals for Copilot

* Generate/refactor **Python CLI** code (data parsing, calculations, imports, downloads).
* Suggest proper **error handling**, **timeouts**, **retries**, and clear **logging**.
* Assist with **GitHub Issues**, **commits**, and **PR reviews**.

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

**Suggested folders**

```
app/
	ui/
	services/
	db/
   repositories/
   migrations/
	core/
		__init__.py  # domain models, errors, utils
```

## Database (SQLite)

* Use **parameters** in queries, never string interpolation.
* Ensure migrations/checks before creating tables.
* Always close cursors/connections.

## Networking & I/O

* Validate **HTTP status**, **content-type**, **file size** when downloading.
* Handle **encoding** (UTF-8 + fallback).
* Normalize dates (`yyyy-mm-dd` or `dd/mm/yyyy`).
* Use **timeouts + retry with jitter** in API calls.

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

## Code Review focus

* Enforce **single quotes + TAB**.
* Suggest simplifications (short funcs, avoid deep nesting).
* Check I/O safety (file exists, encoding, permissions).
* SQL must use **parameters**.
* Normalize dates and currency explicitly.
* Validate architecture boundaries (no UI in services; no DB in UI).
* Ensure reports use `ui/formatters` with **tabulate** and **colorama**.

## Security

* Never expose secrets.
* Recommend **environment variables** for credentials.
* Validate/sanitize CLI user input.

---