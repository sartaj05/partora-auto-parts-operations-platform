# Project Brief

## Product

**Partora** is a trusted operations workspace for auto-parts, hardware and electrical distributors. It is designed for large catalogs where sales, purchasing and warehouse teams need fast search, accurate stock, pricing control and traceable approvals.

## Business problem

Distributor operations are commonly split between spreadsheets, messaging, billing software and warehouse registers. That slows quotation turnaround, hides stock across branches, makes purchasing reactive, and weakens accountability around discounts and stock adjustments.

## Product goals

1. Search a large catalog quickly by SKU, barcode, description, brand, category, supplier or vehicle fitment.
2. Move commercial work from quotation to sales order and invoice.
3. Maintain supplier, customer/dealer, pricing and credit context in one workspace.
4. Run purchasing and receiving with low-stock recommendations.
5. Track stock across branches and transfer inventory between warehouses.
6. Provide useful KPI and exposure reporting without turning the interface into spreadsheet cosplay.
7. Enforce role-based access, approvals and audit visibility.
8. Remain demo-ready when the backend is disconnected by falling back to local React data.

## UX direction

The interface intentionally avoids the generic blue-gradient SaaS look. It uses a warm neutral base, deep ink text, muted sage and restrained amber accents. Low-contrast borders, spacious layouts and clear operational tables are used to build trust and reduce visual fatigue.

## Core screens

- Public landing page and login
- Role-aware dashboard
- Inventory search and stock movements
- Barcode / QR desk
- Vehicle fitment search
- Quotations and sales flow
- Customers / dealer CRM
- Suppliers and purchase orders
- Warehouses and reorder desk
- Pricing calculator and rules
- Analytics / reporting
- Notifications, approvals and audit history

## Backend direction

Core Django exposes JSON endpoints with `JsonResponse`, Django ORM models, signed bearer tokens, role checks and an idempotent demo seed command. No Django REST Framework dependency is required.

## Demo behavior

The React app attempts the Django API first. Network/server failures switch supported modules to local mock data and local create actions. This allows frontend-only hosting for client demonstrations while the same UI connects to Django when the backend is available.
