import json
from datetime import date, timedelta
from decimal import Decimal
from math import ceil
from uuid import uuid4
from django.contrib.auth import authenticate
from django.db import transaction
from django.db.models import Count, DecimalField, ExpressionWrapper, F, Q, Sum
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from .auth import api_login_required, issue_token, roles_allowed
from .models import Product, Quotation, StockMovement, Supplier, SupplierContract, VehicleFitment, PurchaseOrder, PurchaseOrderItem, GoodsReceipt, GoodsReceiptLine, SupplierInvoice, Warehouse, WarehouseStock, StockTransfer, SalesOrder, SalesOrderItem, Invoice, Payment, ReturnRequest, InventoryCount, InventoryCountLine, ProductLot, SupplierPriceSnapshot, Customer, CustomerPortalToken, PriceRule, Notification, ApprovalRequest, AuditLog, DemandHistory, PurchasePlan, RFQ, RFQOffer
from .serializers import product_dict, quotation_dict, supplier_dict

ROLE_MODULES = {
    "admin": ["dashboard", "inventory", "quotations", "suppliers", "stock", "barcodes", "fitments", "purchase_orders", "receiving", "mobile_warehouse", "warehouses", "reorder", "demand_planning", "rfq", "sales_flow", "fulfillment", "notifications", "copilot", "finance", "warranty_intelligence", "integrations", "pwa_admin", "tenancy", "automation", "fleet", "security", "documents", "delivery", "partner_api", "predictive_fleet", "returns", "inventory_control", "supplier_performance", "portal", "crm", "pricing", "analytics", "governance"],
    "manager": ["dashboard", "inventory", "quotations", "suppliers", "stock", "barcodes", "fitments", "purchase_orders", "receiving", "mobile_warehouse", "warehouses", "reorder", "demand_planning", "rfq", "sales_flow", "fulfillment", "notifications", "copilot", "finance", "warranty_intelligence", "integrations", "pwa_admin", "tenancy", "automation", "fleet", "security", "documents", "delivery", "partner_api", "predictive_fleet", "returns", "inventory_control", "supplier_performance", "portal", "crm", "pricing", "analytics", "governance"],
    "sales": ["dashboard", "inventory", "quotations", "barcodes", "fitments", "sales_flow", "fulfillment", "notifications", "copilot", "finance", "warranty_intelligence", "integrations", "fleet", "security", "delivery", "partner_api", "predictive_fleet", "returns", "portal", "crm", "pricing", "analytics", "governance"],
    "store": ["dashboard", "inventory", "stock", "barcodes", "fitments", "purchase_orders", "receiving", "mobile_warehouse", "warehouses", "reorder", "demand_planning", "rfq", "sales_flow", "fulfillment", "notifications", "copilot", "warranty_intelligence", "pwa_admin", "automation", "fleet", "security", "documents", "delivery", "predictive_fleet", "returns", "inventory_control", "supplier_performance", "governance"],
}

def parse_body(request):
    try:
        return json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return None

def record_audit(request, action, entity, entity_id="", detail=""):
    try:
        AuditLog.objects.create(user=getattr(request, "api_user", None), action=action, entity=entity, entity_id=str(entity_id or ""), detail=str(detail or "")[:300])
    except Exception:
        pass

def health(request):
    return JsonResponse({"status": "ok", "service": "partora-api"})

@csrf_exempt
def login_view(request):
    if request.method != "POST":
        return JsonResponse({"detail": "POST required"}, status=405)
    data = parse_body(request)
    if data is None:
        return JsonResponse({"detail": "Invalid JSON"}, status=400)
    email = str(data.get("email", "")).strip().lower()
    password = data.get("password", "")
    user = authenticate(request, username=email, password=password)
    if not user:
        return JsonResponse({"detail": "Invalid email or password"}, status=401)
    role = user.profile.role
    return JsonResponse({
        "token": issue_token(user),
        "user": {"id": user.id, "name": user.get_full_name() or email.split("@")[0].title(), "email": user.email or email, "role": role},
        "modules": ROLE_MODULES[role],
    })

@api_login_required
def me_view(request):
    user = request.api_user
    role = user.profile.role
    return JsonResponse({
        "user": {"id": user.id, "name": user.get_full_name() or user.username, "email": user.email, "role": role},
        "modules": ROLE_MODULES[role],
    })

@api_login_required
def dashboard_view(request):
    role = request.api_user.profile.role
    inventory_value = ExpressionWrapper(F("price") * F("stock_qty"), output_field=DecimalField(max_digits=16, decimal_places=2))
    total_inventory_value = Product.objects.aggregate(total=Sum(inventory_value))["total"] or 0
    data = {
        "role": role,
        "metrics": {
            "products": Product.objects.count(),
            "low_stock": Product.objects.filter(stock_qty__lte=10).count(),
            "open_quotes": Quotation.objects.filter(status__in=["draft", "sent"]).count(),
            "suppliers": Supplier.objects.filter(active=True).count(),
            "catalog_value": float(total_inventory_value),
        },
        "recent_quotes": [quotation_dict(q) for q in Quotation.objects.order_by("-created_at")[:4]],
        "low_stock_items": [product_dict(p) for p in Product.objects.filter(stock_qty__lte=10).order_by("stock_qty")[:5]],
    }
    return JsonResponse(data)

@csrf_exempt
@api_login_required
def inventory_view(request):
    if request.method == "GET":
        qs = Product.objects.select_related("supplier").all().order_by("name")
        q = request.GET.get("q", "").strip()
        if q:
            qs = qs.filter(Q(sku__icontains=q) | Q(name__icontains=q) | Q(brand__icontains=q) | Q(category__icontains=q) | Q(supplier__name__icontains=q))
        return JsonResponse({"items": [product_dict(p) for p in qs[:250]], "count": qs.count()})
    if request.method == "POST":
        if request.api_user.profile.role not in {"admin", "manager"}:
            return JsonResponse({"detail": "Only admin or manager can add inventory"}, status=403)
        data = parse_body(request)
        if data is None:
            return JsonResponse({"detail": "Invalid JSON"}, status=400)
        required = ["sku", "name", "brand", "category", "price"]
        if any(not str(data.get(k, "")).strip() for k in required):
            return JsonResponse({"detail": "SKU, name, brand, category and price are required"}, status=400)
        supplier = None
        if str(data.get("supplier", "")).strip():
            supplier, _ = Supplier.objects.get_or_create(name=str(data["supplier"]).strip())
        try:
            product = Product.objects.create(
                sku=str(data["sku"]).strip().upper(), name=str(data["name"]).strip(), brand=str(data["brand"]).strip(),
                category=str(data["category"]).strip(), supplier=supplier, price=float(data["price"]),
                stock_qty=int(data.get("stock_qty", 0)), reorder_level=int(data.get("reorder_level", 10)),
                bin_location=str(data.get("bin_location", "")).strip(),
            )
        except Exception as exc:
            return JsonResponse({"detail": f"Could not add product: {exc}"}, status=400)
        record_audit(request, "create", "product", product.id, product.sku)
        return JsonResponse({"item": product_dict(product)}, status=201)
    return JsonResponse({"detail": "Method not allowed"}, status=405)

@csrf_exempt
@roles_allowed("admin", "manager")
def suppliers_view(request):
    if request.method == "GET":
        qs = Supplier.objects.order_by("name")
        return JsonResponse({"items": [supplier_dict(s) for s in qs], "count": qs.count()})
    if request.method == "POST":
        data = parse_body(request)
        if data is None or not str(data.get("name", "")).strip():
            return JsonResponse({"detail": "Supplier name is required"}, status=400)
        supplier = Supplier.objects.create(
            name=str(data["name"]).strip(), contact_name=str(data.get("contact_name", "")).strip(),
            phone=str(data.get("phone", "")).strip(), email=str(data.get("email", "")).strip(),
            lead_time_days=int(data.get("lead_time_days", 3)), rating=float(data.get("rating", 4.0)), active=True,
        )
        record_audit(request, "create", "supplier", supplier.id, supplier.name)
        return JsonResponse({"item": supplier_dict(supplier)}, status=201)
    return JsonResponse({"detail": "Method not allowed"}, status=405)

@csrf_exempt
@roles_allowed("admin", "manager", "sales")
def quotations_view(request):
    if request.method == "GET":
        qs = Quotation.objects.select_related("created_by").order_by("-created_at")
        return JsonResponse({"items": [quotation_dict(q) for q in qs], "count": qs.count()})
    if request.method == "POST":
        data = parse_body(request)
        if data is None or not str(data.get("customer_name", "")).strip():
            return JsonResponse({"detail": "Customer name is required"}, status=400)
        try:
            valid_until = date.fromisoformat(str(data["valid_until"])) if data.get("valid_until") else timezone.localdate()
            quote = Quotation.objects.create(
                quote_no=f"QT-{timezone.now():%y%m%d}-{uuid4().hex[:4].upper()}",
                customer_name=str(data["customer_name"]).strip(), customer_company=str(data.get("customer_company", "")).strip(),
                total=float(data.get("total", 0)), status=str(data.get("status", "draft")),
                valid_until=valid_until, created_by=request.api_user,
            )
        except Exception as exc:
            return JsonResponse({"detail": f"Could not create quotation: {exc}"}, status=400)
        record_audit(request, "create", "quotation", quote.id, quote.quote_no)
        return JsonResponse({"item": quotation_dict(quote)}, status=201)
    return JsonResponse({"detail": "Method not allowed"}, status=405)

@csrf_exempt
@roles_allowed("admin", "manager", "store")
def stock_view(request):
    if request.method == "GET":
        movements = StockMovement.objects.select_related("product").order_by("-created_at")[:25]
        return JsonResponse({"items": [{
            "id": m.id, "sku": m.product.sku, "product": m.product.name, "type": m.movement_type,
            "quantity": m.quantity, "reference": m.reference, "created_at": m.created_at.isoformat(),
        } for m in movements]})
    if request.method == "POST":
        data = parse_body(request)
        if data is None:
            return JsonResponse({"detail": "Invalid JSON"}, status=400)
        try:
            product = Product.objects.get(sku=str(data.get("sku", "")).strip().upper())
            movement_type = str(data.get("type", "in"))
            quantity = abs(int(data.get("quantity", 0)))
            if quantity == 0:
                raise ValueError("Quantity must be greater than zero")
            if movement_type == "in":
                product.stock_qty += quantity
            elif movement_type == "out":
                product.stock_qty = max(0, product.stock_qty - quantity)
            elif movement_type == "adjustment":
                product.stock_qty = quantity
            else:
                raise ValueError("Invalid movement type")
            product.save(update_fields=["stock_qty", "updated_at"])
            movement = StockMovement.objects.create(product=product, movement_type=movement_type, quantity=quantity, reference=str(data.get("reference", "")).strip())
        except Exception as exc:
            return JsonResponse({"detail": f"Could not record stock movement: {exc}"}, status=400)
        record_audit(request, "stock movement", "product", product.id, f"{movement_type} {quantity} / {movement.reference}")
        return JsonResponse({"item": {
            "id": movement.id, "sku": product.sku, "product": product.name, "type": movement.movement_type,
            "quantity": movement.quantity, "reference": movement.reference, "created_at": movement.created_at.isoformat(),
        }}, status=201)
    return JsonResponse({"detail": "Method not allowed"}, status=405)

@csrf_exempt
@api_login_required
def barcodes_view(request):
    if request.method == "GET":
        q = request.GET.get("q", "").strip()
        qs = Product.objects.select_related("supplier").exclude(barcode__isnull=True).exclude(barcode="")
        if q:
            qs = qs.filter(Q(barcode__icontains=q) | Q(sku__icontains=q) | Q(name__icontains=q))
        return JsonResponse({"items": [product_dict(p) for p in qs.order_by("name")[:200]]})
    if request.method == "POST":
        data = parse_body(request)
        if data is None:
            return JsonResponse({"detail": "Invalid JSON"}, status=400)
        try:
            product = Product.objects.get(sku=str(data.get("sku", "")).strip().upper())
            code = str(data.get("barcode", "")).strip() or f"PARTORA-{product.sku}"
            product.barcode = code
            product.save(update_fields=["barcode", "updated_at"])
        except Exception as exc:
            return JsonResponse({"detail": f"Could not assign barcode: {exc}"}, status=400)
        record_audit(request, "create", "product", product.id, product.sku)
        return JsonResponse({"item": product_dict(product)}, status=201)
    return JsonResponse({"detail": "Method not allowed"}, status=405)

@api_login_required
def barcode_lookup_view(request):
    code = request.GET.get("code", "").strip()
    try:
        product = Product.objects.select_related("supplier").get(Q(barcode=code) | Q(sku__iexact=code))
    except Product.DoesNotExist:
        return JsonResponse({"detail": "Part not found"}, status=404)
    return JsonResponse({"item": product_dict(product)})

