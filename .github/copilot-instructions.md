## Purpose
Provide concise instructions so a coding agent can become productive quickly in this small "MCP-Basic" repository.

## Project Summary
- Small example project that exposes an MCP server using `fastmcp`. The server entry point is `main.py`.
- The main MCP node is created with `mcp = FastMCP(name='GastosMCP')` and started with `mcp.run()`.
- Data lives in `expenses.csv` (simple CSV with columns `date,category,amount,payment_method`).

## Key Components
- `main.py`: defines tools and resources registered on the MCP node:
  - `@mcp.tool` marks functions callable by the assistant (example: `add_expense`).
  - `@mcp.resource("resources://expenses.csv")` exposes the CSV as a resource (function: `get_expenses_file`).
  - `@mcp.prompt` provides the assistant prompt used by the server.
- `expenses.csv`: the single source of truth for expenses. Contains header, blank lines and potential duplicates.
- `pyproject.toml`: declares dependency `fastmcp>=2.13.1` and Python >= 3.14.

```instructions
## Purpose
Concise guide for coding agents to be productive quickly in this small MCP example.

## Quick Summary
- Entry point: `main.py` — creates `FastMCP(name='GastosMCP')` and calls `mcp.run()`.
- Storage: `expenses.csv` is the single source of truth (columns: `date,category,amount,payment_method`).
- Dependency: `fastmcp` (see `pyproject.toml`). Python >= 3.14.

## Where to Look
- `main.py`: register/add tools with `@mcp.tool`, expose files with `@mcp.resource("resources://expenses.csv")`, and supply the assistant prompt with `@mcp.prompt`.
- `expenses.csv`: CSV data is authoritative; may contain blanks and duplicates.

## Conventions & API
- Tool signature example: `add_expense(date: str, category: str, amount: float, payment_method: str)` — validate types and date with `datetime.strptime('%Y-%m-%d')`.
- Allowed categories: `['Food','Transport','Entertainment','Utilities','Health','Education','Other']`.
- Allowed payment methods: `['cash','card','online']`.
- CSV order: `date,category,amount,payment_method` (do not reorder columns).
- `get_expenses_file` returns a JSON string: list of objects with keys `date`, `category`, `amount` (float|null), `payment_method`.

## Design Notes (why things are this way)
- Appending to CSV keeps the example minimal and deterministic for demos; tools should not assume atomic DB semantics.
- Resources return JSON strings for easy LLM parsing; avoid returning file streams or binary blobs.

## Run & Debug (Windows Git Bash / WSL)
```bash
python -m venv .venv
source .venv/Scripts/activate
pip install -r requirements.txt  # or: pip install fastmcp
python main.py
```

## Editing Guidelines for Agents
- Add new tools in `main.py` with `@mcp.tool` and ensure input validation and clear return types.
- If modifying resource output (e.g., `get_expenses_file`), keep backward compatibility (return same JSON schema) or add a new resource path.
- Do not migrate storage format silently; open an issue or add a compatibility shim.

## Examples
- Add expense (tool): `add_expense(date='2025-11-22', category='Food', amount=10.0, payment_method='cash')`
- Read expenses (resource): `resources://expenses.csv` -> `[ {"date":"2025-11-01","category":"Food","amount":12.5,"payment_method":"cash"}, ... ]`

## Notes
- No automated tests in repo — run the server and use an MCP client for integration checks.
- Keep changes minimal and consistent with existing patterns.
```
```
