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


class SupplierContract(models.Model):
    STATUS_CHOICES = [("active", "Active"), ("expiring", "Expiring soon"), ("review", "Needs review")]
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name="contracts")
    contract_no = models.CharField(max_length=40, unique=True)
    expires_on = models.DateField()
    payment_terms = models.CharField(max_length=80, blank=True)
    annual_value = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["expires_on", "supplier__name"]


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
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    tax_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    valid_until = models.DateField()
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="quotations")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.quote_no


class QuotationItem(models.Model):
    quotation = models.ForeignKey(Quotation, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="quotation_items")
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    line_total = models.DecimalField(max_digits=12, decimal_places=2)


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
    received_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="purchase_orders")
    created_at = models.DateTimeField(auto_now_add=True)

class PurchaseOrderItem(models.Model):
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="purchase_order_items")
    quantity = models.PositiveIntegerField()
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2)
    received_qty = models.PositiveIntegerField(default=0)


class GoodsReceipt(models.Model):
    STATUS_CHOICES = [("posted", "Posted"), ("cancelled", "Cancelled")]
    receipt_no = models.CharField(max_length=30, unique=True)
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.PROTECT, related_name="goods_receipts")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="posted")
    notes = models.CharField(max_length=300, blank=True)
    received_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="goods_receipts")
    received_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-received_at"]


class GoodsReceiptLine(models.Model):
    receipt = models.ForeignKey(GoodsReceipt, on_delete=models.CASCADE, related_name="lines")
    purchase_order_item = models.ForeignKey(PurchaseOrderItem, on_delete=models.PROTECT, related_name="receipt_lines")
    accepted_qty = models.PositiveIntegerField(default=0)
    damaged_qty = models.PositiveIntegerField(default=0)
    notes = models.CharField(max_length=240, blank=True)


class SupplierInvoice(models.Model):
    STATUS_CHOICES = [("exception", "Needs review"), ("matched", "Matched"), ("approved", "Approved"), ("rejected", "Rejected")]
    invoice_no = models.CharField(max_length=40, unique=True)
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.PROTECT, related_name="supplier_invoices")
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name="supplier_invoices")
    invoice_date = models.DateField(null=True, blank=True)
    invoice_qty = models.PositiveIntegerField(default=0)
    subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="exception")
    notes = models.CharField(max_length=300, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="supplier_invoices_created")
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="supplier_invoices_approved")
    created_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

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

class InventoryCount(models.Model):
    STATUS_CHOICES = [("draft", "Draft"), ("submitted", "Submitted"), ("approved", "Approved")]
    reference = models.CharField(max_length=30, unique=True)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.SET_NULL, null=True, blank=True, related_name="inventory_counts")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    notes = models.CharField(max_length=300, blank=True)
    counted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="inventory_counts")
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="inventory_count_approvals")
    created_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)

class InventoryCountLine(models.Model):
    inventory_count = models.ForeignKey(InventoryCount, on_delete=models.CASCADE, related_name="lines")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="inventory_count_lines")
    expected_qty = models.IntegerField()
    counted_qty = models.IntegerField()
    variance = models.IntegerField(default=0)

class ProductLot(models.Model):
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="lots")
    warehouse = models.ForeignKey(Warehouse, on_delete=models.SET_NULL, null=True, blank=True, related_name="product_lots")
    lot_no = models.CharField(max_length=80)
    serial_no = models.CharField(max_length=100, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    expiry_date = models.DateField(null=True, blank=True)
    received_at = models.DateField(default=timezone.localdate)

class SupplierPriceSnapshot(models.Model):
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name="price_snapshots")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="supplier_price_snapshots")
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2)
    source_po = models.ForeignKey(PurchaseOrder, on_delete=models.SET_NULL, null=True, blank=True, related_name="price_snapshots")
    captured_at = models.DateTimeField(auto_now_add=True)

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

class CustomerPortalToken(models.Model):
    token = models.CharField(max_length=80, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="portal_tokens")
    expires_at = models.DateTimeField()
    active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="issued_portal_tokens")
    created_at = models.DateTimeField(auto_now_add=True)

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