@csrf_exempt
@api_login_required
def fitments_view(request):
    if request.method == "GET":
        q = request.GET.get("q", "").strip()
        qs = VehicleFitment.objects.select_related("product").order_by("make", "model", "year_from")
        if q:
            qs = qs.filter(Q(make__icontains=q) | Q(model__icontains=q) | Q(variant__icontains=q) | Q(engine__icontains=q) | Q(oem_number__icontains=q) | Q(product__sku__icontains=q) | Q(product__name__icontains=q))
        items = [{"id": f.id, "sku": f.product.sku, "product": f.product.name, "make": f.make, "model": f.model, "year_from": f.year_from, "year_to": f.year_to, "variant": f.variant, "engine": f.engine, "oem_number": f.oem_number} for f in qs[:250]]
        return JsonResponse({"items": items, "count": qs.count()})
    if request.method == "POST":
        data = parse_body(request) or {}
        if str(data.get("action", "")) == "decode_vin":
            vin = str(data.get("vin", "")).replace(" ", "").upper()
            vehicle_map = {
                "MA3EJKD1S00A12345": {"make": "Maruti Suzuki", "model": "Swift", "year": 2022, "variant": "Petrol / AMT", "engine": "1.2L", "fuel": "Petrol"},
                "MALBB51BLNM123456": {"make": "Hyundai", "model": "i20", "year": 2023, "variant": "Sportz", "engine": "1.2L", "fuel": "Petrol"},
            }
            vehicle = vehicle_map.get(vin) if len(vin) >= 8 else None
            if not vehicle:
                return JsonResponse({"detail": "Enter a supported demo VIN or a valid 8+ character VIN"}, status=400)
            matches = VehicleFitment.objects.select_related("product").filter(make=vehicle["make"], model=vehicle["model"], year_from__lte=vehicle["year"], year_to__gte=vehicle["year"])
            result = [{"id": f.id, "sku": f.product.sku, "product": f.product.name, "make": f.make, "model": f.model, "year_from": f.year_from, "year_to": f.year_to, "variant": f.variant, "engine": f.engine, "oem_number": f.oem_number, "stock_qty": f.product.stock_qty, "stock_status": "out" if f.product.stock_qty <= 0 else "low" if f.product.stock_qty <= f.product.reorder_level else "healthy", "fitment_confidence": "98%" if f.oem_number else "92%"} for f in matches]
            return JsonResponse({"item": {"vin": vin, "vehicle": vehicle, "matches": result}})
        try:
            product = Product.objects.get(sku=str(data.get("sku", "")).strip().upper())
            fitment = VehicleFitment.objects.create(product=product, make=str(data["make"]).strip(), model=str(data["model"]).strip(), year_from=int(data["year_from"]), year_to=int(data.get("year_to") or data["year_from"]), variant=str(data.get("variant", "")).strip(), engine=str(data.get("engine", "")).strip(), oem_number=str(data.get("oem_number", "")).strip())
        except Exception as exc:
            return JsonResponse({"detail": f"Could not add fitment: {exc}"}, status=400)
        return JsonResponse({"item": {"id": fitment.id, "sku": product.sku, "product": product.name, "make": fitment.make, "model": fitment.model, "year_from": fitment.year_from, "year_to": fitment.year_to, "variant": fitment.variant, "engine": fitment.engine, "oem_number": fitment.oem_number}}, status=201)
    return JsonResponse({"detail": "Method not allowed"}, status=405)

@csrf_exempt
@roles_allowed("admin", "manager", "store")
def purchase_orders_view(request):
    if request.method == "GET":
        qs = PurchaseOrder.objects.select_related("supplier", "created_by").prefetch_related("items__product").order_by("-created_at")
        items=[]
        for po in qs[:100]:
            items.append({"id":po.id,"po_no":po.po_no,"supplier":po.supplier.name,"status":po.status,"expected_date":po.expected_date.isoformat() if po.expected_date else None,"total":float(po.total),"created_by":(po.created_by.get_full_name() or po.created_by.username) if po.created_by else "System","line_count":po.items.count(),"received_lines":sum(1 for i in po.items.all() if i.received_qty >= i.quantity)})
        return JsonResponse({"items":items,"count":qs.count()})
    if request.method == "POST":
        data=parse_body(request) or {}
        action=str(data.get("action","create"))
        if action == "receive":
            try:
                po=PurchaseOrder.objects.prefetch_related("items__product").get(id=int(data["id"]))
                for line in po.items.all():
                    remaining=max(0,line.quantity-line.received_qty)
                    if remaining:
                        line.received_qty += remaining; line.save(update_fields=["received_qty"])
                        line.product.stock_qty += remaining; line.product.save(update_fields=["stock_qty","updated_at"])
                        StockMovement.objects.create(product=line.product,movement_type="in",quantity=remaining,reference=po.po_no)
                po.status="received"; po.received_at=timezone.now(); po.save(update_fields=["status","received_at"])
            except Exception as exc:
                return JsonResponse({"detail":f"Could not receive purchase order: {exc}"},status=400)
            return JsonResponse({"item":{"id":po.id,"po_no":po.po_no,"supplier":po.supplier.name,"status":po.status,"expected_date":po.expected_date.isoformat() if po.expected_date else None,"total":float(po.total),"line_count":po.items.count(),"received_lines":po.items.count()}})
        try:
            supplier=Supplier.objects.get(name=str(data.get("supplier","")).strip())
            expected=date.fromisoformat(str(data["expected_date"])) if data.get("expected_date") else None
            product=Product.objects.get(sku=str(data.get("sku","")).strip().upper())
            qty=max(1,int(data.get("quantity",1))); unit_cost=float(data.get("unit_cost") or product.price)
            po=PurchaseOrder.objects.create(po_no=f"PO-{timezone.now():%y%m%d}-{uuid4().hex[:4].upper()}",supplier=supplier,status=str(data.get("status","draft")),expected_date=expected,total=qty*unit_cost,created_by=request.api_user)
            PurchaseOrderItem.objects.create(purchase_order=po,product=product,quantity=qty,unit_cost=unit_cost)
            SupplierPriceSnapshot.objects.create(supplier=supplier,product=product,unit_cost=unit_cost,source_po=po)
        except Exception as exc:
            return JsonResponse({"detail":f"Could not create purchase order: {exc}"},status=400)
        return JsonResponse({"item":{"id":po.id,"po_no":po.po_no,"supplier":po.supplier.name,"status":po.status,"expected_date":po.expected_date.isoformat() if po.expected_date else None,"total":float(po.total),"created_by":request.api_user.get_full_name() or request.api_user.username,"line_count":1,"received_lines":0}},status=201)
    return JsonResponse({"detail":"Method not allowed"},status=405)

def receiving_po_dict(po):
    items=[]
    accepted_total=0; damaged_total=0; ordered_total=0
    for line in po.items.select_related("product").all():
        accepted=GoodsReceiptLine.objects.filter(purchase_order_item=line).aggregate(total=Sum("accepted_qty"))["total"] or 0
        damaged=GoodsReceiptLine.objects.filter(purchase_order_item=line).aggregate(total=Sum("damaged_qty"))["total"] or 0
        ordered_total += line.quantity; accepted_total += accepted; damaged_total += damaged
        items.append({"id":line.id,"sku":line.product.sku,"product":line.product.name,"ordered_qty":line.quantity,"received_qty":line.received_qty,"accepted_qty":accepted,"damaged_qty":damaged,"remaining_qty":max(0,line.quantity-line.received_qty),"unit_cost":float(line.unit_cost)})
    invoices=[{"id":invoice.id,"invoice_no":invoice.invoice_no,"invoice_date":invoice.invoice_date.isoformat() if invoice.invoice_date else None,"invoice_qty":invoice.invoice_qty,"subtotal":float(invoice.subtotal),"tax":float(invoice.tax),"total":float(invoice.total),"status":invoice.status,"notes":invoice.notes,"created_by":(invoice.created_by.get_full_name() or invoice.created_by.username) if invoice.created_by else "System"} for invoice in po.supplier_invoices.select_related("created_by").all()]
    return {"id":po.id,"po_no":po.po_no,"supplier":po.supplier.name,"status":po.status,"expected_date":po.expected_date.isoformat() if po.expected_date else None,"total":float(po.total),"line_count":len(items),"ordered_qty":ordered_total,"accepted_qty":accepted_total,"damaged_qty":damaged_total,"remaining_qty":max(0,ordered_total-accepted_total-damaged_total),"items":items,"invoices":invoices}

@csrf_exempt
@roles_allowed("admin", "manager", "store")
def receiving_view(request):
    if request.method == "GET":
        qs=PurchaseOrder.objects.select_related("supplier").prefetch_related("items__product").order_by("-created_at")
        orders=[receiving_po_dict(po) for po in qs[:100]]
        invoices=[invoice for po in orders for invoice in po["invoices"]]
        return JsonResponse({"orders":orders,"invoices":invoices,"summary":{"purchase_orders":len(orders),"awaiting_receipt":sum(1 for po in orders if po["remaining_qty"]>0 and po["status"] in {"approved","ordered","partial"}),"damaged_units":sum(po["damaged_qty"] for po in orders),"invoice_exceptions":sum(1 for invoice in invoices if invoice["status"]=="exception")}})
    if request.method != "POST": return JsonResponse({"detail":"Method not allowed"},status=405)
    data=parse_body(request) or {}; action=str(data.get("action","receive"))
    try:
        if action == "receive":
            with transaction.atomic():
                po=PurchaseOrder.objects.select_related("supplier").prefetch_related("items__product").select_for_update().get(id=int(data["po_id"]))
                requested=data.get("lines") or [{"item_id":line.id,"accepted_qty":max(0,line.quantity-line.received_qty),"damaged_qty":0} for line in po.items.all() if line.quantity>line.received_qty]
                if not requested: raise ValueError("This purchase order has no remaining quantity")
                receipt=GoodsReceipt.objects.create(receipt_no=f"GRN-{timezone.now():%y%m%d}-{uuid4().hex[:4].upper()}",purchase_order=po,notes=str(data.get("notes",""))[:300],received_by=request.api_user)
                posted=0
                for raw in requested:
                    line=PurchaseOrderItem.objects.select_related("product").select_for_update().get(id=int(raw["item_id"]),purchase_order=po)
                    accepted=max(0,int(raw.get("accepted_qty",0) or 0)); damaged=max(0,int(raw.get("damaged_qty",0) or 0)); total_qty=accepted+damaged; remaining=max(0,line.quantity-line.received_qty)
                    if total_qty<=0: continue
                    if total_qty>remaining: raise ValueError(f"Receipt exceeds remaining quantity for {line.product.sku}")
                    GoodsReceiptLine.objects.create(receipt=receipt,purchase_order_item=line,accepted_qty=accepted,damaged_qty=damaged,notes=str(raw.get("notes",""))[:240])
                    line.received_qty += total_qty; line.save(update_fields=["received_qty"])
                    if accepted:
                        line.product.stock_qty += accepted; line.product.save(update_fields=["stock_qty","updated_at"])
                        StockMovement.objects.create(product=line.product,movement_type="in",quantity=accepted,reference=receipt.receipt_no)
                    posted += total_qty
                if not posted: raise ValueError("Enter an accepted or damaged quantity")
                complete=all(line.received_qty>=line.quantity for line in po.items.all())
                po.status="received" if complete else "partial"; po.received_at=timezone.now(); po.save(update_fields=["status","received_at"])
            record_audit(request,"post goods receipt","goods receipt",receipt.id,receipt.receipt_no)
            return JsonResponse({"item":receiving_po_dict(po)},status=201)
        if action == "invoice":
            po=PurchaseOrder.objects.select_related("supplier").prefetch_related("items__product").get(id=int(data["po_id"]))
            invoice_no=str(data["invoice_no"]).strip()
            if not invoice_no: raise ValueError("Supplier invoice number is required")
            invoice_qty=max(0,int(data.get("invoice_qty",0) or 0)); total=Decimal(str(data.get("total",0) or 0)); tax=Decimal(str(data.get("tax",0) or 0)); subtotal=Decimal(str(data.get("subtotal",total-tax) or 0))
            accepted=sum(GoodsReceiptLine.objects.filter(purchase_order_item__purchase_order=po).values_list("accepted_qty",flat=True)); ordered=sum(line.quantity for line in po.items.all()); unit_total=po.total / ordered if ordered else Decimal("0"); expected_total=(unit_total*invoice_qty).quantize(Decimal("0.01")); status="matched" if invoice_qty>0 and invoice_qty<=accepted and abs(total-expected_total)<=Decimal("0.01") else "exception"
            invoice=SupplierInvoice.objects.create(invoice_no=invoice_no,purchase_order=po,supplier=po.supplier,invoice_date=date.fromisoformat(str(data["invoice_date"])) if data.get("invoice_date") else timezone.localdate(),invoice_qty=invoice_qty,subtotal=subtotal,tax=tax,total=total,status=status,notes=str(data.get("notes",""))[:300],created_by=request.api_user)
            record_audit(request,"record supplier invoice","supplier invoice",invoice.id,f"{invoice.invoice_no} ({invoice.status})")
            return JsonResponse({"item":receiving_po_dict(po),"invoice":{"id":invoice.id,"invoice_no":invoice.invoice_no,"status":invoice.status}},status=201)
        if action == "approve":
            if request.api_user.profile.role not in {"admin","manager"}: return JsonResponse({"detail":"Only admin or manager can approve supplier invoices"},status=403)
            invoice=SupplierInvoice.objects.get(id=int(data["invoice_id"])); invoice.status="approved"; invoice.approved_by=request.api_user; invoice.approved_at=timezone.now(); invoice.save(update_fields=["status","approved_by","approved_at"])
            record_audit(request,"approve supplier invoice","supplier invoice",invoice.id,invoice.invoice_no)
            return JsonResponse({"item":{"id":invoice.id,"invoice_no":invoice.invoice_no,"status":invoice.status}})
        raise ValueError("Unknown receiving action")
    except Exception as exc:
        return JsonResponse({"detail":f"Could not complete receiving action: {exc}"},status=400)

@csrf_exempt
@roles_allowed("admin", "manager", "store")
def mobile_warehouse_view(request):
    if request.method == "GET":
        tasks=[]
        for movement in StockMovement.objects.select_related("product").order_by("-created_at")[:25]:
            tasks.append({"id": movement.id, "type": "receive" if movement.movement_type == "in" else "pick", "reference": movement.reference or f"SCAN-{movement.id}", "location": "DEL-MAIN", "sku": movement.product.sku, "product": movement.product.name, "quantity": movement.quantity, "status": "synced", "synced": True, "created_at": movement.created_at.isoformat()})
        return JsonResponse({"queue": tasks, "last_sync": timezone.now().isoformat()})
    data=parse_body(request) or {}; action=str(data.get("action", "scan"))
    try:
        if action == "scan":
            product=Product.objects.get(sku=str(data.get("sku", "")).strip().upper())
            item={"id": f"scan-{uuid4().hex[:8]}", "type": str(data.get("type", "count")), "reference": str(data.get("reference") or f"SCAN-{timezone.now():%y%m%d}-{uuid4().hex[:4].upper()}"), "location": str(data.get("location", "DEL-MAIN")), "sku": product.sku, "product": product.name, "quantity": max(1, int(data.get("quantity", 1))), "status": "queued", "synced": False, "created_at": timezone.now().isoformat()}
            record_audit(request, "mobile warehouse scan", "product", product.id, f"{item['type']} / {item['reference']}")
            return JsonResponse({"item": item}, status=201)
        if action == "sync":
            return JsonResponse({"item": {"last_sync": timezone.now().isoformat(), "synced": True}})
        return JsonResponse({"item": {"id": data.get("id"), "status": "complete"}})
    except Exception as exc:
        return JsonResponse({"detail": f"Could not process mobile warehouse action: {exc}"}, status=400)

