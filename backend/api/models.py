from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

class Profile(models.Model):
    ROLE_CHOICES = [
        ("admin", "Admin"),
        ("manager", "Manager"),
        ("sales", "Sales"),
        ("store", "Store"),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="sales")

    def __str__(self):
        return f"{self.user.username} ({self.role})"

class Supplier(models.Model):
    name = models.CharField(max_length=120)
    contact_name = models.CharField(max_length=120, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    lead_time_days = models.PositiveIntegerField(default=3)
    rating = models.DecimalField(max_digits=2, decimal_places=1, default=4.0)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Product(models.Model):
    CATEGORY_CHOICES = [
        ("auto", "Auto Parts"),
        ("hardware", "Hardware"),
        ("electrical", "Electrical"),
    ]
    sku = models.CharField(max_length=40, unique=True)
    name = models.CharField(max_length=160)
    brand = models.CharField(max_length=80)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, related_name="products")
    price = models.DecimalField(max_digits=12, decimal_places=2)
    stock_qty = models.IntegerField(default=0)
    reorder_level = models.PositiveIntegerField(default=10)
    bin_location = models.CharField(max_length=40, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def stock_status(self):
        if self.stock_qty <= 0:
            return "out"
        if self.stock_qty <= self.reorder_level:
            return "low"
        return "healthy"

    def __str__(self):
        return f"{self.sku} — {self.name}"


class Quotation(models.Model):
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("sent", "Sent"),
        ("approved", "Approved"),
        ("expired", "Expired"),
    ]
    quote_no = models.CharField(max_length=30, unique=True)
    customer_name = models.CharField(max_length=140)
    customer_company = models.CharField(max_length=140, blank=True)
    total = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    valid_until = models.DateField()
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="quotations")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.quote_no


class StockMovement(models.Model):
    MOVEMENT_CHOICES = [("in", "Stock In"), ("out", "Stock Out"), ("adjustment", "Adjustment")]
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="movements")
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_CHOICES)
    quantity = models.IntegerField()
    reference = models.CharField(max_length=80, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product.sku}: {self.movement_type} {self.quantity}"

# Feature 01: Barcode / QR inventory scanning
# Stored as a standard text code so the frontend can work with USB scanners,
# phone camera integrations, QR values, EAN/UPC codes, or internal labels.
Product.add_to_class("barcode", models.CharField(max_length=64, unique=True, blank=True, null=True))

class VehicleFitment(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="fitments")
    make = models.CharField(max_length=80)
    model = models.CharField(max_length=80)
    year_from = models.PositiveIntegerField()
    year_to = models.PositiveIntegerField()
    variant = models.CharField(max_length=100, blank=True)
    engine = models.CharField(max_length=80, blank=True)
    oem_number = models.CharField(max_length=80, blank=True)

    def __str__(self):
        return f"{self.make} {self.model} {self.year_from}-{self.year_to} / {self.product.sku}"

class PurchaseOrder(models.Model):
    STATUS_CHOICES = [("draft","Draft"),("approved","Approved"),("ordered","Ordered"),("partial","Partially received"),("received","Received")]
    po_no = models.CharField(max_length=30, unique=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name="purchase_orders")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    expected_date = models.DateField(null=True, blank=True)
    total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="purchase_orders")
    created_at = models.DateTimeField(auto_now_add=True)

class PurchaseOrderItem(models.Model):
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="purchase_order_items")
    quantity = models.PositiveIntegerField()
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2)
    received_qty = models.PositiveIntegerField(default=0)

class Warehouse(models.Model):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=120)
    address = models.CharField(max_length=240, blank=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.code} — {self.name}"

class WarehouseStock(models.Model):
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name="stocks")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="warehouse_stocks")
    quantity = models.IntegerField(default=0)

    class Meta:
        unique_together = [("warehouse", "product")]

class StockTransfer(models.Model):
    STATUS_CHOICES = [("completed", "Completed"), ("cancelled", "Cancelled")]
    reference = models.CharField(max_length=40, unique=True)
    from_warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, related_name="outgoing_transfers")
    to_warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, related_name="incoming_transfers")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="warehouse_transfers")
    quantity = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="completed")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="stock_transfers")
    created_at = models.DateTimeField(auto_now_add=True)

# Feature 05: smarter replenishment quantity separate from alert threshold.
Product.add_to_class("reorder_qty", models.PositiveIntegerField(default=25))