class DemandHistory(models.Model):
    SOURCE_CHOICES = [("sales", "Sales history"), ("manual", "Manual import"), ("adjustment", "Stock adjustment")]
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="demand_history")
    warehouse = models.ForeignKey(Warehouse, on_delete=models.SET_NULL, null=True, blank=True, related_name="demand_history")
    period_start = models.DateField()
    quantity = models.PositiveIntegerField(default=0)
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default="sales")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-period_start"]
        unique_together = [("product", "warehouse", "period_start")]


class PurchasePlan(models.Model):
    STATUS_CHOICES = [("pending", "Pending approval"), ("approved", "Approved"), ("rejected", "Rejected"), ("ordered", "PO created")]
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="purchase_plans")
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name="purchase_plans")
    average_daily_demand = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    window_days = models.PositiveIntegerField(default=90)
    horizon_days = models.PositiveIntegerField(default=30)
    available_qty = models.IntegerField(default=0)
    safety_stock = models.PositiveIntegerField(default=0)
    reorder_point = models.PositiveIntegerField(default=0)
    recommended_qty = models.PositiveIntegerField(default=0)
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    estimated_cost = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    projected_stockout = models.DateField(null=True, blank=True)
    expected_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    requested_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="purchase_plans_requested")
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="purchase_plans_reviewed")
    purchase_order = models.OneToOneField(PurchaseOrder, on_delete=models.SET_NULL, null=True, blank=True, related_name="purchase_plan")
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)


class RFQ(models.Model):
    STATUS_CHOICES = [("sent", "Sent"), ("quoted", "Quotes received"), ("selected", "Offer selected"), ("closed", "Closed")]
    rfq_no = models.CharField(max_length=30, unique=True)
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="rfqs")
    purchase_plan = models.ForeignKey(PurchasePlan, on_delete=models.SET_NULL, null=True, blank=True, related_name="rfqs")
    quantity = models.PositiveIntegerField()
    needed_by = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="sent")
    notes = models.CharField(max_length=300, blank=True)
    requested_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="rfqs_requested")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class RFQOffer(models.Model):
    STATUS_CHOICES = [("pending", "Awaiting quote"), ("received", "Quote received"), ("selected", "Selected"), ("rejected", "Rejected")]
    rfq = models.ForeignKey(RFQ, on_delete=models.CASCADE, related_name="offers")
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name="rfq_offers")
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    lead_time_days = models.PositiveIntegerField(default=0)
    moq = models.PositiveIntegerField(default=1)
    available_qty = models.PositiveIntegerField(default=0)
    payment_terms = models.CharField(max_length=80, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    notes = models.CharField(max_length=240, blank=True)
    responded_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["unit_price", "lead_time_days"]
        unique_together = [("rfq", "supplier")]


# Persistent enterprise operations models. These replace the hard-coded demo
# responses used by the enterprise workspace while keeping the response shape
# consumed by the existing React screens.
class IntegrationConnection(models.Model):
    TYPE_CHOICES = [("accounting", "Accounting"), ("messaging", "Messaging"), ("shipping", "Shipping"), ("payments", "Payments"), ("webhook", "Webhook")]
    STATUS_CHOICES = [("connected", "Connected"), ("attention", "Needs attention"), ("available", "Available"), ("disabled", "Disabled")]
    name = models.CharField(max_length=120)
    integration_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default="webhook")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="available")
    last_sync = models.DateTimeField(null=True, blank=True)
    records = models.PositiveIntegerField(default=0)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="integration_connections")
    created_at = models.DateTimeField(auto_now_add=True)


class WebhookSubscription(models.Model):
    STATUS_CHOICES = [("active", "Active"), ("paused", "Paused"), ("failed", "Failed")]
    connection = models.ForeignKey(IntegrationConnection, on_delete=models.CASCADE, null=True, blank=True, related_name="webhooks")
    event = models.CharField(max_length=100)
    target = models.URLField(max_length=300)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")
    deliveries = models.PositiveIntegerField(default=0)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="webhook_subscriptions")
    created_at = models.DateTimeField(auto_now_add=True)


