from datetime import date, timedelta
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from api.models import Product, Profile, Quotation, StockMovement, Supplier

USERS = [
    ("admin@partora.demo", "Aarav Admin", "admin"),
    ("manager@partora.demo", "Meera Manager", "manager"),
    ("sales@partora.demo", "Rohan Sales", "sales"),
    ("store@partora.demo", "Kabir Store", "store"),
]

class Command(BaseCommand):
    help = "Seed Partora with demo-ready users and operational data"

    def handle(self, *args, **options):
        users = {}
        for email, full_name, role in USERS:
            first, last = full_name.split(" ", 1)
            user, _ = User.objects.get_or_create(username=email, defaults={"email": email, "first_name": first, "last_name": last})
            user.email = email
            user.first_name = first
            user.last_name = last
            user.set_password("demo123")
            user.save()
            profile, _ = Profile.objects.get_or_create(user=user)
            profile.role = role
            profile.save()
            users[role] = user

        suppliers = []
        for data in [
            ("TorqueLine Components", "Neha Rao", "sales@torqueline.demo", "+91 98100 21001", 3, 4.8),
            ("VoltEdge Electricals", "Sameer Khan", "trade@voltedge.demo", "+91 98100 21002", 2, 4.7),
            ("ForgeFast Hardware", "Pooja Shah", "orders@forgefast.demo", "+91 98100 21003", 5, 4.5),
        ]:
            supplier, _ = Supplier.objects.update_or_create(name=data[0], defaults={"contact_name": data[1], "email": data[2], "phone": data[3], "lead_time_days": data[4], "rating": data[5]})
            suppliers.append(supplier)

        products = [
            ("BRK-1048", "Ceramic Brake Pad Set", "RoadShield", "auto", suppliers[0], 2450, 38, 12, "A-04-12"),
            ("FLT-2210", "Engine Oil Filter", "MotoPure", "auto", suppliers[0], 420, 8, 15, "A-02-03"),
            ("BLT-0812", "Hex Bolt M8 × 20 mm", "ForgeFast", "hardware", suppliers[2], 12, 640, 120, "H-11-08"),
            ("BRG-6204", "Deep Groove Bearing 6204", "AxisPro", "hardware", suppliers[2], 310, 5, 18, "H-03-14"),
            ("MCB-C32", "32A C-Curve MCB", "VoltEdge", "electrical", suppliers[1], 690, 72, 20, "E-08-02"),
            ("RLY-24V4", "24V 4-Pin Automotive Relay", "VoltEdge", "electrical", suppliers[1], 180, 0, 16, "E-05-09"),
            ("HLM-H7", "H7 LED Headlamp Pair", "NightArc", "auto", suppliers[1], 1650, 26, 10, "A-09-01"),
            ("CBL-25R", "2.5 sq mm Copper Cable Roll", "VoltEdge", "electrical", suppliers[1], 3250, 14, 8, "E-12-04"),
        ]
        product_objs = {}
        for sku, name, brand, category, supplier, price, stock, reorder, bin_location in products:
            p, _ = Product.objects.update_or_create(sku=sku, defaults={"name": name, "brand": brand, "category": category, "supplier": supplier, "price": price, "stock_qty": stock, "reorder_level": reorder, "bin_location": bin_location})
            product_objs[sku] = p

        quotes = [
            ("QT-260921-104", "Anil Verma", "Metro Garage", 18450, "sent", 7, "sales"),
            ("QT-260921-103", "Priya Nair", "Northline Repairs", 32600, "approved", 10, "manager"),
            ("QT-260920-099", "Imran Sheikh", "Rapid Fleet Care", 12780, "draft", 5, "sales"),
            ("QT-260919-091", "Vikas Jain", "Jain Electrical Works", 48500, "sent", 4, "admin"),
        ]
        for number, customer, company, total, status, days, role in quotes:
            Quotation.objects.update_or_create(quote_no=number, defaults={"customer_name": customer, "customer_company": company, "total": total, "status": status, "valid_until": date.today() + timedelta(days=days), "created_by": users[role]})

        if not StockMovement.objects.exists():
            for sku, kind, qty, ref in [
                ("BRK-1048", "in", 24, "GRN-8842"),
                ("FLT-2210", "out", 12, "INV-5901"),
                ("BRG-6204", "out", 4, "INV-5897"),
                ("MCB-C32", "in", 50, "GRN-8838"),
                ("RLY-24V4", "out", 18, "INV-5880"),
            ]:
                StockMovement.objects.create(product=product_objs[sku], movement_type=kind, quantity=qty, reference=ref)

        self.stdout.write(self.style.SUCCESS("Partora demo data is ready. Password for all demo users: demo123"))
