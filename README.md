# Partora — Auto Parts / Hardware / Electrical Operations Platform

[![CI](https://github.com/sartaj05/partora-auto-parts-operations-platform/actions/workflows/ci.yml/badge.svg)](https://github.com/sartaj05/partora-auto-parts-operations-platform/actions/workflows/ci.yml)

Partora is a demo-ready distributor operations portal built for large inventories, fast quotation work, warehouse control, purchasing, customer accounts and role-based access. The frontend is React + Vite; the backend is **core Django JSON APIs without Django REST Framework**.

## What is included

The original landing/login/dashboard experience plus twenty-eight operational modules:

- Barcode / QR inventory scanning and labels
- Vehicle compatibility and OEM cross-reference
- Purchase-order and receiving workflow
- Multi-warehouse stock and transfers
- Low-stock recommendations and one-click replenishment
- Quotation → sales order → invoice pipeline
- Customer / dealer CRM and credit terms
- Tier pricing, quantity discounts and margin preview
- Analytics, KPI reports and CSV export
- Notifications, approvals and audit history
- Order fulfillment, stock reservation, dispatch and payment tracking
- Returns, warranty inspection and RMA resolution
- Cycle counts, stock availability and lot/serial traceability
- Supplier performance, delivery metrics and procurement planning
- Demand forecasting, safety stock and approval-ready purchase planning
- Supplier RFQs, quote scoring and manager-approved offer selection
- Goods receipt, damaged-stock handling and three-way supplier invoice matching
- Customer/dealer self-service portal links
- Integrations hub for accounting, messaging, shipping, payments and webhooks
- Production mobile PWA device, sync and conflict controls
- Multi-tenant organization, branch and approval permissions
- Workflow automation rules with execution history
- Fleet maintenance, service reminders and technician work orders
- Security and compliance center with MFA, sessions and audit evidence
- AI invoice and document processing with PO exception review
- Delivery routes, shipment status and proof of delivery
- B2B EDI and partner API portal with scoped keys and webhooks
- Predictive fleet maintenance and component risk forecasting

Client demonstration highlights:

- VIN decoding with vehicle-aware compatible parts and stock confidence
- Dealer self-service access for quotes, orders, invoices and account exposure
- Branch capacity visibility with traceable multi-warehouse transfers
- Supplier scorecards with contract renewal and shortage alerts
- Executive operations command center with action queues and CSV reporting
- Mobile warehouse queue with offline task sync
- Supplier and dealer workflow notifications
- Explainable AI operations copilot
- GST, receivables and payment reconciliation
- Warranty claims, root causes and supplier chargeback tracking

Client demo additions:

- Integrations hub with connection health and webhook delivery history
- Production mobile PWA controls for offline queue and conflict review
- Multi-tenant permissions with branch-level data boundaries
- Workflow automation builder for operational alerts and approvals
- Fleet maintenance workspace for vehicles and service work orders

See `FEATURES.md` for the feature-by-feature scope.

## Stack

- Frontend: React, React Router and Vite
- Backend: Django ORM + `JsonResponse` APIs
- Database: SQLite for demo, replaceable for production
- Authentication: Django users, role profile and signed bearer token
- Roles: Admin, Manager, Sales and Store
- Offline demo: automatic mock-data fallback when the API cannot be reached
- Deployment: Docker Compose or frontend-only static deployment
- Repository: initialized Git repository on `main`, with GitHub Actions CI included

## Demo users

All demo accounts use password `demo123`.

| Role | Email |
|---|---|
| Admin | `admin@partora.demo` |
| Manager | `manager@partora.demo` |
| Sales | `sales@partora.demo` |
| Store | `store@partora.demo` |

## Quick start

### Full stack with Docker

```bash
docker compose up --build
```

Open `http://localhost:8080`.

### Backend development

```bash
cd backend
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py runserver 8000
```

### Frontend development

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. If Django is unavailable, login automatically falls back to local demo mode and the enhanced modules use mock data/actions.

## Git / GitHub

The downloadable ZIP includes `.git`, all feature-wise commits, the `main` branch and `.github/workflows/ci.yml`. Read `GITHUB_SETUP.md` to attach your own GitHub repository and push the complete history.

## More documentation

- `PROJECT_BRIEF.md` — product and UX direction
- `FEATURES.md` — enhanced module scope
- `FEATURE_COMMITS.md` — commit-by-commit implementation map
- `DEPLOYMENT.md` — Docker and static deployment options
- `GITHUB_SETUP.md` — publish this initialized repository to GitHub
