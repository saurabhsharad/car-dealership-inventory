# Test Report

Results from an actual run on 2026-10-25 at commit `36f8fc3`, on macOS with Python 3.12.15, Node.js 24.19.0 and PostgreSQL 16 (Docker).

## Summary

| Suite | Tests | Result | Coverage |
|---|---|---|---|
| Backend (pytest, real PostgreSQL) | 225 | 225 passed in 3.84 s | 99% statements (420/422) |
| Frontend (Vitest + React Testing Library) | 85 in 13 files | 85 passed | 94.85% statements, 87.13% branches, 96.55% functions, 96% lines |

Commands:

```bash
cd backend && pytest --cov=app --cov-report=term-missing
cd frontend && npm run test:coverage
```

## Backend

The API and database tests run against the `dealership_test` PostgreSQL database, not SQLite or mocks. A guard refuses to run unless the database name ends in `_test`.

| Area | Tests |
|---|---|
| Auth API: register, validation, duplicates, login, current user, admin checks | 33 |
| Vehicle API: create, list, search, update, delete | 48 |
| Inventory API: purchase and restock | 22 |
| Error envelope, validation errors, unexpected errors, CORS | 14 |
| Database: constraints, migrations, sessions | 18 |
| Services: admin CLI, create admin, concurrent purchases, purchase failure | 11 |
| Unit: schemas, tokens, passwords | 63 |
| Config, test-database guard, app startup | 16 |

The concurrency test (run with two stock levels) starts more buyer threads than there are units, each with its own committed connection, all buying the same vehicle at once. It checks that exactly as many purchases succeed as there were units, that every other buyer gets "out of stock", and that stock ends at 0 rather than below.

Coverage by file:

```
Name                         Stmts   Miss  Cover   Missing
----------------------------------------------------------
app/api/dependencies.py         29      0   100%
app/api/errors.py               39      0   100%
app/api/routes/auth.py          18      0   100%
app/api/routes/vehicles.py      29      0   100%
app/cli.py                      51      1    98%   77
app/core/config.py              15      0   100%
app/core/security.py             7      0   100%
app/core/tokens.py              16      0   100%
app/db/base.py                   5      0   100%
app/db/session.py               14      0   100%
app/main.py                     10      0   100%
app/models/user.py              13      0   100%
app/models/vehicle.py           16      0   100%
app/schemas/auth.py             25      0   100%
app/schemas/vehicles.py         47      0   100%
app/services/auth.py            29      1    97%   37
app/services/errors.py           8      0   100%
app/services/vehicles.py        48      0   100%
----------------------------------------------------------
TOTAL                          422      2    99%
```

(Empty `__init__.py` files omitted.) The two uncovered lines are `app/cli.py:77`, the `if __name__ == "__main__"` entry point (the tests call `main()` directly), and `app/services/auth.py:37`, which re-raises a database integrity error that is not a duplicate email.

## Frontend

API modules are mocked with `vi.mock`, and pages are tested through what the user sees: roles, labels and text.

Coverage (files below 100% only):

```
File               | % Stmts | % Branch | % Funcs | % Lines | Uncovered Line #s
-------------------|---------|----------|---------|---------|-------------------
All files          |   94.85 |    87.13 |   96.55 |      96 |
  client.ts        |   96.42 |       92 |   66.66 |      96 | 31
  useAuth.ts       |      75 |       50 |     100 |      75 | 8
  RestockControl   |     100 |    85.71 |     100 |     100 | 25
  VehicleForm.tsx  |   93.87 |    84.09 |     100 |   93.33 | 27,34,95
  DashboardPage    |    90.9 |    82.92 |   96.55 |      93 | ...61,173-175,207
  LoginPage.tsx    |   94.73 |       80 |     100 |     100 | 17-25
  RegisterPage.tsx |   95.83 |    84.61 |     100 |   97.77 | 75
```

Lint (ESLint), formatting (Prettier), type checking (`tsc -b`) and the production build also passed.

## Manual end-to-end check

On 2026-10-25, the running app (Vite on port 5173, API on port 8001, the development database) was exercised in a browser at 1280 px and 360 px wide:

- **Customer:**
  - Registered and was signed in, with no admin controls showing.
  - Bought the last unit of a vehicle; the card switched to "Out of stock" and Purchase was disabled.
  - Searched by category and max price; the request carried only those two filters.
  - Min price above max price showed an inline error and sent no request.
  - Logged out.
- **Admin:**
  - Restocking re-enabled Purchase.
  - An empty Add vehicle form showed an error on each required field.
  - Added, edited and deleted a vehicle. For the delete, `window.confirm` was stubbed to answer yes, because native dialogs block the browser automation.
- **Layout:** no horizontal scrolling at 360 px.

The screenshots are in the [README](../README.md#screenshots).