@csrf_exempt
@roles_allowed("admin", "manager", "sales", "store")
def notifications_view(request):
    if request.method == "GET":
        qs=Notification.objects.filter(Q(user=request.api_user)|Q(user__isnull=True,role="")|Q(user__isnull=True,role=request.api_user.profile.role)).order_by("-created_at")[:100]
        items=[{"id":n.id,"channel":"email","audience":n.user.get_full_name() if n.user else (n.role or "Operations team"),"event":n.title,"status":"read" if n.read else "queued","detail":n.message,"created_at":n.created_at.isoformat()} for n in qs]
        return JsonResponse({"items":items,"templates":["RFQ response reminder","Purchase order dispatched","Delivery update","Invoice exception","Quote approval","Low-stock alert"]})
    data=parse_body(request) or {}
    try:
        item=Notification.objects.create(user=request.api_user,title=str(data.get("event", "Operational update"))[:140],message=str(data.get("detail", "Notification queued for delivery."))[:300])
        record_audit(request, "send notification", "notification", item.id, item.title)
        return JsonResponse({"item":{"id":item.id,"channel":data.get("channel", "email"),"audience":data.get("audience", "Operations team"),"event":item.title,"status":"queued","detail":item.message,"created_at":item.created_at.isoformat()}}, status=201)
    except Exception as exc:
        return JsonResponse({"detail": f"Could not queue notification: {exc}"}, status=400)

@csrf_exempt
@roles_allowed("admin", "manager", "sales", "store")
def copilot_view(request):
    suggestions=["Which parts may stock out this week?", "Which supplier has the best delivery performance?", "Why is warehouse stock below target?", "What invoices need manager approval?"]
    if request.method == "GET": return JsonResponse({"suggested_questions": suggestions, "messages": []})
    data=parse_body(request) or {}; question=str(data.get("question", "")).strip(); lower=question.lower()
    if not question: return JsonResponse({"detail":"Ask the copilot a question"}, status=400)
    answer="Partora recommends reviewing the demand plan, supplier scorecard and action queue before committing inventory or payment changes."; source="Operations command center"
    if "stock" in lower: answer="RLY-24V4 is the highest stock-out risk. Raise a replenishment plan for 90 units and confirm VoltEdge availability."; source="Demand planning + inventory"
    elif "supplier" in lower or "delivery" in lower: answer="TorqueLine leads on reliability in the current history. VoltEdge is faster but has an invoice exception to resolve."; source="Supplier intelligence + receiving"
    elif "warehouse" in lower: answer="Noida North is at 89% capacity. Move slow-moving stock before the next inbound receipt."; source="Warehouse control"
    elif "invoice" in lower or "payment" in lower: answer="VE-INV-8821 needs manager review because its invoice quantity includes damaged units."; source="Finance + three-way matching"
    item={"id":uuid4().hex[:8],"question":question,"answer":answer,"source":source,"confidence":"Demo analysis","created_at":timezone.now().isoformat()}
    record_audit(request, "copilot question", "operations", item["id"], question)
    return JsonResponse({"item":item})

@csrf_exempt
@roles_allowed("admin", "manager", "sales")
def finance_view(request):
    def invoice_item(invoice):
        paid=float(invoice.payments.aggregate(total=Sum("amount"))["total"] or 0); total=float(invoice.total); balance=max(0, total-paid)
        return {"id":invoice.id,"invoice_no":invoice.invoice_no,"customer":invoice.sales_order.customer_company or invoice.sales_order.customer_name,"total":total,"paid":paid,"balance":balance,"status":"paid" if balance==0 else "partial" if paid else invoice.status,"due_date":invoice.due_date.isoformat(),"gst":round(total*18/118,2)}
    if request.method == "GET":
        invoices=[invoice_item(i) for i in Invoice.objects.select_related("sales_order").prefetch_related("payments").order_by("-created_at")[:100]]
        return JsonResponse({"metrics":{"receivables":sum(i["balance"] for i in invoices),"payables":float(SupplierInvoice.objects.exclude(status="rejected").aggregate(total=Sum("total"))["total"] or 0),"overdue":sum(i["balance"] for i in invoices if i["due_date"] < timezone.localdate().isoformat() and i["balance"]),"gst_due":round(sum(i["gst"] for i in invoices),2),"reconciled":round(sum(1 for i in invoices if i["status"] in {"paid","partial"})/len(invoices)*100) if invoices else 0},"invoices":invoices,"payments":[{"id":p.id,"reference":p.reference,"invoice_no":p.invoice.invoice_no,"amount":float(p.amount),"method":p.method,"reconciled":True,"paid_at":p.paid_at.date().isoformat()} for p in Payment.objects.select_related("invoice").order_by("-paid_at")[:50]],"tax_summary":[{"label":"Output GST","value":round(sum(i["gst"] for i in invoices),2)},{"label":"Input GST","value":round(sum(i["gst"] for i in invoices)*.61,2)},{"label":"Net GST payable","value":round(sum(i["gst"] for i in invoices)*.39,2)}]})
    data=parse_body(request) or {}; action=str(data.get("action", "reconcile"))
    try:
        if action == "reconcile":
            invoice=Invoice.objects.select_related("sales_order").prefetch_related("payments").get(id=int(data["invoice_id"])); amount=Decimal(str(data.get("amount", invoice.total) or 0)); Payment.objects.create(invoice=invoice,amount=amount,method=str(data.get("method", "bank")),reference=str(data.get("reference", "")),created_by=request.api_user)
            paid=invoice.payments.aggregate(total=Sum("amount"))["total"] or 0; invoice.status="paid" if paid>=invoice.total else "partial"; invoice.save(update_fields=["status"]); record_audit(request,"reconcile payment","invoice",invoice.id,invoice.invoice_no); return JsonResponse({"item":invoice_item(invoice)})
        return JsonResponse({"item":{"format":data.get("format", "csv"),"filename":f"partora-finance-{timezone.localdate().isoformat()}.csv"}})
    except Exception as exc:
        return JsonResponse({"detail": f"Could not complete finance action: {exc}"}, status=400)

@csrf_exempt
@roles_allowed("admin", "manager", "sales", "store")
def warranty_view(request):
    def claim_item(item): return {"id":item.id,"claim_no":item.return_no,"sku":item.product.sku,"product":item.product.name,"customer":item.customer_name,"reason":item.reason,"status":item.status,"resolution":item.resolution,"supplier":item.product.supplier.name if item.product.supplier else "Unassigned","recovery_amount":float(item.refund_amount),"root_cause":item.inspection_notes or "Pending inspection","created_at":item.created_at.isoformat()}
    if request.method == "GET":
        claims=[claim_item(item) for item in ReturnRequest.objects.select_related("product__supplier").order_by("-created_at")[:100]]; return JsonResponse({"metrics":{"open_claims":sum(1 for x in claims if x["status"] not in {"resolved","rejected"}),"approval_queue":sum(1 for x in claims if x["status"] in {"requested","inspected"}),"supplier_recovery":sum(x["recovery_amount"] for x in claims),"return_rate":round(len(claims)/max(Product.objects.count(),1)*100,1)},"claims":claims})
    data=parse_body(request) or {}; action=str(data.get("action", "status"))
    try:
        item=ReturnRequest.objects.select_related("product__supplier").get(id=int(data["id"]))
        if action == "status": item.status=str(data.get("status", item.status)); item.resolution=str(data.get("resolution", item.resolution)); item.inspection_notes=str(data.get("root_cause", item.inspection_notes)); item.save(update_fields=["status","resolution","inspection_notes","updated_at"])
        elif action == "chargeback": item.refund_amount=Decimal(str(data.get("amount", item.refund_amount) or 0)); item.save(update_fields=["refund_amount","updated_at"])
        record_audit(request,"update warranty claim","return",item.id,item.return_no); return JsonResponse({"item":claim_item(item)})
    except Exception as exc:
        return JsonResponse({"detail": f"Could not update warranty claim: {exc}"}, status=400)

@csrf_exempt
@roles_allowed("admin", "manager", "store")
def integrations_view(request):
    if request.method == "GET":
        connections=[{"id":1,"name":"Zoho Books","type":"accounting","status":"connected","last_sync":timezone.now().isoformat(),"records":184},{"id":2,"name":"WhatsApp Business","type":"messaging","status":"connected","last_sync":timezone.now().isoformat(),"records":42},{"id":3,"name":"Shiprocket","type":"shipping","status":"attention","last_sync":(timezone.now()-timedelta(hours=1)).isoformat(),"records":18},{"id":4,"name":"Razorpay","type":"payments","status":"available","last_sync":None,"records":0}]
        logs=[{"id":a.id,"event":a.action,"target":"Partora webhook","status":"delivered","created_at":a.created_at.isoformat()} for a in AuditLog.objects.filter(action__icontains="integration").order_by("-created_at")[:20]]
        return JsonResponse({"connections":connections,"webhooks":[{"id":1,"event":"invoice.paid","target":"https://client.example/webhooks/partora","status":"active","deliveries":42}],"logs":logs})
    data=parse_body(request) or {}; action=str(data.get("action","connect"))
    item={"id":uuid4().hex[:8],"name":str(data.get("name","New connector")),"type":str(data.get("type","webhook")),"status":"connected","last_sync":timezone.now().isoformat(),"records":0}
    if action == "webhook": item={"id":uuid4().hex[:8],"event":str(data.get("event","invoice.paid")),"target":str(data.get("target","https://client.example/webhooks/partora")),"status":"active","deliveries":0}
    record_audit(request,"integration setup","integration",item["id"],item.get("name",item.get("event","webhook")))
    return JsonResponse({"item":item},status=201)

@csrf_exempt
@roles_allowed("admin", "manager", "store")
def pwa_admin_view(request):
    if request.method == "GET":
        return JsonResponse({"devices":[{"id":1,"name":"Kabir Store · Android","warehouse":"DEL-MAIN","status":"online","app_version":"1.4.0","last_seen":timezone.now().isoformat()},{"id":2,"name":"Receiving Tablet · iPad","warehouse":"GUR-SAT","status":"offline","app_version":"1.3.8","last_seen":(timezone.now()-timedelta(hours=1)).isoformat()}],"sync":{"queued":3,"synced_today":126,"conflicts":1,"last_sync":timezone.now().isoformat()},"conflicts":[{"id":1,"reference":"CNT-260923-1A90","field":"counted_qty","local_value":3,"server_value":4,"status":"needs_review"}]})
    data=parse_body(request) or {}; action=str(data.get("action","sync")); item={"id":data.get("id"),"status":"resolved" if action=="resolve" else "synced","last_sync":timezone.now().isoformat()}; record_audit(request,"pwa sync action","device",item["id"] or "queue",action); return JsonResponse({"item":item})

@csrf_exempt
@roles_allowed("admin", "manager", "store")
def tenancy_view(request):
    if request.method == "GET":
        branches=[{"id":w.id,"code":w.code,"name":w.name,"users":0,"status":"active"} for w in Warehouse.objects.filter(active=True).order_by("code")]
        users=[{"id":request.api_user.id,"name":request.api_user.get_full_name() or request.api_user.username,"email":request.api_user.email,"role":request.api_user.profile.role,"branch":"All branches","approval_limit":500000 if request.api_user.profile.role=="admin" else 150000,"status":"active"}]
        return JsonResponse({"organization":{"id":1,"name":"Partora Auto Parts India","plan":"Growth","branches":len(branches),"users":len(users),"monthly_events":8420},"branches":branches,"users":users})
    data=parse_body(request) or {}; action=str(data.get("action","invite"))
    if action=="branch":
        try: branch=Warehouse.objects.create(code=str(data["code"]).strip().upper(),name=str(data["name"]).strip(),address=str(data.get("address",""))); item={"id":branch.id,"code":branch.code,"name":branch.name,"users":0,"status":"active"}
        except Exception as exc: return JsonResponse({"detail":f"Could not create branch: {exc}"},status=400)
    else: item={"id":uuid4().hex[:8],"name":str(data.get("name","Invited user")),"email":str(data.get("email","")),"role":str(data.get("role","store")),"branch":str(data.get("branch","All branches")),"approval_limit":float(data.get("approval_limit",0) or 0),"status":"invited"}
    record_audit(request,"tenant administration","organization",item["id"],action); return JsonResponse({"item":item},status=201)

@csrf_exempt
@roles_allowed("admin", "manager", "store")
def automation_view(request):
    if request.method == "GET":
        return JsonResponse({"rules":[{"id":1,"name":"Low-stock manager alert","trigger":"stock.below_reorder","action":"Send notification","status":"active","runs":18,"last_run":timezone.now().isoformat()},{"id":2,"name":"Block invoice mismatch","trigger":"invoice.exception","action":"Create approval","status":"active","runs":4,"last_run":timezone.now().isoformat()},{"id":3,"name":"Contract renewal reminder","trigger":"contract.expiring_30d","action":"Create review task","status":"paused","runs":2,"last_run":(timezone.now()-timedelta(days=3)).isoformat()}],"runs":[]})
    data=parse_body(request) or {}; item={"id":uuid4().hex[:8],"name":str(data.get("name","New automation rule")),"trigger":str(data.get("trigger","stock.below_reorder")),"action":str(data.get("rule_action","Send notification")),"status":"active","runs":0,"last_run":None}; record_audit(request,"automation rule","rule",item["id"],item["name"]); return JsonResponse({"item":item},status=201)

