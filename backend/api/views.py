import json
from datetime import date, timedelta
from uuid import uuid4
from django.contrib.auth import authenticate
from django.db import transaction
from django.db.models import Count, DecimalField, ExpressionWrapper, F, Q, Sum
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from .auth import api_login_required, issue_token, roles_allowed
from .models import Product, Quotation, StockMovement, Supplier, VehicleFitment, PurchaseOrder, PurchaseOrderItem, Warehouse, WarehouseStock, StockTransfer, SalesOrder, SalesOrderItem, Invoice, Payment, ReturnRequest, InventoryCount, InventoryCountLine, ProductLot, SupplierPriceSnapshot, Customer, CustomerPortalToken, PriceRule, Notification, ApprovalRequest, AuditLog
from .serializers import product_dict, quotation_dict, supplier_dict

ROLE_MODULES = {
    "admin": ["dashboard", "inventory", "quotations", "suppliers", "stock", "barcodes", "fitments", "purchase_orders", "warehouses", "reorder", "sales_flow", "fulfillment", "returns", "inventory_control", "supplier_performance", "portal", "crm", "pricing", "analytics", "governance"],
    "manager": ["dashboard", "inventory", "quotations", "suppliers", "stock", "barcodes", "fitments", "purchase_orders", "warehouses", "reorder", "sales_flow", "fulfillment", "returns", "inventory_control", "supplier_performance", "portal", "crm", "pricing", "analytics", "governance"],
    "sales": ["dashboard", "inventory", "quotations", "barcodes", "fitments", "sales_flow", "fulfillment", "returns", "portal", "crm", "pricing", "analytics", "governance"],
    "store": ["dashboard", "inventory", "stock", "barcodes", "fitments", "purchase_orders", "warehouses", "reorder", "sales_flow", "fulfillment", "returns", "inventory_control", "supplier_performance", "governance"],
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
        return JsonResponse({"suppliers":suppliers,"plans":plans,"prices":prices})
    data=parse_body(request) or {}
    try:
        supplier=Supplier.objects.get(name=str(data["supplier"]).strip()); product=Product.objects.get(sku=str(data["sku"]).strip().upper()); snapshot=SupplierPriceSnapshot.objects.create(supplier=supplier,product=product,unit_cost=float(data["unit_cost"]))
    except Exception as exc:
        return JsonResponse({"detail":f"Could not record supplier price: {exc}"},status=400)
    record_audit(request,"record supplier price","supplier",supplier.id,f"{product.sku} / {snapshot.unit_cost}")
    return JsonResponse({"item":{"id":snapshot.id,"supplier":supplier.name,"sku":product.sku,"product":product.name,"unit_cost":float(snapshot.unit_cost),"captured_at":snapshot.captured_at.isoformat()}},status=201)

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
    return JsonResponse({"metrics":{"sales_total":sales_total,"invoice_total":invoice_total,"inventory_value":inventory_value,"inventory_cost":inventory_cost,"estimated_inventory_margin":max(0,inventory_value-inventory_cost),"outstanding":outstanding,"quote_conversion":round((approved/quotes_total*100),1) if quotes_total else 0,"low_stock":sum(1 for p in products if p.stock_qty<=p.reorder_level)},"categories":categories,"suppliers":suppliers,"top_customers":top_customers})

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
