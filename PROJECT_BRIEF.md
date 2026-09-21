# Project Brief

## Product
**Partora** is a trusted operations workspace for auto-parts, hardware, and electrical distributors. It is designed for businesses with large catalogs where staff need fast inventory lookup, quotation creation, stock visibility, supplier coordination, and role-specific access.

## Business problem
Traditional distributor workflows are often split across spreadsheets, calls, and separate billing or warehouse tools. That creates slow quote turnaround, uncertain stock visibility, duplicate supplier follow-up, and inconsistent permissions.

## Main goals
1. Search a large parts catalog quickly by SKU, category, brand, description, or supplier.
2. Generate and track quotations with clear statuses and values.
3. View available, low, and out-of-stock items at a glance.
4. Maintain supplier contact and lead-time information.
5. Show each employee only the modules relevant to their role.
6. Keep the frontend presentable even when the backend is not connected, using safe local demo data.

## Frontend UX direction
The interface intentionally avoids the common blue-gradient SaaS look. It uses a light warm-neutral base, deep ink text, muted sage, and restrained amber accents to communicate stability and trust. Cards have low contrast borders, generous spacing, and operational data is prioritized over decorative effects.

## Core screens
- Public landing page
- Login page with demo account helper
- Role-aware dashboard
- Inventory search and stock table
- Quotation list
- Supplier list
- Stock overview

## Backend scope
Core Django provides JSON endpoints through `JsonResponse`, Django ORM models, signed bearer tokens using `django.core.signing`, role checks, and a seed command for demo data. No Django REST Framework dependency is required.

## Demo behavior
The frontend first attempts the Django API. On connection failure it automatically serves mock inventory, quotes, suppliers, metrics, and role permissions. This makes static frontend hosting suitable for client demos.