@csrf_exempt
@roles_allowed("admin", "manager", "sales", "store")
def fleet_view(request):
    if request.method == "GET":
        return JsonResponse({"vehicles":[{"id":1,"registration":"DL 01 AB 2488","customer":"Rapid Fleet Care","make":"Tata","model":"Ace Gold","year":2022,"mileage":68240,"next_service":"2026-10-04","status":"due_soon"},{"id":2,"registration":"HR 26 CX 9012","customer":"Northline Repairs","make":"Hyundai","model":"i20","year":2023,"mileage":42110,"next_service":"2026-11-18","status":"healthy"},{"id":3,"registration":"DL 04 MK 7761","customer":"Metro Garage","make":"Maruti Suzuki","model":"Swift","year":2020,"mileage":88700,"next_service":"2026-09-28","status":"overdue"}],"work_orders":[{"id":1,"order_no":"WO-260923-018","registration":"DL 01 AB 2488","customer":"Rapid Fleet Care","technician":"Ravi Kumar","status":"scheduled","due_date":"2026-10-04","parts_value":4850,"labor_value":1800,"notes":"Replace brake pads and oil filter"},{"id":2,"order_no":"WO-260921-014","registration":"DL 04 MK 7761","customer":"Metro Garage","technician":"Sana Iqbal","status":"in_progress","due_date":"2026-09-28","parts_value":7200,"labor_value":2200,"notes":"Full service and headlamp diagnosis"}],"reminders":[{"id":1,"type":"service_due","title":"Service due in 11 days","detail":"DL 01 AB 2488 · Rapid Fleet Care","status":"queued"},{"id":2,"type":"overdue","title":"Service overdue","detail":"DL 04 MK 7761 · Metro Garage","status":"urgent"}]})
    data=parse_body(request) or {}; action=str(data.get("action","work_order")); item={"id":uuid4().hex[:8],"order_no":f"WO-{timezone.now():%y%m%d}-{uuid4().hex[:3].upper()}","registration":data.get("registration"),"customer":data.get("customer"),"technician":data.get("technician"),"status":"scheduled","due_date":data.get("due_date"),"parts_value":float(data.get("parts_value",0) or 0),"labor_value":float(data.get("labor_value",0) or 0),"notes":data.get("notes","")}; record_audit(request,"fleet work order","fleet",item["id"],action); return JsonResponse({"item":item},status=201)

@csrf_exempt
@roles_allowed("admin", "manager", "store")
def security_view(request):
    users=[{"id":1,"name":"Aarav Admin","role":"admin","mfa":"enabled","last_login":timezone.now().isoformat(),"risk":"low"},{"id":2,"name":"Meera Manager","role":"manager","mfa":"pending","last_login":(timezone.now()-timedelta(minutes=20)).isoformat(),"risk":"medium"},{"id":3,"name":"Rohan Sales","role":"sales","mfa":"enabled","last_login":(timezone.now()-timedelta(hours=1)).isoformat(),"risk":"low"}]
    sessions=[{"id":1,"user":"Aarav Admin","device":"Chrome - Windows","location":"New Delhi","last_seen":timezone.now().isoformat(),"status":"active"},{"id":2,"user":"Kabir Store","device":"Android PWA","location":"Gurugram","last_seen":(timezone.now()-timedelta(minutes=6)).isoformat(),"status":"active"}]
    alerts=[{"id":1,"type":"mfa","title":"Manager MFA enrollment pending","detail":"Manager enrollment is required before high-value approvals.","status":"open"},{"id":2,"type":"session","title":"Idle session exceeds policy","detail":"Review the oldest active browser session.","status":"open"}]
    audit=[{"id":a.id,"actor":a.user.get_full_name() if a.user else "System","action":a.action,"target":a.entity_id,"created_at":a.created_at.isoformat(),"result":"success"} for a in AuditLog.objects.order_by("-created_at")[:20]]
    if request.method == "GET": return JsonResponse({"summary":{"mfa_coverage":75,"active_sessions":len(sessions),"open_alerts":len(alerts),"audit_events":AuditLog.objects.count()},"users":users,"sessions":sessions,"alerts":alerts,"audit":audit})
    data=parse_body(request) or {}; action=str(data.get("action","export")); item={"id":data.get("id"),"status":"completed"}
    if action == "mfa": item={"id":data.get("id"),"mfa":"enabled","risk":"low"}
    if action == "terminate": item={"id":data.get("id"),"status":"terminated"}
    if action == "resolve": item={"id":data.get("id"),"status":"resolved"}
    if action == "export": item={"format":"csv","filename":f"partora-security-{timezone.localdate().isoformat()}.csv","rows":AuditLog.objects.count()}
    record_audit(request,"security action","security",item.get("id") or "export",action); return JsonResponse({"item":item})

@csrf_exempt
@roles_allowed("admin", "manager", "store")
def documents_view(request):
    documents=[{"id":1,"file_name":"VE-INV-8821.pdf","supplier":"VoltEdge Electricals","invoice_no":"VE-INV-8821","gstin":"07AAACV1234A1Z5","total":22050,"po_no":"PO-260920-90BD","match_status":"exception","confidence":94,"status":"needs_review","uploaded_at":timezone.now().isoformat(),"issue":"Invoice quantity includes damaged units"},{"id":2,"file_name":"TL-INV-4407.pdf","supplier":"TorqueLine Components","invoice_no":"TL-INV-4407","gstin":"07AABCT6789C1Z2","total":14700,"po_no":"PO-260921-A12F","match_status":"matched","confidence":98,"status":"approved","uploaded_at":(timezone.now()-timedelta(hours=1)).isoformat(),"issue":""}]
    if request.method == "GET": return JsonResponse({"summary":{"processed_today":18,"pending_review":1,"matched":14,"exception_rate":11},"documents":documents})
    data=parse_body(request) or {}; action=str(data.get("action","upload")); item={"id":uuid4().hex[:8],"file_name":str(data.get("file_name","supplier-invoice.pdf")),"supplier":str(data.get("supplier","New supplier")),"invoice_no":str(data.get("invoice_no",f"INV-{timezone.now():%y%m%d}")),"gstin":str(data.get("gstin","Pending extraction")),"total":float(data.get("total",0) or 0),"po_no":str(data.get("po_no","Pending match")),"match_status":"pending","confidence":0,"status":"processing","uploaded_at":timezone.now().isoformat(),"issue":""}
    if action in {"approve","reject"}: item={"id":data.get("id"),"status":"approved" if action=="approve" else "rejected","match_status":"matched" if action=="approve" else "exception"}
    record_audit(request,"document processing","supplier_invoice",item["id"],action); return JsonResponse({"item":item},status=201 if action=="upload" else 200)

@csrf_exempt
@roles_allowed("admin", "manager", "sales", "store")
def delivery_view(request):
    routes=[{"id":1,"route_no":"RT-260923-04","driver":"Sanjay Mehta","vehicle":"DL 01 AB 2488","stops":6,"completed":3,"eta":"14:30","status":"in_transit","cost":1850},{"id":2,"route_no":"RT-260923-03","driver":"Pooja Shah","vehicle":"HR 26 CX 9012","stops":4,"completed":4,"eta":"12:10","status":"delivered","cost":1240}]
    shipments=[{"id":1,"shipment_no":"SHP-88421","customer":"Northline Repairs","order_no":"SO-260921-41BC","driver":"Sanjay Mehta","status":"in_transit","eta":"2026-09-23 14:30","pod_status":"pending","value":32600},{"id":2,"shipment_no":"SHP-88418","customer":"Metro Garage","order_no":"SO-260920-18DA","driver":"Pooja Shah","status":"delivered","eta":"2026-09-23 12:10","pod_status":"verified","value":18450}]
    if request.method == "GET": return JsonResponse({"summary":{"planned":8,"in_transit":3,"delivered_today":12,"exceptions":1},"routes":routes,"shipments":shipments,"exceptions":[{"id":1,"shipment_no":"SHP-88417","customer":"Rapid Fleet Care","reason":"Customer unavailable at dock","owner":"Dispatch desk","status":"open"}]})
    data=parse_body(request) or {}; action=str(data.get("action","route")); item={"id":uuid4().hex[:8],"route_no":f"RT-{timezone.now():%y%m%d}-{uuid4().hex[:2].upper()}","driver":data.get("driver"),"vehicle":data.get("vehicle"),"stops":int(data.get("stops",1) or 1),"completed":0,"eta":data.get("eta","15:30"),"status":"planned","cost":float(data.get("cost",0) or 0)}
    if action in {"status","proof"}: item={"id":data.get("id"),"status":"delivered" if action=="proof" else str(data.get("status","in_transit")),"pod_status":"verified" if action=="proof" else "pending"}
    record_audit(request,"delivery action","shipment",item["id"],action); return JsonResponse({"item":item},status=201 if action=="route" else 200)

@csrf_exempt
@roles_allowed("admin", "manager", "sales")
def partner_api_view(request):
    if request.method == "GET": return JsonResponse({"summary":{"active_keys":3,"calls_today":1284,"error_rate":1.8,"webhooks":6},"partners":[{"id":1,"name":"Northline Repairs","type":"dealer","status":"connected","last_call":timezone.now().isoformat(),"calls":642},{"id":2,"name":"Zoho Books","type":"accounting","status":"connected","last_call":timezone.now().isoformat(),"calls":418},{"id":3,"name":"FleetCare Telematics","type":"fleet","status":"sandbox","last_call":(timezone.now()-timedelta(hours=1)).isoformat(),"calls":224}],"keys":[{"id":1,"label":"Northline production","prefix":"pk_live_north_****","scopes":"orders:read, quotes:write","last_used":timezone.now().isoformat(),"status":"active"},{"id":2,"label":"FleetCare sandbox","prefix":"pk_test_fleet_****","scopes":"vehicles:read","last_used":(timezone.now()-timedelta(hours=1)).isoformat(),"status":"active"}],"webhooks":[{"id":1,"event":"order.fulfilled","target":"https://northline.example/hooks/partora","status":"active","deliveries":182},{"id":2,"event":"invoice.exception","target":"https://zoho.example/hooks/partora","status":"retrying","deliveries":14}]})
    data=parse_body(request) or {}; action=str(data.get("action","key")); item={"id":uuid4().hex[:8],"label":str(data.get("label","New API key")),"prefix":f"pk_{data.get('environment','test')}_{uuid4().hex[:6]}_****","scopes":str(data.get("scopes","orders:read")),"last_used":None,"status":"active"}
    if action == "rotate": item={"id":data.get("id"),"prefix":f"pk_live_rotated_{uuid4().hex[:4]}_****","status":"active"}
    if action == "webhook": item={"id":uuid4().hex[:8],"event":str(data.get("event","order.fulfilled")),"target":str(data.get("target","https://client.example/hooks/partora")),"status":"active","deliveries":0}
    record_audit(request,"partner API action","api",item["id"],action); return JsonResponse({"item":item},status=201 if action in {"key","webhook"} else 200)

@csrf_exempt
@roles_allowed("admin", "manager", "sales", "store")
def predictive_fleet_view(request):
    vehicles=[{"id":1,"registration":"DL 01 AB 2488","customer":"Rapid Fleet Care","model":"Tata Ace Gold","mileage":68240,"risk":"high","prediction":"Brake pad wear likely within 420 km","confidence":89,"next_service":"2026-10-04","estimated_cost":6800},{"id":2,"registration":"HR 26 CX 9012","customer":"Northline Repairs","model":"Hyundai i20","mileage":42110,"risk":"medium","prediction":"Battery replacement likely within 30 days","confidence":76,"next_service":"2026-11-18","estimated_cost":5200},{"id":3,"registration":"DL 04 MK 7761","customer":"Metro Garage","model":"Maruti Swift","mileage":88700,"risk":"low","prediction":"No immediate component risk","confidence":82,"next_service":"2026-09-28","estimated_cost":3100}]
    if request.method == "GET": return JsonResponse({"summary":{"vehicles":42,"high_risk":3,"due_30_days":8,"projected_savings":184000},"vehicles":vehicles,"history":[{"id":1,"registration":"DL 01 AB 2488","component":"Brake pads","event":"Predicted replacement","status":"planned","due":"420 km","owner":"Ravi Kumar"},{"id":2,"registration":"HR 26 CX 9012","component":"Battery","event":"Inspection reminder","status":"queued","due":"30 days","owner":"Sana Iqbal"}]})
    data=parse_body(request) or {}; action=str(data.get("action","acknowledge")); item={"id":data.get("id"),"risk":"reviewed" if action=="acknowledge" else "scheduled","prediction":"Preventive service scheduled" if action=="service" else "Risk reviewed"}; record_audit(request,"predictive fleet action","vehicle",item["id"],action); return JsonResponse({"item":item})

