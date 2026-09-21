# Feature-wise Commit Map

This repository was intentionally built in feature-sized Git commits so the development sequence is easy to review, demo, or extend.

| Commit | Feature |
|---|---|
| `a55f57d` | Bootstrap repository, product brief, README and ignore rules |
| `8b904c4` | Core Django project, signed-token login, roles and CORS foundation |
| `e274051` | Inventory, quotation, supplier and stock domain models/API reads |
| `31d5591` | Responsive public landing page and trust-focused visual system |
| `f7e6d6d` | Login flow and automatic offline/demo authentication fallback |
| `a70c502` | Role-aware application shell, dashboards and operational modules |
| `66cf805` | Database migration, Docker stack and static frontend deployment support |
| `cc0c549` | Persistent demo database path and hardened seed data setup |
| `7c696cc` | Backend create flows for catalog, quotations, suppliers and stock |
| `a6cce81` | Reusable frontend create modal plus offline write fallback |
| `f335368` | Connected create forms for live Django and frontend-only demo mode |

Use `git log --oneline --reverse` to view the exact history in sequence.