class IntegrationLog(models.Model):
    connection = models.ForeignKey(IntegrationConnection, on_delete=models.SET_NULL, null=True, blank=True, related_name="logs")
    event = models.CharField(max_length=120)
    target = models.CharField(max_length=300, blank=True)
    status = models.CharField(max_length=20, default="delivered")
    detail = models.CharField(max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class PwaDevice(models.Model):
    STATUS_CHOICES = [("online", "Online"), ("offline", "Offline"), ("blocked", "Blocked")]
    name = models.CharField(max_length=140)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.SET_NULL, null=True, blank=True, related_name="pwa_devices")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="offline")
    app_version = models.CharField(max_length=30, blank=True)
    last_seen = models.DateTimeField(null=True, blank=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)


class SyncConflict(models.Model):
    STATUS_CHOICES = [("needs_review", "Needs review"), ("resolved", "Resolved")]
    device = models.ForeignKey(PwaDevice, on_delete=models.CASCADE, related_name="conflicts")
    reference = models.CharField(max_length=80)
    field = models.CharField(max_length=80)
    local_value = models.CharField(max_length=240)
    server_value = models.CharField(max_length=240)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="needs_review")
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="resolved_sync_conflicts")
    resolved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class AutomationRule(models.Model):
    STATUS_CHOICES = [("active", "Active"), ("paused", "Paused")]
    name = models.CharField(max_length=140)
    trigger = models.CharField(max_length=120)
    action = models.CharField(max_length=160)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")
    runs = models.PositiveIntegerField(default=0)
    last_run = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="automation_rules")
    created_at = models.DateTimeField(auto_now_add=True)


class AutomationRun(models.Model):
    rule = models.ForeignKey(AutomationRule, on_delete=models.CASCADE, related_name="run_history")
    result = models.CharField(max_length=20, default="success")
    detail = models.CharField(max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class FleetVehicle(models.Model):
    STATUS_CHOICES = [("healthy", "Healthy"), ("due_soon", "Due soon"), ("overdue", "Overdue")]
    registration = models.CharField(max_length=30, unique=True)
    customer = models.CharField(max_length=140)
    make = models.CharField(max_length=80)
    model = models.CharField(max_length=80)
    year = models.PositiveIntegerField(default=2022)
    mileage = models.PositiveIntegerField(default=0)
    next_service = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="healthy")
    created_at = models.DateTimeField(auto_now_add=True)


class FleetWorkOrder(models.Model):
    STATUS_CHOICES = [("scheduled", "Scheduled"), ("in_progress", "In progress"), ("completed", "Completed"), ("cancelled", "Cancelled")]
    order_no = models.CharField(max_length=40, unique=True)
    vehicle = models.ForeignKey(FleetVehicle, on_delete=models.SET_NULL, null=True, blank=True, related_name="work_orders")
    registration = models.CharField(max_length=30)
    customer = models.CharField(max_length=140)
    technician = models.CharField(max_length=120, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="scheduled")
    due_date = models.DateField()
    parts_value = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    labor_value = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = models.CharField(max_length=300, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="fleet_work_orders")
    created_at = models.DateTimeField(auto_now_add=True)


class SupportTicket(models.Model):
    STATUS_CHOICES = [("open", "Open"), ("in_progress", "In progress"), ("pending_customer", "Pending customer"), ("escalated", "Escalated"), ("resolved", "Resolved")]
    PRIORITY_CHOICES = [("normal", "Normal"), ("high", "High"), ("urgent", "Urgent")]
    ticket_no = models.CharField(max_length=40, unique=True)
    customer = models.CharField(max_length=140)
    subject = models.CharField(max_length=200)
    channel = models.CharField(max_length=40, default="portal")
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default="normal")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="open")
    assignee = models.CharField(max_length=120, blank=True)
    sla_due = models.DateTimeField(null=True, blank=True)
    last_message = models.CharField(max_length=300, blank=True)
    messages = models.PositiveIntegerField(default=1)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="support_tickets")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class SupportCommunication(models.Model):
    ticket = models.ForeignKey(SupportTicket, on_delete=models.CASCADE, related_name="communications")
    actor = models.CharField(max_length=120)
    channel = models.CharField(max_length=40)
    message = models.CharField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)