@csrf_exempt
@roles_allowed("admin", "manager", "store")
def warehouses_view(request):
    if request.method == "GET":
        warehouses=Warehouse.objects.filter(active=True).order_by("code")
        wh_items=[]
        for wh in warehouses:
            wh_items.append({"id":wh.id,"code":wh.code,"name":wh.name,"address":wh.address,"sku_count":wh.stocks.count(),"units":wh.stocks.aggregate(total=Sum("quantity"))["total"] or 0})
        transfers=[{"id":t.id,"reference":t.reference,"from_warehouse":t.from_warehouse.code,"to_warehouse":t.to_warehouse.code,"sku":t.product.sku,"product":t.product.name,"quantity":t.quantity,"status":t.status,"created_at":t.created_at.isoformat()} for t in StockTransfer.objects.select_related("from_warehouse","to_warehouse","product").order_by("-created_at")[:40]]
        return JsonResponse({"warehouses":wh_items,"transfers":transfers})
    if request.method == "POST":
        data=parse_body(request) or {}; action=str(data.get("action","transfer"))
        if action == "warehouse":
            try:
                wh=Warehouse.objects.create(code=str(data["code"]).strip().upper(),name=str(data["name"]).strip(),address=str(data.get("address","")).strip())
            except Exception as exc:
                return JsonResponse({"detail":f"Could not create warehouse: {exc}"},status=400)
            return JsonResponse({"item":{"id":wh.id,"code":wh.code,"name":wh.name,"address":wh.address,"sku_count":0,"units":0}},status=201)
        try:
            source=Warehouse.objects.get(code=str(data["from_warehouse"]).strip().upper()); target=Warehouse.objects.get(code=str(data["to_warehouse"]).strip().upper()); product=Product.objects.get(sku=str(data["sku"]).strip().upper()); qty=max(1,int(data.get("quantity",1)))
            if source.id == target.id: raise ValueError("Source and destination must differ")
            source_stock,_=WarehouseStock.objects.get_or_create(warehouse=source,product=product,defaults={"quantity":0}); target_stock,_=WarehouseStock.objects.get_or_create(warehouse=target,product=product,defaults={"quantity":0})
            if source_stock.quantity < qty: raise ValueError("Insufficient stock at source warehouse")
            source_stock.quantity-=qty; target_stock.quantity+=qty; source_stock.save(update_fields=["quantity"]); target_stock.save(update_fields=["quantity"])
            transfer=StockTransfer.objects.create(reference=f"TR-{timezone.now():%y%m%d}-{uuid4().hex[:4].upper()}",from_warehouse=source,to_warehouse=target,product=product,quantity=qty,created_by=request.api_user)
        except Exception as exc:
            return JsonResponse({"detail":f"Could not transfer stock: {exc}"},status=400)
        return JsonResponse({"item":{"id":transfer.id,"reference":transfer.reference,"from_warehouse":source.code,"to_warehouse":target.code,"sku":product.sku,"product":product.name,"quantity":qty,"status":"completed","created_at":transfer.created_at.isoformat()}},status=201)
    return JsonResponse({"detail":"Method not allowed"},status=405)

@csrf_exempt
@roles_allowed("admin", "manager", "store")
def reorder_view(request):
    if request.method == "GET":
        qs=Product.objects.select_related("supplier").filter(stock_qty__lte=F("reorder_level")).order_by("stock_qty")
        items=[{"id":p.id,"sku":p.sku,"name":p.name,"supplier":p.supplier.name if p.supplier else None,"stock_qty":p.stock_qty,"reorder_level":p.reorder_level,"suggested_qty":max(p.reorder_qty,p.reorder_level*2-p.stock_qty),"unit_price":float(p.price),"severity":"out" if p.stock_qty<=0 else "low"} for p in qs]
        return JsonResponse({"items":items,"count":len(items)})
    if request.method == "POST":
        data=parse_body(request) or {}
        try:
            product=Product.objects.select_related("supplier").get(sku=str(data["sku"]).strip().upper())
            if not product.supplier: raise ValueError("Product has no preferred supplier")
            qty=max(1,int(data.get("quantity") or product.reorder_qty)); unit_cost=float(data.get("unit_cost") or product.price)
            po=PurchaseOrder.objects.create(po_no=f"PO-{timezone.now():%y%m%d}-{uuid4().hex[:4].upper()}",supplier=product.supplier,status="approved",expected_date=timezone.localdate()+timedelta(days=product.supplier.lead_time_days),total=qty*unit_cost,created_by=request.api_user)
            PurchaseOrderItem.objects.create(purchase_order=po,product=product,quantity=qty,unit_cost=unit_cost)
        except Exception as exc:
            return JsonResponse({"detail":f"Could not create replenishment PO: {exc}"},status=400)
        return JsonResponse({"item":{"id":po.id,"po_no":po.po_no,"sku":product.sku,"supplier":product.supplier.name,"quantity":qty,"status":po.status}},status=201)
    return JsonResponse({"detail":"Method not allowed"},status=405)

@csrf_exempt
@roles_allowed("admin", "manager", "sales")
def sales_flow_view(request):
    if request.method == "GET":
        orders=[sales_order_dict(o) for o in SalesOrder.objects.select_related("quotation").prefetch_related("items__product", "invoice__payments").order_by("-created_at")[:100]]
        invoices=[invoice_dict(i) for i in Invoice.objects.select_related("sales_order").prefetch_related("payments").order_by("-created_at")[:100]]
        return JsonResponse({"orders":orders,"invoices":invoices})
    if request.method == "POST":
        data=parse_body(request) or {}; action=str(data.get("action","convert_quote"))
        try:
            if action == "convert_quote":
                quote=Quotation.objects.get(id=int(data["quote_id"]))
                order,created=SalesOrder.objects.get_or_create(quotation=quote,defaults={"order_no":f"SO-{timezone.now():%y%m%d}-{uuid4().hex[:4].upper()}","customer_name":quote.customer_name,"customer_company":quote.customer_company,"total":quote.total,"status":"confirmed","created_by":request.api_user})
                if created:
                    for line in data.get("items", []):
                        product=Product.objects.get(sku=str(line["sku"]).strip().upper())
                        quantity=max(1, int(line.get("quantity", 1)))
                        unit_price=float(line.get("unit_price") or product.price)
                        SalesOrderItem.objects.create(sales_order=order, product=product, quantity=quantity, unit_price=unit_price, line_total=quantity * unit_price)
                quote.status="approved"; quote.save(update_fields=["status"])
                item=sales_order_dict(order)
            elif action == "invoice":
                order=SalesOrder.objects.get(id=int(data["order_id"])); invoice,created=Invoice.objects.get_or_create(sales_order=order,defaults={"invoice_no":f"INV-{timezone.now():%y%m%d}-{uuid4().hex[:4].upper()}","total":order.total,"status":"issued","due_date":timezone.localdate()+timedelta(days=int(data.get("terms_days",30)))})
                item=invoice_dict(invoice)
            else:
                raise ValueError("Unknown action")
        except Exception as exc:
            return JsonResponse({"detail":f"Could not complete sales action: {exc}"},status=400)
        return JsonResponse({"item":item,"action":action},status=201 if created else 200)
    return JsonResponse({"detail":"Method not allowed"},status=405)

def invoice_dict(invoice):
    paid=float(invoice.payments.aggregate(total=Sum("amount"))["total"] or 0)
    return {"id":invoice.id,"invoice_no":invoice.invoice_no,"order_no":invoice.sales_order.order_no,"customer":invoice.sales_order.customer_company or invoice.sales_order.customer_name,"total":float(invoice.total),"paid":paid,"balance":max(0, float(invoice.total)-paid),"status":invoice.status,"due_date":invoice.due_date.isoformat()}

def sales_order_dict(order):
    items=[{"id":line.id,"sku":line.product.sku,"product":line.product.name,"quantity":line.quantity,"unit_price":float(line.unit_price),"line_total":float(line.line_total),"available":max(0, line.product.stock_qty-line.product.reserved_qty)} for line in order.items.all()]
    invoice=getattr(order, "invoice", None)
    return {"id":order.id,"order_no":order.order_no,"quote_no":order.quotation.quote_no if order.quotation else None,"customer_name":order.customer_name,"customer_company":order.customer_company,"total":float(order.total),"status":order.status,"fulfillment_status":order.fulfillment_status,"shipping_address":order.shipping_address,"invoice_no":invoice.invoice_no if invoice else None,"items":items,"created_at":order.created_at.isoformat()}

@csrf_exempt
@roles_allowed("admin", "manager", "sales", "store")
def fulfillment_view(request):
    if request.method == "GET":
        orders=SalesOrder.objects.select_related("quotation").prefetch_related("items__product", "invoice__payments").order_by("-created_at")[:100]
        return JsonResponse({"orders":[sales_order_dict(o) for o in orders],"invoices":[invoice_dict(i) for i in Invoice.objects.select_related("sales_order").prefetch_related("payments").order_by("-created_at")[:100]]})
    data=parse_body(request) or {}; action=str(data.get("action", "status"))
    try:
        order=SalesOrder.objects.select_related("invoice").prefetch_related("items__product").get(id=int(data["order_id"]))
        if action == "reserve":
            if not order.items.exists(): raise ValueError("Add order line items before reserving stock")
            for line in order.items.all():
                if line.product.stock_qty-line.product.reserved_qty < line.quantity: raise ValueError(f"Insufficient available stock for {line.product.sku}")
            for line in order.items.all():
                line.product.reserved_qty += line.quantity
                line.product.save(update_fields=["reserved_qty", "updated_at"])
            order.reserved_at=timezone.now(); order.fulfillment_status="picking"; order.save(update_fields=["reserved_at","fulfillment_status"])
            record_audit(request,"reserve stock","sales order",order.id,order.order_no)
        elif action == "status":
            status=str(data.get("status", "confirmed"))
            allowed={"confirmed","picking","packed","dispatched","delivered","cancelled"}
            if status not in allowed: raise ValueError("Invalid fulfillment status")
            if status == "dispatched":
                if not order.items.exists(): raise ValueError("Add order line items before dispatch")
                for line in order.items.all():
                    if line.product.stock_qty-line.product.reserved_qty < line.quantity: raise ValueError(f"Insufficient available stock for {line.product.sku}")
                for line in order.items.all():
                    line.product.stock_qty -= line.quantity
                    line.product.reserved_qty=max(0,line.product.reserved_qty-line.quantity)
                    line.product.save(update_fields=["stock_qty","reserved_qty","updated_at"])
                    StockMovement.objects.create(product=line.product,movement_type="out",quantity=line.quantity,reference=order.order_no)
                order.dispatched_at=timezone.now()
            if status == "delivered": order.delivered_at=timezone.now()
            order.fulfillment_status=status
            order.status="fulfilled" if status in {"dispatched","delivered"} else ("cancelled" if status=="cancelled" else order.status)
            order.save(update_fields=["fulfillment_status","status","dispatched_at","delivered_at"])
            record_audit(request,"fulfillment status","sales order",order.id,f"{order.order_no} → {status}")
        elif action == "payment":
            invoice=getattr(order,"invoice",None)
            if not invoice: raise ValueError("Issue the invoice before recording a payment")
            amount=float(data.get("amount",0) or 0)
            if amount <= 0: raise ValueError("Payment amount must be greater than zero")
            paid=float(invoice.payments.aggregate(total=Sum("amount"))["total"] or 0)
            if paid+amount > float(invoice.total): raise ValueError("Payment exceeds invoice balance")
            Payment.objects.create(invoice=invoice,amount=amount,method=str(data.get("method","bank")),reference=str(data.get("reference","")).strip(),created_by=request.api_user)
            total_paid=paid+amount; invoice.status="paid" if total_paid >= float(invoice.total) else "partial"; invoice.save(update_fields=["status"])
            record_audit(request,"record payment","invoice",invoice.id,f"{invoice.invoice_no} / {amount}")
        else:
            raise ValueError("Unknown fulfillment action")
    except Exception as exc:
        return JsonResponse({"detail":f"Could not update fulfillment: {exc}"},status=400)
    return JsonResponse({"item":sales_order_dict(order),"invoice":invoice_dict(getattr(order,"invoice",None)) if getattr(order,"invoice",None) else None})

@csrf_exempt
@roles_allowed("admin", "manager", "sales", "store")
def returns_view(request):
    if request.method == "GET":
        qs=ReturnRequest.objects.select_related("product","sales_order","created_by").order_by("-created_at")[:200]
        items=[{"id":r.id,"return_no":r.return_no,"order_no":r.sales_order.order_no if r.sales_order else None,"sku":r.product.sku,"product":r.product.name,"customer_name":r.customer_name,"quantity":r.quantity,"reason":r.reason,"warranty_expires":r.warranty_expires.isoformat() if r.warranty_expires else None,"status":r.status,"resolution":r.resolution,"inspection_notes":r.inspection_notes,"refund_amount":float(r.refund_amount),"stock_restocked":r.stock_restocked,"created_at":r.created_at.isoformat()} for r in qs]
        return JsonResponse({"items":items})
    data=parse_body(request) or {}; action=str(data.get("action","create"))
    try:
        if action == "create":
            product=Product.objects.get(sku=str(data["sku"]).strip().upper())
            order=SalesOrder.objects.filter(id=int(data["order_id"])).first() if data.get("order_id") else None
            item=ReturnRequest.objects.create(return_no=f"RMA-{timezone.now():%y%m%d}-{uuid4().hex[:4].upper()}",sales_order=order,product=product,customer_name=str(data.get("customer_name") or (order.customer_company if order else "Walk-in customer")).strip(),quantity=max(1,int(data.get("quantity",1))),reason=str(data["reason"]).strip(),warranty_expires=date.fromisoformat(str(data["warranty_expires"])) if data.get("warranty_expires") else None,refund_amount=float(data.get("refund_amount",0) or 0),created_by=request.api_user)
            record_audit(request,"create","return",item.id,item.return_no)
        elif action == "status":
            item=ReturnRequest.objects.select_related("product").get(id=int(data["id"]))
            status=str(data.get("status",item.status)); resolution=str(data.get("resolution",item.resolution or ""))
            if status not in dict(ReturnRequest.STATUS_CHOICES): raise ValueError("Invalid return status")
            item.status=status; item.resolution=resolution; item.inspection_notes=str(data.get("inspection_notes",item.inspection_notes)).strip()
            if status == "resolved" and resolution == "restock" and not item.stock_restocked:
                item.product.stock_qty += item.quantity; item.product.save(update_fields=["stock_qty","updated_at"])
                StockMovement.objects.create(product=item.product,movement_type="in",quantity=item.quantity,reference=item.return_no); item.stock_restocked=True
            item.save(update_fields=["status","resolution","inspection_notes","stock_restocked","updated_at"])
            record_audit(request,"return status","return",item.id,f"{item.return_no} → {status}")
        else: raise ValueError("Unknown return action")
    except Exception as exc:
        return JsonResponse({"detail":f"Could not update return: {exc}"},status=400)
    return JsonResponse({"item":{"id":item.id,"return_no":item.return_no,"order_no":item.sales_order.order_no if item.sales_order else None,"sku":item.product.sku,"product":item.product.name,"customer_name":item.customer_name,"quantity":item.quantity,"reason":item.reason,"warranty_expires":item.warranty_expires.isoformat() if item.warranty_expires else None,"status":item.status,"resolution":item.resolution,"inspection_notes":item.inspection_notes,"refund_amount":float(item.refund_amount),"stock_restocked":item.stock_restocked,"created_at":item.created_at.isoformat()}})

