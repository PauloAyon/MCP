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

## Data Flow & Design Rationale
- The MCP server exposes two main interaction types:
  - Tools: actions the LLM can invoke (e.g., append a new expense).
  - Resources: read-only data the LLM can request (e.g., a JSON representation of the CSV).
- `add_expense` appends rows directly to `expenses.csv` by design; no external DB is used to keep the example minimal.
- `get_expenses_file` returns a JSON string with structured records to make it easy for an LLM to parse and analyze data.

## Project-specific Conventions
- Date format: `YYYY-MM-DD`. `add_expense` validates dates with `datetime.strptime`.
- Allowed categories in `add_expense`: `['Food','Transport','Entertainment','Utilities','Health','Education','Other']`.
- Allowed payment methods in `add_expense`: `['cash','card','online']`.
- CSV column order is expected as: `date,category,amount,payment_method`.
- `get_expenses_file` returns JSON objects with keys: `date`, `category`, `amount`, `payment_method`. `amount` is parsed to `float` when possible, otherwise `null`.

## Run & Debug (reproducible commands)
Use Git Bash / WSL on Windows:

```bash
# Create and activate venv
python -m venv .venv
source .venv/Scripts/activate

# Install minimal dependencies
pip install fastmcp

# Run the MCP server
python main.py
```

Notes:
- There are no automated tests. To validate behavior, run the server and interact using an MCP client or send HTTP/CLI requests if you have a client.

## Editing Guidelines
- Keep tool/resource APIs declared with `@mcp.tool`, `@mcp.resource`, and `@mcp.prompt` inside `main.py`.
- New tools should be strongly typed and validate inputs, following the example of `add_expense(date: str, category: str, amount: float, payment_method: str)`.
- If you change `get_expenses_file` output format, keep backward compatibility by returning a JSON string with the same structure or add a new resource path.

## Integrations & External Dependencies
- `fastmcp` is the only runtime dependency — MCP decorators and `mcp.run()` are provided by that package.
- All persistent data is local in `expenses.csv`.

## Concrete Examples
- Add an expense (tool call):
  - `add_expense(date='2025-11-22', category='Food', amount=10.0, payment_method='cash')`
- Read expenses (resource): `resources://expenses.csv` returns a JSON string such as:
  - `[{"date":"2025-11-01","category":"Food","amount":12.5,"payment_method":"cash"}, ...]`

## Caveats & What To Avoid
- Do not assume the CSV is sorted or unique; callers should validate and deduplicate when needed.
- Do not store secrets or credentials in the repo. This project is intentionally minimal.

## Open Questions for Maintainers
- Should `expenses.csv` remain the canonical storage, or migrate to SQLite for better queries and testability?
- Do you want automated tests or a simple integration test harness for MCP tools/resources?

If any section is unclear or you want more examples (MCP client snippets, summary endpoints, or tests), tell me which part to expand.
