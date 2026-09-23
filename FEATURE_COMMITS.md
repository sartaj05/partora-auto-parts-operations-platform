# Feature-wise Commit Map

The repository is intentionally built in reviewable feature commits. The ten requested enhancements each have their own commit.

| Commit | Enhancement |
|---|---|
| `d732880` | Barcode / QR scan lookup and printable inventory labels |
| `5701cba` | Vehicle compatibility, year/variant/engine and OEM mapping |
| `55a1001` | Purchase orders, supplier ordering and stock receiving |
| `1577959` | Multi-warehouse stock and branch transfer workflow |
| `efe254e` | Low-stock recommendations and one-click replenishment PO |
| `981840f` | Quotation → sales order → invoice pipeline |
| `744b484` | Customer/dealer CRM, credit and payment terms |
| `5905792` | Tier pricing, quantity discounts and margin calculator |
| `4a17a83` | KPI analytics, reporting visuals and CSV export |
| `2cbe53f` | Notifications, approvals and audit trail |
| `5f97ea6` | Complete demo seed data for all enhanced workflows |
| `ac401f4` | Demand forecasting, safety stock and approval-ready purchase planning |
| `1c0e0b7` | Supplier RFQ, quote scoring and manager-approved offer selection |
| `a6fb9c1` | Goods receipt, damaged-stock handling and three-way supplier invoice matching |
| `ce3163a` | Five-feature client showcase with VIN, dealer, warehouse, supplier and command-center demos |

The earlier repository history is also preserved, including the original landing page, login, role-aware dashboard, Django API foundation, offline demo mode and deployment setup.

Useful commands:

```bash
git log --oneline --decorate
git log --oneline --reverse
git show d732880
git show 2cbe53f
```