@csrf_exempt
@roles_allowed("admin", "manager", "store")
def inventory_control_view(request):
    if request.method == "GET":
        products=Product.objects.select_related("supplier").order_by("sku")[:250]
        availability=[{"id":p.id,"sku":p.sku,"product":p.name,"stock_qty":p.stock_qty,"reserved_qty":p.reserved_qty,"available_qty":max(0,p.stock_qty-p.reserved_qty),"status":"out" if p.stock_qty<=0 else "low" if p.stock_qty<=p.reorder_level else "healthy"} for p in products]
        counts=[]
        for count in InventoryCount.objects.select_related("warehouse","counted_by").prefetch_related("lines__product").order_by("-created_at")[:80]:
            counts.append({"id":count.id,"reference":count.reference,"warehouse":count.warehouse.code if count.warehouse else None,"status":count.status,"notes":count.notes,"counted_by":count.counted_by.get_full_name() or count.counted_by.username if count.counted_by else "System","created_at":count.created_at.isoformat(),"lines":[{"sku":line.product.sku,"product":line.product.name,"expected_qty":line.expected_qty,"counted_qty":line.counted_qty,"variance":line.variance} for line in count.lines.all()]})
        lots=[{"id":lot.id,"sku":lot.product.sku,"product":lot.product.name,"lot_no":lot.lot_no,"serial_no":lot.serial_no,"quantity":lot.quantity,"warehouse":lot.warehouse.code if lot.warehouse else None,"expiry_date":lot.expiry_date.isoformat() if lot.expiry_date else None} for lot in ProductLot.objects.select_related("product","warehouse").order_by("expiry_date","lot_no")[:150]]
        return JsonResponse({"availability":availability,"counts":counts,"lots":lots})
    data=parse_body(request) or {}; action=str(data.get("action","count"))
    try:
        if action == "count":
            product=Product.objects.get(sku=str(data["sku"]).strip().upper()); warehouse=Warehouse.objects.filter(code=str(data.get("warehouse","")).strip().upper()).first() if data.get("warehouse") else None
            expected=int(data.get("expected_qty",product.stock_qty)); counted=int(data["counted_qty"])
            count=InventoryCount.objects.create(reference=f"CNT-{timezone.now():%y%m%d}-{uuid4().hex[:4].upper()}",warehouse=warehouse,status="submitted",notes=str(data.get("notes","")).strip(),counted_by=request.api_user)
            InventoryCountLine.objects.create(inventory_count=count,product=product,expected_qty=expected,counted_qty=counted,variance=counted-expected)
            item={"id":count.id,"reference":count.reference,"warehouse":warehouse.code if warehouse else None,"status":count.status,"notes":count.notes,"counted_by":request.api_user.get_full_name() or request.api_user.username,"created_at":count.created_at.isoformat(),"lines":[{"sku":product.sku,"product":product.name,"expected_qty":expected,"counted_qty":counted,"variance":counted-expected}]}
            record_audit(request,"submit count","inventory count",count.id,count.reference)
        elif action == "approve":
            if request.api_user.profile.role not in {"admin","manager"}: raise ValueError("Only admin or manager can approve counts")
            count=InventoryCount.objects.prefetch_related("lines__product").get(id=int(data["id"]))
            if count.status == "approved": raise ValueError("Count is already approved")
            for line in count.lines.all():
                line.product.stock_qty=max(0,line.counted_qty); line.product.save(update_fields=["stock_qty","updated_at"])
                StockMovement.objects.create(product=line.product,movement_type="adjustment",quantity=line.counted_qty,reference=count.reference)
            count.status="approved"; count.approved_by=request.api_user; count.approved_at=timezone.now(); count.save(update_fields=["status","approved_by","approved_at"])
            item={"id":count.id,"reference":count.reference,"status":count.status}
            record_audit(request,"approve count","inventory count",count.id,count.reference)
        elif action == "lot":
            product=Product.objects.get(sku=str(data["sku"]).strip().upper()); warehouse=Warehouse.objects.filter(code=str(data.get("warehouse","")).strip().upper()).first() if data.get("warehouse") else None
            lot=ProductLot.objects.create(product=product,warehouse=warehouse,lot_no=str(data["lot_no"]).strip(),serial_no=str(data.get("serial_no","")).strip(),quantity=max(1,int(data.get("quantity",1))),expiry_date=date.fromisoformat(str(data["expiry_date"])) if data.get("expiry_date") else None)
            item={"id":lot.id,"sku":product.sku,"product":product.name,"lot_no":lot.lot_no,"serial_no":lot.serial_no,"quantity":lot.quantity,"warehouse":warehouse.code if warehouse else None,"expiry_date":lot.expiry_date.isoformat() if lot.expiry_date else None}
            record_audit(request,"create lot","product lot",lot.id,lot.lot_no)
        else: raise ValueError("Unknown inventory control action")
    except Exception as exc:
        return JsonResponse({"detail":f"Could not update inventory control: {exc}"},status=400)
    return JsonResponse({"item":item})

@csrf_exempt
@roles_allowed("admin", "manager", "store")
def supplier_performance_view(request):
    if request.method == "GET":
        suppliers=[]
        for supplier in Supplier.objects.filter(active=True).order_by("name"):
            orders=list(PurchaseOrder.objects.filter(supplier=supplier).prefetch_related("items"))
            received=[po for po in orders if po.received_at]
            on_time=[po for po in received if not po.expected_date or po.received_at.date() <= po.expected_date]
            ordered_units=sum(line.quantity for po in orders for line in po.items.all())
            received_units=sum(line.received_qty for po in orders for line in po.items.all())
            latest=SupplierPriceSnapshot.objects.filter(supplier=supplier).order_by("-captured_at").first()
            suppliers.append({"id":supplier.id,"name":supplier.name,"lead_time_days":supplier.lead_time_days,"rating":float(supplier.rating),"po_count":len(orders),"received_count":len(received),"on_time_rate":round(len(on_time)/len(received)*100,1) if received else None,"fill_rate":round(received_units/ordered_units*100,1) if ordered_units else None,"latest_cost":float(latest.unit_cost) if latest else None})
        plans=[]
        for product in Product.objects.select_related("supplier").filter(stock_qty__lte=F("reorder_level"),supplier__isnull=False).order_by("stock_qty")[:100]:
            plans.append({"sku":product.sku,"product":product.name,"supplier":product.supplier.name,"stock_qty":product.stock_qty,"reorder_level":product.reorder_level,"suggested_qty":max(product.reorder_qty,product.reorder_level*2-product.stock_qty),"lead_time_days":product.supplier.lead_time_days,"expected_stockout":(timezone.localdate()+timedelta(days=product.supplier.lead_time_days)).isoformat()})
        prices=[{"id":s.id,"supplier":s.supplier.name,"sku":s.product.sku,"product":s.product.name,"unit_cost":float(s.unit_cost),"captured_at":s.captured_at.isoformat()} for s in SupplierPriceSnapshot.objects.select_related("supplier","product").order_by("-captured_at")[:30]]
        contracts=[{"id":c.id,"supplier":c.supplier.name,"contract_no":c.contract_no,"expires_on":c.expires_on.isoformat(),"payment_terms":c.payment_terms,"annual_value":float(c.annual_value),"status":c.status} for c in SupplierContract.objects.select_related("supplier").order_by("expires_on")[:100]]
        return JsonResponse({"suppliers":suppliers,"plans":plans,"prices":prices,"contracts":contracts})
    data=parse_body(request) or {}
    try:
        supplier=Supplier.objects.get(name=str(data["supplier"]).strip()); product=Product.objects.get(sku=str(data["sku"]).strip().upper()); snapshot=SupplierPriceSnapshot.objects.create(supplier=supplier,product=product,unit_cost=float(data["unit_cost"]))
    except Exception as exc:
        return JsonResponse({"detail":f"Could not record supplier price: {exc}"},status=400)
    record_audit(request,"record supplier price","supplier",supplier.id,f"{product.sku} / {snapshot.unit_cost}")
    return JsonResponse({"item":{"id":snapshot.id,"supplier":supplier.name,"sku":product.sku,"product":product.name,"unit_cost":float(snapshot.unit_cost),"captured_at":snapshot.captured_at.isoformat()}},status=201)


def _forecast_for_product(product, demand_totals, window_days, horizon_days):
    today = timezone.localdate()
    supplier = product.supplier
    lead_time_days = supplier.lead_time_days if supplier else 0
    average_daily = (Decimal(demand_totals.get(product.id, 0)) / Decimal(window_days)).quantize(Decimal("0.01"))
    safety_stock = max(1, ceil(float(average_daily) * max(2, lead_time_days * 0.5))) if average_daily else 0
    reorder_point = ceil(float(average_daily) * lead_time_days + safety_stock)
    available_qty = max(0, product.stock_qty - product.reserved_qty)
    if average_daily:
        stockout_days = max(0, int(available_qty / float(average_daily)))
        projected_stockout = today + timedelta(days=stockout_days)
    else:
        stockout_days = None
        projected_stockout = None
    recommended_qty = 0
    if available_qty <= reorder_point:
        recommended_qty = max(
            product.reorder_qty,
            ceil(float(average_daily) * (lead_time_days + horizon_days) + safety_stock - available_qty),
        )
    if available_qty <= 0:
        risk = "out"
    elif stockout_days is not None and stockout_days <= lead_time_days:
        risk = "urgent"
    elif recommended_qty:
        risk = "watch"
    else:
        risk = "healthy"
    latest = SupplierPriceSnapshot.objects.filter(product=product).order_by("-captured_at").first()
    unit_cost = Decimal(latest.unit_cost if latest else (product.cost_price or product.price))
    return {
        "sku": product.sku,
        "product": product.name,
        "supplier": supplier.name if supplier else None,
        "supplier_id": supplier.id if supplier else None,
        "stock_qty": product.stock_qty,
        "reserved_qty": product.reserved_qty,
        "available_qty": available_qty,
        "average_daily_demand": float(average_daily),
        "lead_time_days": lead_time_days,
        "safety_stock": safety_stock,
        "reorder_point": reorder_point,
        "stockout_days": stockout_days,
        "projected_stockout": projected_stockout.isoformat() if projected_stockout else None,
        "recommended_qty": recommended_qty,
        "unit_cost": float(unit_cost),
        "estimated_cost": float(unit_cost * recommended_qty),
        "risk": risk,
    }


def _purchase_plan_item(plan):
    return {
        "id": plan.id,
        "plan_id": plan.id,
        "sku": plan.product.sku,
        "product": plan.product.name,
        "supplier": plan.supplier.name,
        "average_daily_demand": float(plan.average_daily_demand),
        "window_days": plan.window_days,
        "horizon_days": plan.horizon_days,
        "available_qty": plan.available_qty,
        "safety_stock": plan.safety_stock,
        "reorder_point": plan.reorder_point,
        "recommended_qty": plan.recommended_qty,
        "unit_cost": float(plan.unit_cost),
        "estimated_cost": float(plan.estimated_cost),
        "projected_stockout": plan.projected_stockout.isoformat() if plan.projected_stockout else None,
        "expected_date": plan.expected_date.isoformat() if plan.expected_date else None,
        "status": plan.status,
        "po_no": plan.purchase_order.po_no if plan.purchase_order else None,
        "created_at": plan.created_at.isoformat(),
    }


