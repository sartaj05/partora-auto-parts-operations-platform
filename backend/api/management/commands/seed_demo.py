from datetime import date, timedelta
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone
from api.models import (
    ApprovalRequest, AuditLog, Customer, Invoice, Notification, PriceRule, Product,
    Profile, PurchaseOrder, PurchaseOrderItem, Quotation, SalesOrder, StockMovement, DemandHistory,
    StockTransfer, Supplier, VehicleFitment, Warehouse, WarehouseStock,
)

USERS = [
    ("admin@partora.demo", "Aarav Admin", "admin"),
    ("manager@partora.demo", "Meera Manager", "manager"),
    ("sales@partora.demo", "Rohan Sales", "sales"),
    ("store@partora.demo", "Kabir Store", "store"),
]

PRODUCTS = [
    ("BRK-1048", "Ceramic Brake Pad Set", "RoadShield", "auto", "TorqueLine Components", 2450, 1519, 2156, 2009, 38, 12, 30, "A-04-12", "890100010481"),
    ("FLT-2210", "Engine Oil Filter", "MotoPure", "auto", "TorqueLine Components", 420, 260, 370, 344, 8, 15, 40, "A-02-03", "890100022102"),
    ("BLT-0812", "Hex Bolt M8 × 20 mm", "ForgeFast", "hardware", "ForgeFast Hardware", 12, 7, 11, 10, 640, 120, 250, "H-11-08", "890100008123"),
    ("BRG-6204", "Deep Groove Bearing 6204", "AxisPro", "hardware", "ForgeFast Hardware", 310, 192, 273, 254, 5, 18, 50, "H-03-14", "890100062043"),
    ("MCB-C32", "32A C-Curve MCB", "VoltEdge", "electrical", "VoltEdge Electricals", 690, 428, 607, 566, 72, 20, 50, "E-08-02", "890100032003"),
    ("RLY-24V4", "24V 4-Pin Automotive Relay", "VoltEdge", "electrical", "VoltEdge Electricals", 180, 112, 158, 148, 0, 16, 40, "E-05-09", "890100024004"),
    ("HLM-H7", "H7 LED Headlamp Pair", "NightArc", "auto", "VoltEdge Electricals", 1650, 1023, 1452, 1353, 26, 10, 25, "A-09-01", "890100000707"),
    ("CBL-25R", "2.5 sq mm Copper Cable Roll", "VoltEdge", "electrical", "VoltEdge Electricals", 3250, 2015, 2860, 2665, 14, 8, 20, "E-12-04", "890100025007"),
]

