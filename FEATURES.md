# Partora Enhanced Feature Set

The enhanced demo adds ten operational modules on top of the original inventory, quotations, suppliers and stock foundation.

1. **Barcode / QR inventory** — assign internal or external codes, scan/search by code or SKU, and print labels.
2. **Vehicle compatibility** — map SKUs to make, model, year range, variant, engine and OEM reference.
3. **Purchase orders** — create supplier POs, track status and expected date, and receive ordered quantities into stock.
4. **Multi-warehouse stock** — manage branches, warehouse stock and traceable inter-warehouse transfers.
5. **Smart reorder desk** — detect low/out-of-stock products, calculate suggested quantities and create replenishment POs.
6. **Quote → sales order → invoice** — convert approved commercial activity without retyping customer totals.
7. **Customer / dealer CRM** — keep contacts, customer type, credit limit, payment terms, outstanding balance and notes.
8. **Pricing & discounts** — retail/wholesale/dealer tiers, quantity rules, discount preview and estimated margin.
9. **Analytics & reports** — sales, inventory value, outstanding exposure, conversion, catalog mix and CSV export.
10. **Notifications, approvals & audit** — request/review purchase, discount or stock approvals and retain trace history.

## Role access

- **Admin**: all modules.
- **Manager**: all operational, commercial, reporting and approval modules.
- **Sales**: inventory, barcodes, fitments, quotations, sales flow, CRM, pricing, analytics and governance inbox.
- **Store**: inventory, stock, barcodes, fitments, purchase orders, warehouses, reorder and governance inbox.

## Demo resilience

Every enhanced React module has local fallback data or a local demo action. If the Django API is unavailable, a static frontend deployment remains navigable and demonstrable with the same four demo logins.
