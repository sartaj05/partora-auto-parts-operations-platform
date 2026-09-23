# Partora Enhanced Feature Set

The enhanced demo adds operational modules on top of the original inventory, quotations, suppliers and stock foundation.

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
11. **Order fulfillment & payments** — reserve stock, pick/pack/dispatch orders, deliver them and record partial or full invoice payments.
12. **Returns, warranty & RMA** — register returns, inspect issues, choose refund/replacement/credit/restock and return approved stock.
13. **Inventory control** — compare on-hand versus reserved units, submit cycle counts, approve variances and attach lot/serial traceability.
14. **Supplier performance** — measure PO delivery timing, fill rate, lead time, price snapshots and shortage planning.
15. **Customer portal** — issue expiring share links so customers can review quotes, approve work, see orders/invoices and request repeats.
16. **Demand forecasting & purchase planning** — calculate demand velocity, stock-out risk, safety stock, supplier-level spend and manager-approved replenishment plans.
17. **Supplier RFQ & quote comparison** — request multiple supplier offers, compare price, lead time, availability and reliability, then select an approved offer into a purchase order.
18. **Goods receipt & three-way invoice matching** — post partial deliveries, separate damaged units, update sellable inventory and match supplier invoices against PO pricing and received quantities before manager approval.

## Client demo journey

The recommended presentation path is:

```text
VIN Fitment → Dealer Portal → Multi-Warehouse Control → Supplier Intelligence → Executive Command Center
```

- **VIN Fitment** — decode a supported demo VIN, identify the vehicle and show stock-aware compatible parts.
- **Dealer Portal** — issue a time-limited customer link for quote approvals, order tracking, invoices and account exposure.
- **Multi-Warehouse Control** — compare branch capacity and create traceable stock transfers.
- **Supplier Intelligence** — review delivery performance, shortage plans and contract renewal dates.
- **Executive Command Center** — surface sales, inventory, procurement, invoice and warehouse risks in one view.

## Next operations suite

The next client-ready workflow is also available in the demo:

```text
Mobile Warehouse → Notifications → AI Copilot → Finance & GST → Warranty Intelligence
```

- **Mobile Warehouse** — scan, receive, pick and count from a device-friendly queue with offline sync status.
- **Notifications** — queue supplier, dealer and internal messages using reusable workflow templates.
- **AI Copilot** — answer stock, supplier, warehouse and invoice questions with explainable demo recommendations.
- **Finance & GST** — reconcile payments, review receivables, estimate GST and export finance CSV data.
- **Warranty Intelligence** — monitor claim approvals, root causes, supplier recovery and return-rate trends.

## Deployability & scale suite

The next five client-facing platform capabilities complete the path from an impressive demo to a deployable operations product:

```text
Integrations Hub -> Production Mobile PWA -> Multi-Tenant SaaS -> Workflow Automation -> Fleet Maintenance
```

- **Integrations Hub** — connect accounting, messaging, shipping, payments, VIN providers and webhooks with connection health and delivery history.
- **Production Mobile PWA** — monitor registered devices, offline queues, sync retries and conflicts that need manager review.
- **Multi-Tenant SaaS & permissions** — separate organizations and branches, invite users, assign role scope and set approval ceilings.
- **Workflow Automation Builder** — define trigger/action rules, run them on demand, pause them safely and retain execution history.
- **Fleet Maintenance** — register fleet vehicles, track service reminders and manage technician work orders with parts and labor value.

All five screens use the same API-or-local-demo fallback as the rest of the product, so a client walkthrough remains usable when the backend is offline.

## Role access

- **Admin**: all modules.
- **Manager**: all operational, commercial, reporting and approval modules.
- **Sales**: inventory, barcodes, fitments, quotations, sales flow, CRM, pricing, analytics and governance inbox.
- **Store**: inventory, stock, barcodes, fitments, purchase orders, receiving, warehouses, reorder, demand planning, supplier RFQs and governance inbox.

## Demo resilience

Every enhanced React module has local fallback data or a local demo action. If the Django API is unavailable, a static frontend deployment remains navigable and demonstrable with the same four demo logins. The five client-demo screens also include realistic seeded states and interactive fallback actions, so a backend outage does not interrupt a presentation.