class Command(BaseCommand):
    help = "Seed Partora with complete demo-ready users and operational data"

    def handle(self, *args, **options):
        users = {}
        for email, full_name, role in USERS:
            first, last = full_name.split(" ", 1)
            user, _ = User.objects.get_or_create(username=email, defaults={"email": email})
            user.email, user.first_name, user.last_name = email, first, last
            user.set_password("demo123")
            user.save()
            profile, _ = Profile.objects.get_or_create(user=user)
            profile.role = role
            profile.save()
            users[role] = user

        supplier_rows = [
            ("TorqueLine Components", "Neha Rao", "sales@torqueline.demo", "+91 98100 21001", 3, 4.8),
            ("VoltEdge Electricals", "Sameer Khan", "trade@voltedge.demo", "+91 98100 21002", 2, 4.7),
            ("ForgeFast Hardware", "Pooja Shah", "orders@forgefast.demo", "+91 98100 21003", 5, 4.5),
        ]
        suppliers = {}
        for name, contact, email, phone, lead, rating in supplier_rows:
            supplier, _ = Supplier.objects.update_or_create(name=name, defaults={"contact_name": contact, "email": email, "phone": phone, "lead_time_days": lead, "rating": rating, "active": True})
            suppliers[name] = supplier

        products = {}
        for row in PRODUCTS:
            sku, name, brand, category, supplier_name, price, cost, wholesale, dealer, stock, reorder, reorder_qty, bin_location, barcode = row
            product, _ = Product.objects.update_or_create(sku=sku, defaults={
                "name": name, "brand": brand, "category": category, "supplier": suppliers[supplier_name],
                "price": price, "cost_price": cost, "wholesale_price": wholesale, "dealer_price": dealer,
                "stock_qty": stock, "reorder_level": reorder, "reorder_qty": reorder_qty,
                "bin_location": bin_location, "barcode": barcode,
            })
            products[sku] = product

        fitments = [
            ("BRK-1048", "Maruti Suzuki", "Swift", 2018, 2026, "Petrol / AMT", "1.2L", "55810M68P00"),
            ("FLT-2210", "Hyundai", "i20", 2020, 2026, "Petrol", "1.2L", "26300-35505"),
            ("HLM-H7", "Universal", "H7 socket", 2005, 2026, "12V", "", "H7"),
        ]
        for sku, make, model, y1, y2, variant, engine, oem in fitments:
            VehicleFitment.objects.update_or_create(product=products[sku], make=make, model=model, year_from=y1, defaults={"year_to": y2, "variant": variant, "engine": engine, "oem_number": oem})

        demand_rows = {
            "BRK-1048": [8, 10, 12], "FLT-2210": [18, 24, 30], "BLT-0812": [150, 180, 210],
            "BRG-6204": [10, 14, 18], "MCB-C32": [12, 18, 20], "RLY-24V4": [24, 30, 36],
            "HLM-H7": [6, 8, 10], "CBL-25R": [4, 6, 8],
        }
        for sku, quantities in demand_rows.items():
            for days_ago, quantity in zip((60, 30, 0), quantities):
                DemandHistory.objects.update_or_create(product=products[sku], warehouse=None, period_start=date.today() - timedelta(days=days_ago), defaults={"quantity": quantity, "source": "sales"})

        quote_rows = [
            ("QT-260921-104", "Anil Verma", "Metro Garage", 18450, "sent", 7, "sales"),
            ("QT-260921-103", "Priya Nair", "Northline Repairs", 32600, "approved", 10, "manager"),
            ("QT-260920-099", "Imran Sheikh", "Rapid Fleet Care", 12780, "draft", 5, "sales"),
            ("QT-260919-091", "Vikas Jain", "Jain Electrical Works", 48500, "sent", 4, "admin"),
        ]
        quotes = {}
        for number, customer, company, total, status, days, role in quote_rows:
            quote, _ = Quotation.objects.update_or_create(quote_no=number, defaults={"customer_name": customer, "customer_company": company, "total": total, "status": status, "valid_until": date.today() + timedelta(days=days), "created_by": users[role]})
            quotes[number] = quote

        customer_rows = [
            ("Anil Verma", "Metro Garage", "anil@metrogarage.demo", "+91 98111 10001", "workshop", 100000, 15, 18450, "Regular brake and service parts buyer."),
            ("Priya Nair", "Northline Repairs", "priya@northline.demo", "+91 98111 10002", "dealer", 250000, 30, 32600, "Priority dealer pricing."),
            ("Imran Sheikh", "Rapid Fleet Care", "imran@rapidfleet.demo", "+91 98111 10003", "fleet", 400000, 30, 12780, "Fleet maintenance account."),
        ]
        for name, company, email, phone, kind, limit, terms, outstanding, notes in customer_rows:
            Customer.objects.update_or_create(company=company, defaults={"name": name, "email": email, "phone": phone, "customer_type": kind, "credit_limit": limit, "payment_terms_days": terms, "outstanding_balance": outstanding, "notes": notes, "active": True})

        for name, kind, min_qty, discount in [
            ("Dealer 10+ units", "dealer", 10, 4),
            ("Fleet bulk 25+", "fleet", 25, 7.5),
            ("Workshop pack 12+", "workshop", 12, 5),
        ]:
            PriceRule.objects.update_or_create(name=name, defaults={"customer_type": kind, "min_qty": min_qty, "discount_percent": discount, "active": True})

        main, _ = Warehouse.objects.update_or_create(code="DEL-MAIN", defaults={"name": "Delhi Main Warehouse", "address": "Okhla Industrial Area, Delhi", "active": True})
        gur, _ = Warehouse.objects.update_or_create(code="GUR-SAT", defaults={"name": "Gurugram Satellite Store", "address": "Udyog Vihar, Gurugram", "active": True})
        noi, _ = Warehouse.objects.update_or_create(code="NOI-NTH", defaults={"name": "Noida North Store", "address": "Sector 63, Noida", "active": True})
        for idx, product in enumerate(products.values()):
            total = max(product.stock_qty, 0)
            main_qty = max(0, total - (idx % 3) * 2)
            WarehouseStock.objects.update_or_create(warehouse=main, product=product, defaults={"quantity": main_qty})
        for sku, qty in [("BRK-1048", 12), ("FLT-2210", 4), ("HLM-H7", 8), ("MCB-C32", 30)]:
            WarehouseStock.objects.update_or_create(warehouse=gur, product=products[sku], defaults={"quantity": qty})
        for sku, qty in [("BLT-0812", 100), ("BRG-6204", 3), ("CBL-25R", 5)]:
            WarehouseStock.objects.update_or_create(warehouse=noi, product=products[sku], defaults={"quantity": qty})

        if not StockTransfer.objects.filter(reference="TR-260921-2A7F").exists():
            StockTransfer.objects.create(reference="TR-260921-2A7F", from_warehouse=main, to_warehouse=gur, product=products["BRK-1048"], quantity=12, status="completed", created_by=users["store"])

        po, _ = PurchaseOrder.objects.update_or_create(po_no="PO-260921-A12F", defaults={"supplier": suppliers["TorqueLine Components"], "status": "ordered", "expected_date": date.today() + timedelta(days=3), "total": 25200, "created_by": users["manager"]})
        PurchaseOrderItem.objects.update_or_create(purchase_order=po, product=products["FLT-2210"], defaults={"quantity": 60, "unit_cost": 420, "received_qty": 0})
        po2, _ = PurchaseOrder.objects.update_or_create(po_no="PO-260920-90BD", defaults={"supplier": suppliers["VoltEdge Electricals"], "status": "partial", "expected_date": date.today() + timedelta(days=2), "total": 44100, "created_by": users["admin"]})
        PurchaseOrderItem.objects.update_or_create(purchase_order=po2, product=products["MCB-C32"], defaults={"quantity": 40, "unit_cost": 690, "received_qty": 20})

        order, _ = SalesOrder.objects.update_or_create(order_no="SO-260921-41BC", defaults={"quotation": quotes["QT-260921-103"], "customer_name": "Priya Nair", "customer_company": "Northline Repairs", "total": 32600, "status": "confirmed", "created_by": users["manager"]})
        Invoice.objects.update_or_create(invoice_no="INV-260921-0081", defaults={"sales_order": order, "total": 32600, "status": "issued", "due_date": date.today() + timedelta(days=30)})

        if not StockMovement.objects.exists():
            for sku, kind, qty, ref in [("BRK-1048", "in", 24, "GRN-8842"), ("FLT-2210", "out", 12, "INV-5901"), ("BRG-6204", "out", 4, "INV-5897"), ("MCB-C32", "in", 50, "GRN-8838"), ("RLY-24V4", "out", 18, "INV-5880")]:
                StockMovement.objects.create(product=products[sku], movement_type=kind, quantity=qty, reference=ref)

        if not Notification.objects.exists():
            Notification.objects.create(role="manager", title="Low stock needs attention", message="RLY-24V4 is out of stock and has a preferred supplier.")
            Notification.objects.create(role="store", title="Purchase order expected tomorrow", message="PO-260920-90BD is due from VoltEdge Electricals.")
        if not ApprovalRequest.objects.exists():
            ApprovalRequest.objects.create(kind="discount", reference="QT-260921-104 / 9% discount", amount=1650, status="pending", requested_by=users["sales"], notes="Fleet follow-up opportunity")
        if not AuditLog.objects.exists():
            AuditLog.objects.create(user=users["store"], action="stock movement", entity="product", entity_id=str(products["RLY-24V4"].id), detail="out 18 / INV-5880")
            AuditLog.objects.create(user=users["sales"], action="create", entity="quotation", entity_id=str(quotes["QT-260921-104"].id), detail="QT-260921-104")

        self.stdout.write(self.style.SUCCESS("Partora full demo data is ready. Password for all demo users: demo123"))