class SalesOrder(models.Model):
    STATUS_CHOICES = [("confirmed","Confirmed"),("fulfilled","Fulfilled"),("cancelled","Cancelled")]
    FULFILLMENT_CHOICES = [("confirmed", "Confirmed"), ("picking", "Picking"), ("packed", "Packed"), ("dispatched", "Dispatched"), ("delivered", "Delivered"), ("cancelled", "Cancelled")]
    order_no = models.CharField(max_length=30, unique=True)
    quotation = models.OneToOneField(Quotation, on_delete=models.SET_NULL, null=True, blank=True, related_name="sales_order")
    customer_name = models.CharField(max_length=140)
    customer_company = models.CharField(max_length=140, blank=True)
    total = models.DecimalField(max_digits=14, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="confirmed")
    fulfillment_status = models.CharField(max_length=20, choices=FULFILLMENT_CHOICES, default="confirmed")
    shipping_address = models.CharField(max_length=240, blank=True)
    reserved_at = models.DateTimeField(null=True, blank=True)
    dispatched_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="sales_orders")
    created_at = models.DateTimeField(auto_now_add=True)

class SalesOrderItem(models.Model):
    sales_order = models.ForeignKey(SalesOrder, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="sales_order_items")
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    line_total = models.DecimalField(max_digits=14, decimal_places=2)

class Invoice(models.Model):
    STATUS_CHOICES = [("issued","Issued"),("partial","Partially paid"),("paid","Paid"),("overdue","Overdue"),("cancelled","Cancelled")]
    invoice_no = models.CharField(max_length=30, unique=True)
    sales_order = models.OneToOneField(SalesOrder, on_delete=models.PROTECT, related_name="invoice")
    total = models.DecimalField(max_digits=14, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="issued")
    due_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

class Payment(models.Model):
    METHOD_CHOICES = [("cash", "Cash"), ("bank", "Bank transfer"), ("upi", "UPI"), ("card", "Card"), ("credit", "Credit terms")]
    invoice = models.ForeignKey(Invoice, on_delete=models.PROTECT, related_name="payments")
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    method = models.CharField(max_length=20, choices=METHOD_CHOICES, default="bank")
    reference = models.CharField(max_length=80, blank=True)
    paid_at = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="partora_payments")

class ReturnRequest(models.Model):
    STATUS_CHOICES = [("requested", "Requested"), ("approved", "Approved"), ("received", "Received"), ("inspected", "Inspected"), ("resolved", "Resolved"), ("rejected", "Rejected")]
    RESOLUTION_CHOICES = [("refund", "Refund"), ("replacement", "Replacement"), ("credit", "Account credit"), ("restock", "Restock")]
    return_no = models.CharField(max_length=30, unique=True)
    sales_order = models.ForeignKey(SalesOrder, on_delete=models.SET_NULL, null=True, blank=True, related_name="returns")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="return_requests")
    customer_name = models.CharField(max_length=140)
    quantity = models.PositiveIntegerField(default=1)
    reason = models.CharField(max_length=240)
    warranty_expires = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="requested")
    resolution = models.CharField(max_length=20, choices=RESOLUTION_CHOICES, blank=True)
    inspection_notes = models.CharField(max_length=300, blank=True)
    refund_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    stock_restocked = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="return_requests")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Customer(models.Model):
    TYPE_CHOICES = [("retail","Retail"),("dealer","Dealer"),("fleet","Fleet"),("workshop","Workshop")]
    name = models.CharField(max_length=140)
    company = models.CharField(max_length=160, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    customer_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default="retail")
    credit_limit = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    payment_terms_days = models.PositiveIntegerField(default=0)
    outstanding_balance = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.company or self.name

# Feature 08: tier pricing and discount rules.
Product.add_to_class("cost_price", models.DecimalField(max_digits=12, decimal_places=2, default=0))
Product.add_to_class("wholesale_price", models.DecimalField(max_digits=12, decimal_places=2, default=0))
Product.add_to_class("dealer_price", models.DecimalField(max_digits=12, decimal_places=2, default=0))
Product.add_to_class("reserved_qty", models.PositiveIntegerField(default=0))

class PriceRule(models.Model):
    name = models.CharField(max_length=120)
    customer_type = models.CharField(max_length=20, choices=Customer.TYPE_CHOICES, default="dealer")
    min_qty = models.PositiveIntegerField(default=1)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name="partora_notifications")
    role = models.CharField(max_length=20, blank=True)
    title = models.CharField(max_length=140)
    message = models.CharField(max_length=300)
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

class ApprovalRequest(models.Model):
    STATUS_CHOICES = [("pending","Pending"),("approved","Approved"),("rejected","Rejected")]
    KIND_CHOICES = [("purchase","Purchase"),("discount","Discount"),("stock","Stock adjustment")]
    kind = models.CharField(max_length=20, choices=KIND_CHOICES)
    reference = models.CharField(max_length=80)
    amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    requested_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="approval_requests")
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="approval_reviews")
    notes = models.CharField(max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

class AuditLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="partora_audit_logs")
    action = models.CharField(max_length=80)
    entity = models.CharField(max_length=80)
    entity_id = models.CharField(max_length=80, blank=True)
    detail = models.CharField(max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