class DeliveryRoute(models.Model):
    STATUS_CHOICES = [("planned", "Planned"), ("in_transit", "In transit"), ("delivered", "Delivered"), ("cancelled", "Cancelled")]
    route_no = models.CharField(max_length=40, unique=True)
    driver = models.CharField(max_length=120)
    vehicle = models.CharField(max_length=80)
    stops = models.PositiveIntegerField(default=1)
    completed = models.PositiveIntegerField(default=0)
    eta = models.CharField(max_length=40, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="planned")
    cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="delivery_routes")
    created_at = models.DateTimeField(auto_now_add=True)


class Shipment(models.Model):
    STATUS_CHOICES = [("planned", "Planned"), ("in_transit", "In transit"), ("delivered", "Delivered"), ("exception", "Exception")]
    POD_CHOICES = [("pending", "Pending"), ("verified", "Verified")]
    shipment_no = models.CharField(max_length=40, unique=True)
    route = models.ForeignKey(DeliveryRoute, on_delete=models.SET_NULL, null=True, blank=True, related_name="shipments")
    customer = models.CharField(max_length=140)
    order_no = models.CharField(max_length=40, blank=True)
    driver = models.CharField(max_length=120, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="planned")
    eta = models.DateTimeField(null=True, blank=True)
    pod_status = models.CharField(max_length=20, choices=POD_CHOICES, default="pending")
    value = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    proof_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class Organization(models.Model):
    PLAN_CHOICES = [("starter", "Starter"), ("growth", "Growth"), ("scale", "Scale")]
    name = models.CharField(max_length=160)
    slug = models.SlugField(max_length=80, unique=True)
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES, default="growth")
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class OrganizationMembership(models.Model):
    ROLE_CHOICES = Profile.ROLE_CHOICES
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="organization_memberships")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="sales")
    approval_limit = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["organization", "user"], name="unique_organization_membership")]


class OrganizationInvitation(models.Model):
    STATUS_CHOICES = [("pending", "Pending"), ("accepted", "Accepted"), ("expired", "Expired"), ("cancelled", "Cancelled")]
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="invitations")
    email = models.EmailField()
    role = models.CharField(max_length=20, choices=Profile.ROLE_CHOICES, default="store")
    branch = models.ForeignKey(Warehouse, on_delete=models.SET_NULL, null=True, blank=True, related_name="organization_invitations")
    approval_limit = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    token = models.CharField(max_length=80, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    invited_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="organization_invitations_sent")
    created_at = models.DateTimeField(auto_now_add=True)


# Tenant ownership is added to the existing branch and enterprise records in
# one place so every new enterprise feature has the same isolation boundary.
for _tenant_model in [
    Warehouse, IntegrationConnection, WebhookSubscription, IntegrationLog,
    PwaDevice, SyncConflict, AutomationRule, AutomationRun, FleetVehicle, FleetWorkOrder,
    SupportTicket, SupportCommunication, DeliveryRoute, Shipment,
]:
    _tenant_model.add_to_class("organization", models.ForeignKey(Organization, on_delete=models.CASCADE, null=True, blank=True, related_name=f"{_tenant_model.__name__.lower()}_records"))


class StockLedgerEntry(models.Model):
    MOVEMENT_CHOICES = [("in", "Stock in"), ("out", "Stock out"), ("adjustment", "Adjustment"), ("reserve", "Reserve"), ("release", "Release")]
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, null=True, blank=True, related_name="stock_ledger")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="ledger_entries")
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, null=True, blank=True, related_name="ledger_entries")
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_CHOICES)
    quantity = models.IntegerField()
    balance_qty = models.IntegerField()
    reference = models.CharField(max_length=80, blank=True)
    idempotency_key = models.CharField(max_length=100, unique=True, null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="stock_ledger_entries")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class StockReservation(models.Model):
    STATUS_CHOICES = [("active", "Active"), ("released", "Released"), ("fulfilled", "Fulfilled"), ("cancelled", "Cancelled")]
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, null=True, blank=True, related_name="stock_reservations")
    sales_order = models.ForeignKey(SalesOrder, on_delete=models.CASCADE, related_name="stock_reservations")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="stock_reservations")
    quantity = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")
    idempotency_key = models.CharField(max_length=100, unique=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    released_at = models.DateTimeField(null=True, blank=True)