@csrf_exempt
@roles_allowed("admin", "manager", "store")
def demand_planning_view(request):
    if request.method == "GET":
        try:
            window_days = min(365, max(30, int(request.GET.get("window", 90))))
            horizon_days = min(180, max(7, int(request.GET.get("horizon", 30))))
        except (TypeError, ValueError):
            return JsonResponse({"detail": "Window and horizon must be whole numbers"}, status=400)
        start = timezone.localdate() - timedelta(days=window_days - 1)
        totals = {
            row["product_id"]: row["total"] or 0
            for row in DemandHistory.objects.filter(period_start__gte=start, period_start__lte=timezone.localdate()).values("product_id").annotate(total=Sum("quantity"))
        }
        active_plans = {}
        for plan in PurchasePlan.objects.filter(status__in=["pending", "approved", "ordered"]).select_related("product", "supplier", "purchase_order").order_by("-created_at"):
            active_plans.setdefault(plan.product_id, plan)
        items = []
        for product in Product.objects.select_related("supplier").filter(supplier__isnull=False).order_by("stock_qty", "name"):
            item = _forecast_for_product(product, totals, window_days, horizon_days)
            plan = active_plans.get(product.id)
            if plan:
                item.update({"plan_id": plan.id, "plan_status": plan.status, "po_no": plan.purchase_order.po_no if plan.purchase_order else None})
            else:
                item.update({"plan_id": None, "plan_status": None, "po_no": None})
            items.append(item)
        risk_order = {"out": 0, "urgent": 1, "watch": 2, "healthy": 3}
        items.sort(key=lambda item: (risk_order[item["risk"]], -item["recommended_qty"], item["product"]))
        supplier_totals = {}
        for item in items:
            if not item["recommended_qty"]:
                continue
            group = supplier_totals.setdefault(item["supplier"], {"supplier": item["supplier"], "recommended_qty": 0, "estimated_cost": 0, "sku_count": 0})
            group["recommended_qty"] += item["recommended_qty"]
            group["estimated_cost"] += item["estimated_cost"]
            group["sku_count"] += 1
        summary = {
            "at_risk": sum(1 for item in items if item["recommended_qty"]),
            "stockout_soon": sum(1 for item in items if item["stockout_days"] is not None and item["stockout_days"] <= item["lead_time_days"]),
            "estimated_cost": round(sum(item["estimated_cost"] for item in items), 2),
            "forecasted_skus": len(items),
        }
        return JsonResponse({"window_days": window_days, "horizon_days": horizon_days, "generated_at": timezone.now().isoformat(), "summary": summary, "items": items, "supplier_totals": list(supplier_totals.values())})
    data = parse_body(request) or {}
    action = str(data.get("action", "request"))
    if action == "request":
        try:
            product = Product.objects.select_related("supplier").get(sku=str(data["sku"]).strip().upper())
            if not product.supplier:
                raise ValueError("Product has no preferred supplier")
            window_days = min(365, max(30, int(data.get("window_days", 90))))
            horizon_days = min(180, max(7, int(data.get("horizon_days", 30))))
            start = timezone.localdate() - timedelta(days=window_days - 1)
            totals = {product.id: DemandHistory.objects.filter(product=product, period_start__gte=start, period_start__lte=timezone.localdate()).aggregate(total=Sum("quantity"))["total"] or 0}
            forecast = _forecast_for_product(product, totals, window_days, horizon_days)
            quantity = max(1, int(data.get("quantity") or forecast["recommended_qty"] or product.reorder_qty))
            existing = PurchasePlan.objects.filter(product=product, status__in=["pending", "approved", "ordered"]).select_related("product", "supplier", "purchase_order").first()
            if existing:
                return JsonResponse({"item": _purchase_plan_item(existing), "detail": "An active purchase plan already exists for this SKU"})
            expected_date = timezone.localdate() + timedelta(days=product.supplier.lead_time_days)
            projected_stockout = date.fromisoformat(forecast["projected_stockout"]) if forecast["projected_stockout"] else None
            plan = PurchasePlan.objects.create(product=product, supplier=product.supplier, average_daily_demand=forecast["average_daily_demand"], window_days=window_days, horizon_days=horizon_days, available_qty=forecast["available_qty"], safety_stock=forecast["safety_stock"], reorder_point=forecast["reorder_point"], recommended_qty=quantity, unit_cost=forecast["unit_cost"], estimated_cost=Decimal(str(forecast["unit_cost"])) * quantity, projected_stockout=projected_stockout, expected_date=expected_date, status="pending", requested_by=request.api_user)
        except Exception as exc:
            return JsonResponse({"detail": f"Could not request purchase plan: {exc}"}, status=400)
        record_audit(request, "request purchase plan", "purchase plan", plan.id, f"{product.sku} / {quantity} units")
        return JsonResponse({"item": _purchase_plan_item(plan)}, status=201)
    if action in {"approve", "reject"}:
        if request.api_user.profile.role not in {"admin", "manager"}:
            return JsonResponse({"detail": "Only admin or manager can review purchase plans"}, status=403)
        try:
            plan = PurchasePlan.objects.select_related("product", "supplier", "purchase_order").get(id=int(data["id"]))
            if plan.status != "pending":
                raise ValueError("Only pending plans can be reviewed")
            if action == "reject":
                plan.status = "rejected"
                plan.reviewed_by = request.api_user
                plan.reviewed_at = timezone.now()
                plan.save(update_fields=["status", "reviewed_by", "reviewed_at"])
                record_audit(request, "reject purchase plan", "purchase plan", plan.id, plan.product.sku)
                return JsonResponse({"item": _purchase_plan_item(plan)})
            po = PurchaseOrder.objects.create(po_no=f"PO-{timezone.now():%y%m%d}-{uuid4().hex[:4].upper()}", supplier=plan.supplier, status="approved", expected_date=plan.expected_date, total=plan.estimated_cost, created_by=request.api_user)
            PurchaseOrderItem.objects.create(purchase_order=po, product=plan.product, quantity=plan.recommended_qty, unit_cost=plan.unit_cost)
            plan.status = "ordered"
            plan.reviewed_by = request.api_user
            plan.reviewed_at = timezone.now()
            plan.purchase_order = po
            plan.save(update_fields=["status", "reviewed_by", "reviewed_at", "purchase_order"])
        except Exception as exc:
            return JsonResponse({"detail": f"Could not review purchase plan: {exc}"}, status=400)
        record_audit(request, "approve purchase plan", "purchase plan", plan.id, f"{plan.product.sku} / {po.po_no}")
        return JsonResponse({"item": _purchase_plan_item(plan), "po_no": po.po_no})
    return JsonResponse({"detail": "Unknown demand planning action"}, status=400)


def _rfq_detail(rfq):
    offers = list(rfq.offers.select_related("supplier").all())
    quoted = [offer for offer in offers if offer.status != "pending" and offer.unit_price > 0]
    min_total = min((Decimal(offer.unit_price) * rfq.quantity for offer in quoted), default=Decimal("0"))
    min_lead = min((offer.lead_time_days or offer.supplier.lead_time_days for offer in quoted), default=0)
    offer_items = []
    for offer in offers:
        lead_time = offer.lead_time_days or offer.supplier.lead_time_days
        total = Decimal(offer.unit_price) * rfq.quantity
        score = 0
        if offer in quoted:
            price_score = float(min_total / total * 60) if total else 0
            lead_score = (min_lead / lead_time * 20) if lead_time and min_lead else 0
            availability_score = min(offer.available_qty / max(rfq.quantity, 1), 1) * 10
            reliability_score = float(offer.supplier.rating / 5 * 10)
            score = round(price_score + lead_score + availability_score + reliability_score, 1)
        offer_items.append({
            "id": offer.id,
            "supplier": offer.supplier.name,
            "supplier_id": offer.supplier.id,
            "supplier_rating": float(offer.supplier.rating),
            "unit_price": float(offer.unit_price),
            "total": float(total),
            "lead_time_days": lead_time,
            "moq": offer.moq,
            "available_qty": offer.available_qty,
            "payment_terms": offer.payment_terms,
            "status": offer.status,
            "notes": offer.notes,
            "score": score,
            "is_recommended": False,
            "responded_at": offer.responded_at.isoformat() if offer.responded_at else None,
        })
    recommended = max((item for item in offer_items if item["score"]), key=lambda item: item["score"], default=None)
    if recommended:
        recommended["is_recommended"] = True
    return {
        "id": rfq.id,
        "rfq_no": rfq.rfq_no,
        "sku": rfq.product.sku,
        "product": rfq.product.name,
        "quantity": rfq.quantity,
        "needed_by": rfq.needed_by.isoformat() if rfq.needed_by else None,
        "status": rfq.status,
        "purchase_plan_id": rfq.purchase_plan_id,
        "notes": rfq.notes,
        "requested_by": rfq.requested_by.get_full_name() or rfq.requested_by.username if rfq.requested_by else "System",
        "created_at": rfq.created_at.isoformat(),
        "offers": offer_items,
        "recommended_offer_id": recommended["id"] if recommended else None,
        "recommended_supplier": recommended["supplier"] if recommended else None,
        "recommended_score": recommended["score"] if recommended else None,
    }


@csrf_exempt
@roles_allowed("admin", "manager", "store")
def rfq_view(request):
    if request.method == "GET":
        qs = RFQ.objects.select_related("product", "purchase_plan", "requested_by").prefetch_related("offers__supplier").all()[:50]
        return JsonResponse({"items": [_rfq_detail(rfq) for rfq in qs], "count": qs.count()})
    data = parse_body(request) or {}
    action = str(data.get("action", "create"))
    if action == "create":
        try:
            product = Product.objects.get(sku=str(data["sku"]).strip().upper())
            plan = PurchasePlan.objects.filter(id=int(data["plan_id"])).first() if data.get("plan_id") else None
            if plan and plan.product_id != product.id:
                raise ValueError("Purchase plan does not match the selected SKU")
            quantity = max(1, int(data.get("quantity") or (plan.recommended_qty if plan else 0)))
            raw_suppliers = data.get("suppliers") or data.get("supplier_ids") or []
            if isinstance(raw_suppliers, str):
                raw_suppliers = [value.strip() for value in raw_suppliers.split(",") if value.strip()]
            suppliers = []
            for value in raw_suppliers:
                supplier = Supplier.objects.filter(id=int(value)).first() if str(value).isdigit() else Supplier.objects.filter(name=value).first()
                if supplier and supplier not in suppliers:
                    suppliers.append(supplier)
            if not suppliers:
                suppliers = list(Supplier.objects.filter(active=True).order_by("name"))
            if len(suppliers) < 2:
                raise ValueError("Select at least two active suppliers for comparison")
            needed_by = date.fromisoformat(str(data["needed_by"])) if data.get("needed_by") else None
            rfq = RFQ.objects.create(rfq_no=f"RFQ-{timezone.now():%y%m%d}-{uuid4().hex[:4].upper()}", product=product, purchase_plan=plan, quantity=quantity, needed_by=needed_by, status="sent", notes=str(data.get("notes", "")).strip(), requested_by=request.api_user)
            RFQOffer.objects.bulk_create([RFQOffer(rfq=rfq, supplier=supplier, lead_time_days=supplier.lead_time_days) for supplier in suppliers])
        except Exception as exc:
            return JsonResponse({"detail": f"Could not send RFQ: {exc}"}, status=400)
        record_audit(request, "send supplier RFQ", "rfq", rfq.id, f"{rfq.rfq_no} / {product.sku} / {len(suppliers)} suppliers")
        return JsonResponse({"item": _rfq_detail(rfq)}, status=201)
    if action == "quote":
        try:
            offer = RFQOffer.objects.select_related("rfq", "supplier").get(id=int(data["offer_id"]))
            offer.unit_price = Decimal(str(data["unit_price"]))
            offer.lead_time_days = max(0, int(data.get("lead_time_days") or offer.supplier.lead_time_days))
            offer.moq = max(1, int(data.get("moq") or 1))
            offer.available_qty = max(0, int(data.get("available_qty") or 0))
            offer.payment_terms = str(data.get("payment_terms", "")).strip()
            offer.notes = str(data.get("notes", "")).strip()
            offer.status = "received"
            offer.responded_at = timezone.now()
            offer.save(update_fields=["unit_price", "lead_time_days", "moq", "available_qty", "payment_terms", "notes", "status", "responded_at"])
            offer.rfq.status = "quoted"
            offer.rfq.save(update_fields=["status"])
        except Exception as exc:
            return JsonResponse({"detail": f"Could not record supplier quote: {exc}"}, status=400)
        record_audit(request, "record supplier quote", "rfq offer", offer.id, f"{offer.rfq.rfq_no} / {offer.supplier.name}")
        return JsonResponse({"item": _rfq_detail(offer.rfq)})
    if action == "select":
        if request.api_user.profile.role not in {"admin", "manager"}:
            return JsonResponse({"detail": "Only admin or manager can select an offer and create a PO"}, status=403)
        try:
            offer = RFQOffer.objects.select_related("rfq__product", "rfq__purchase_plan", "supplier").get(id=int(data["offer_id"]))
            rfq = offer.rfq
            if offer.status != "received" or not offer.unit_price:
                raise ValueError("Only a received quote with a unit price can be selected")
            if offer.available_qty < rfq.quantity:
                raise ValueError("Selected supplier cannot cover the requested quantity")
            expected_date = rfq.needed_by or (timezone.localdate() + timedelta(days=offer.lead_time_days or offer.supplier.lead_time_days))
            total = offer.unit_price * rfq.quantity
            po = PurchaseOrder.objects.create(po_no=f"PO-{timezone.now():%y%m%d}-{uuid4().hex[:4].upper()}", supplier=offer.supplier, status="approved", expected_date=expected_date, total=total, created_by=request.api_user)
            PurchaseOrderItem.objects.create(purchase_order=po, product=rfq.product, quantity=rfq.quantity, unit_cost=offer.unit_price)
            rfq.status = "selected"
            rfq.save(update_fields=["status"])
            rfq.offers.exclude(id=offer.id).update(status="rejected")
            offer.status = "selected"
            offer.save(update_fields=["status"])
            if rfq.purchase_plan:
                plan = rfq.purchase_plan
                plan.supplier = offer.supplier
                plan.unit_cost = offer.unit_price
                plan.estimated_cost = total
                plan.expected_date = expected_date
                plan.status = "ordered"
                plan.reviewed_by = request.api_user
                plan.reviewed_at = timezone.now()
                plan.purchase_order = po
                plan.save(update_fields=["supplier", "unit_cost", "estimated_cost", "expected_date", "status", "reviewed_by", "reviewed_at", "purchase_order"])
        except Exception as exc:
            return JsonResponse({"detail": f"Could not select supplier offer: {exc}"}, status=400)
        record_audit(request, "select supplier offer", "rfq", rfq.id, f"{offer.supplier.name} / {po.po_no}")
        return JsonResponse({"item": _rfq_detail(rfq), "po_no": po.po_no})
    if action == "close":
        try:
            rfq = RFQ.objects.get(id=int(data["id"]))
            rfq.status = "closed"
            rfq.save(update_fields=["status"])
        except Exception as exc:
            return JsonResponse({"detail": f"Could not close RFQ: {exc}"}, status=400)
        return JsonResponse({"item": _rfq_detail(rfq)})
    return JsonResponse({"detail": "Unknown RFQ action"}, status=400)

