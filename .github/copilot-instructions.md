# Copilot Instructions — D Mark I

## Project
- **Name**: D Mark I  
- **Type**: CLI for tracking and analyzing investments in **Stocks** and **REITs (FIIs)**  
- **Language**: Python with **SQLite**  
- **Integrations**: external APIs + CVM file downloads (CSV/XLSX)  

## Goals for Copilot
- Generate/refactor **Python CLI** code (data parsing, calculations, imports, downloads).  
- Suggest proper **error handling**, **timeouts**, **retries**, and clear **logging**.  
- Assist with **GitHub Issues**, **commits**, and **PR reviews**.  

## Style
- Quotes: **single quotes** in Python.  
- Indentation: **TAB** (not spaces).  
- Naming: `snake_case` (functions/vars), `PascalCase` (classes).  
- Messages/CLI output: **Portuguese (PT-BR)**.  
- Follow repo linting rules; **do not auto-convert tabs to spaces**.  

## Database (SQLite)
- Use **parameters** in queries, never string interpolation.  
- Ensure migrations/checks before creating tables.  
- Always close cursors/connections.  

## Networking & I/O
- Validate **HTTP status**, **content-type**, **file size** when downloading.  
- Handle **encoding** (UTF-8 + fallback).  
- Normalize dates (`yyyy-mm-dd` or `dd/mm/yyyy`).  
- Use **timeouts + retry with jitter** in API calls.  

## Commits & PRs
- Commit types: `feature`, `bug`, `chore`, `spike`.  
- Format: `<type> : short description`  
  - Ex: `feature : import monthly CVM positions`  
- PR checklist:  
  - [ ] Tested CLI locally  
  - [ ] Handled network errors/timeouts  
  - [ ] No secrets committed  

## Code Review focus
- Enforce **single quotes + TAB**.  
- Suggest simplifications (short funcs, avoid deep nesting).  
- Check I/O safety (file exists, encoding, permissions).  
- SQL must use **parameters**.  
- Normalize dates and currency explicitly.  

## Security
- Never expose secrets.  
- Recommend **environment variables** for credentials.  
- Validate/sanitize CLI user input.    