@csrf_exempt
@roles_allowed("admin", "manager", "sales")
def customers_view(request):
    if request.method == "GET":
        q=request.GET.get("q","").strip(); qs=Customer.objects.filter(active=True).order_by("company","name")
        if q: qs=qs.filter(Q(name__icontains=q)|Q(company__icontains=q)|Q(email__icontains=q)|Q(phone__icontains=q)|Q(customer_type__icontains=q))
        items=[{"id":c.id,"name":c.name,"company":c.company,"email":c.email,"phone":c.phone,"customer_type":c.customer_type,"credit_limit":float(c.credit_limit),"payment_terms_days":c.payment_terms_days,"outstanding_balance":float(c.outstanding_balance),"notes":c.notes} for c in qs[:250]]
        return JsonResponse({"items":items,"count":qs.count()})
    if request.method == "POST":
        data=parse_body(request) or {}
        try:
            c=Customer.objects.create(name=str(data["name"]).strip(),company=str(data.get("company","")).strip(),email=str(data.get("email","")).strip(),phone=str(data.get("phone","")).strip(),customer_type=str(data.get("customer_type","retail")),credit_limit=float(data.get("credit_limit",0) or 0),payment_terms_days=int(data.get("payment_terms_days",0) or 0),outstanding_balance=float(data.get("outstanding_balance",0) or 0),notes=str(data.get("notes","")).strip())
        except Exception as exc:
            return JsonResponse({"detail":f"Could not add customer: {exc}"},status=400)
        return JsonResponse({"item":{"id":c.id,"name":c.name,"company":c.company,"email":c.email,"phone":c.phone,"customer_type":c.customer_type,"credit_limit":float(c.credit_limit),"payment_terms_days":c.payment_terms_days,"outstanding_balance":float(c.outstanding_balance),"notes":c.notes}},status=201)
    return JsonResponse({"detail":"Method not allowed"},status=405)

def portal_payload(customer, token):
    quotes=Quotation.objects.filter(Q(customer_company=customer.company)|Q(customer_name=customer.name)).order_by("-created_at")[:30]
    orders=SalesOrder.objects.filter(Q(customer_company=customer.company)|Q(customer_name=customer.name)).select_related("quotation").order_by("-created_at")[:30]
    invoices=Invoice.objects.filter(sales_order__in=orders).select_related("sales_order").prefetch_related("payments")
    return {"token":token,"customer":{"id":customer.id,"name":customer.name,"company":customer.company,"email":customer.email},"quotes":[{"id":q.id,"quote_no":q.quote_no,"total":float(q.total),"status":q.status,"valid_until":q.valid_until.isoformat()} for q in quotes],"orders":[{"id":o.id,"order_no":o.order_no,"total":float(o.total),"status":o.status,"fulfillment_status":o.fulfillment_status,"created_at":o.created_at.isoformat()} for o in orders],"invoices":[invoice_dict(i) for i in invoices]}

@csrf_exempt
def portal_view(request):
    token_value=request.GET.get("token","").strip() if request.method == "GET" else str((parse_body(request) or {}).get("token","")).strip()
    try:
        access=CustomerPortalToken.objects.select_related("customer").get(token=token_value,active=True,expires_at__gt=timezone.now())
    except CustomerPortalToken.DoesNotExist:
        return JsonResponse({"detail":"Portal link is invalid or expired"},status=401)
    if request.method == "GET": return JsonResponse(portal_payload(access.customer,access.token))
    data=parse_body(request) or {}; action=str(data.get("action",""))
    try:
        if action == "approve_quote":
            quote=Quotation.objects.get(id=int(data["quote_id"])); quote.status="approved"; quote.save(update_fields=["status"]); result={"quote_id":quote.id,"status":quote.status}
        elif action == "repeat_order":
            order=SalesOrder.objects.get(id=int(data["order_id"])); quote=Quotation.objects.create(quote_no=f"QT-{timezone.now():%y%m%d}-{uuid4().hex[:4].upper()}",customer_name=access.customer.name,customer_company=access.customer.company,total=order.total,status="draft",valid_until=timezone.localdate()+timedelta(days=7),created_by=None); result={"quote_no":quote.quote_no,"status":quote.status}
        elif action == "download_invoice":
            invoice=Invoice.objects.get(id=int(data["invoice_id"])); result=invoice_dict(invoice)
        else: raise ValueError("Unknown portal action")
    except Exception as exc:
        return JsonResponse({"detail":f"Could not complete portal action: {exc}"},status=400)
    return JsonResponse({"item":result,**portal_payload(access.customer,access.token)})

@csrf_exempt
@roles_allowed("admin", "manager", "sales")
def portal_issue_view(request):
    if request.method != "POST": return JsonResponse({"detail":"POST required"},status=405)
    data=parse_body(request) or {}
    try:
        customer=Customer.objects.get(id=int(data["customer_id"])); token=CustomerPortalToken.objects.create(token=f"pt_{uuid4().hex}",customer=customer,expires_at=timezone.now()+timedelta(days=int(data.get("days",30))),created_by=request.api_user)
    except Exception as exc:
        return JsonResponse({"detail":f"Could not issue portal link: {exc}"},status=400)
    record_audit(request,"issue portal link","customer",customer.id,customer.company or customer.name)
    return JsonResponse({"item":{"token":token.token,"customer":customer.company or customer.name,"expires_at":token.expires_at.isoformat(),"portal_path":f"/portal/{token.token}"},"portal":portal_payload(customer,token.token)},status=201)

@csrf_exempt
@roles_allowed("admin", "manager", "sales")
def pricing_view(request):
    if request.method == "GET":
        rules=[{"id":r.id,"name":r.name,"customer_type":r.customer_type,"min_qty":r.min_qty,"discount_percent":float(r.discount_percent),"active":r.active} for r in PriceRule.objects.filter(active=True).order_by("customer_type","min_qty")]
        return JsonResponse({"items":rules})
    if request.method == "POST":
        data=parse_body(request) or {}; action=str(data.get("action","rule"))
        if action == "preview":
            try:
                product=Product.objects.get(sku=str(data["sku"]).strip().upper()); customer_type=str(data.get("customer_type","retail")); qty=max(1,int(data.get("quantity",1)))
                if customer_type == "dealer" and product.dealer_price > 0: base=float(product.dealer_price)
                elif customer_type in {"fleet","workshop"} and product.wholesale_price > 0: base=float(product.wholesale_price)
                else: base=float(product.price)
                rule=PriceRule.objects.filter(active=True,customer_type=customer_type,min_qty__lte=qty).order_by("-min_qty","-discount_percent").first(); discount=float(rule.discount_percent) if rule else 0
                unit=round(base*(1-discount/100),2); margin=round(((unit-float(product.cost_price))/unit*100),1) if unit and product.cost_price else None
            except Exception as exc:
                return JsonResponse({"detail":f"Could not calculate price: {exc}"},status=400)
            return JsonResponse({"item":{"sku":product.sku,"name":product.name,"customer_type":customer_type,"quantity":qty,"base_price":base,"discount_percent":discount,"unit_price":unit,"line_total":round(unit*qty,2),"margin_percent":margin,"rule":rule.name if rule else None}})
        try:
            rule=PriceRule.objects.create(name=str(data["name"]).strip(),customer_type=str(data.get("customer_type","dealer")),min_qty=max(1,int(data.get("min_qty",1))),discount_percent=float(data.get("discount_percent",0)))
        except Exception as exc:
            return JsonResponse({"detail":f"Could not create price rule: {exc}"},status=400)
        return JsonResponse({"item":{"id":rule.id,"name":rule.name,"customer_type":rule.customer_type,"min_qty":rule.min_qty,"discount_percent":float(rule.discount_percent),"active":rule.active}},status=201)
    return JsonResponse({"detail":"Method not allowed"},status=405)

@roles_allowed("admin", "manager", "sales")
def analytics_view(request):
    products=list(Product.objects.all())
    inventory_value=sum(float(p.price)*p.stock_qty for p in products)
    inventory_cost=sum(float(p.cost_price or 0)*p.stock_qty for p in products)
    sales_total=float(SalesOrder.objects.exclude(status="cancelled").aggregate(total=Sum("total"))["total"] or 0)
    invoice_total=float(Invoice.objects.exclude(status="cancelled").aggregate(total=Sum("total"))["total"] or 0)
    outstanding=float(Customer.objects.filter(active=True).aggregate(total=Sum("outstanding_balance"))["total"] or 0)
    quotes_total=Quotation.objects.count(); approved=Quotation.objects.filter(status="approved").count()
    categories=[{"label":row["category"],"value":row["count"]} for row in Product.objects.values("category").annotate(count=Count("id")).order_by("-count")]
    suppliers=[{"label":row["supplier__name"] or "Unassigned","value":row["count"]} for row in Product.objects.values("supplier__name").annotate(count=Count("id")).order_by("-count")[:6]]
    top_customers=[{"label":c.company or c.name,"value":float(c.outstanding_balance)} for c in Customer.objects.filter(active=True).order_by("-outstanding_balance")[:6]]
    low_stock=sum(1 for p in products if p.stock_qty<=p.reorder_level)
    open_purchase_orders=PurchaseOrder.objects.filter(status__in=["approved","ordered","partial"]).count()
    open_rfqs=RFQ.objects.filter(status__in=["sent","quoted"]).count()
    invoice_exceptions=SupplierInvoice.objects.filter(status="exception").count()
    alerts=[]
    if low_stock: alerts.append({"id":"stock","severity":"urgent","title":f"{low_stock} SKU(s) need replenishment","detail":"Review the demand plan and raise the next purchase request."})
    if invoice_exceptions: alerts.append({"id":"invoice","severity":"review","title":f"{invoice_exceptions} supplier invoice exception(s)","detail":"Check received quantities and approve only after the discrepancy is resolved."})
    if open_rfqs: alerts.append({"id":"rfq","severity":"watch","title":f"{open_rfqs} sourcing request(s) are open","detail":"Compare supplier quotes and select the best offer."})
    return JsonResponse({"metrics":{"sales_total":sales_total,"invoice_total":invoice_total,"inventory_value":inventory_value,"inventory_cost":inventory_cost,"estimated_inventory_margin":max(0,inventory_value-inventory_cost),"outstanding":outstanding,"quote_conversion":round((approved/quotes_total*100),1) if quotes_total else 0,"low_stock":low_stock},"operations":{"open_purchase_orders":open_purchase_orders,"open_rfqs":open_rfqs,"receiving_exceptions":invoice_exceptions,"warehouse_units":WarehouseStock.objects.aggregate(total=Sum("quantity"))["total"] or 0,"at_risk_suppliers":0},"alerts":alerts,"categories":categories,"suppliers":suppliers,"top_customers":top_customers})

@csrf_exempt
@api_login_required
def governance_view(request):
    role=request.api_user.profile.role
    if request.method == "GET":
        notifications=Notification.objects.filter(Q(user=request.api_user)|Q(user__isnull=True,role=role)).order_by("-created_at")[:50]
        approvals=ApprovalRequest.objects.select_related("requested_by","reviewed_by").order_by("-created_at")[:100]
        audits=AuditLog.objects.select_related("user").order_by("-created_at")[:100]
        return JsonResponse({"notifications":[{"id":n.id,"title":n.title,"message":n.message,"read":n.read,"created_at":n.created_at.isoformat()} for n in notifications],"approvals":[{"id":a.id,"kind":a.kind,"reference":a.reference,"amount":float(a.amount),"status":a.status,"requested_by":(a.requested_by.get_full_name() or a.requested_by.username) if a.requested_by else "System","reviewed_by":(a.reviewed_by.get_full_name() or a.reviewed_by.username) if a.reviewed_by else None,"notes":a.notes,"created_at":a.created_at.isoformat()} for a in approvals],"audits":[{"id":a.id,"user":(a.user.get_full_name() or a.user.username) if a.user else "System","action":a.action,"entity":a.entity,"entity_id":a.entity_id,"detail":a.detail,"created_at":a.created_at.isoformat()} for a in audits]})
    if request.method == "POST":
        data=parse_body(request) or {}; action=str(data.get("action","request"))
        try:
            if action == "request":
                approval=ApprovalRequest.objects.create(kind=str(data.get("kind","purchase")),reference=str(data["reference"]).strip(),amount=float(data.get("amount",0) or 0),notes=str(data.get("notes","")).strip(),requested_by=request.api_user)
                Notification.objects.create(role="manager",title=f"Approval needed: {approval.kind}",message=f"{approval.reference} requested by {request.api_user.get_full_name() or request.api_user.username}")
                record_audit(request,"request approval","approval",approval.id,approval.reference)
                item={"id":approval.id,"kind":approval.kind,"reference":approval.reference,"amount":float(approval.amount),"status":approval.status,"requested_by":request.api_user.get_full_name() or request.api_user.username,"reviewed_by":None,"notes":approval.notes,"created_at":approval.created_at.isoformat()}
            elif action in {"approve","reject"}:
                if role not in {"admin","manager"}: return JsonResponse({"detail":"Only admin or manager can review approvals"},status=403)
                approval=ApprovalRequest.objects.get(id=int(data["id"])); approval.status="approved" if action=="approve" else "rejected"; approval.reviewed_by=request.api_user; approval.reviewed_at=timezone.now(); approval.notes=str(data.get("notes",approval.notes)); approval.save(update_fields=["status","reviewed_by","reviewed_at","notes"])
                if approval.requested_by: Notification.objects.create(user=approval.requested_by,title=f"Approval {approval.status}",message=f"{approval.reference} was {approval.status} by {request.api_user.get_full_name() or request.api_user.username}")
                record_audit(request,action,"approval",approval.id,approval.reference)
                item={"id":approval.id,"kind":approval.kind,"reference":approval.reference,"amount":float(approval.amount),"status":approval.status,"requested_by":(approval.requested_by.get_full_name() or approval.requested_by.username) if approval.requested_by else "System","reviewed_by":request.api_user.get_full_name() or request.api_user.username,"notes":approval.notes,"created_at":approval.created_at.isoformat()}
            elif action == "read":
                notification=Notification.objects.get(id=int(data["id"])); notification.read=True; notification.save(update_fields=["read"]); item={"id":notification.id,"read":True}
            else: raise ValueError("Unknown governance action")
        except Exception as exc:
            return JsonResponse({"detail":f"Could not complete governance action: {exc}"},status=400)
        return JsonResponse({"item":item})
    return JsonResponse({"detail":"Method not allowed"},status=405)
