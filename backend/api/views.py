import json
from datetime import date, timedelta
from uuid import uuid4
from django.contrib.auth import authenticate
from django.db.models import DecimalField, ExpressionWrapper, F, Q, Sum
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from .auth import api_login_required, issue_token, roles_allowed
from .models import Product, Quotation, StockMovement, Supplier, VehicleFitment, PurchaseOrder, PurchaseOrderItem, Warehouse, WarehouseStock, StockTransfer, SalesOrder, Invoice, Customer, PriceRule
from .serializers import product_dict, quotation_dict, supplier_dict

ROLE_MODULES = {
    "admin": ["dashboard", "inventory", "quotations", "suppliers", "stock", "barcodes", "fitments", "purchase_orders", "warehouses", "reorder", "sales_flow", "crm", "pricing"],
    "manager": ["dashboard", "inventory", "quotations", "suppliers", "stock", "barcodes", "fitments", "purchase_orders", "warehouses", "reorder", "sales_flow", "crm", "pricing"],
    "sales": ["dashboard", "inventory", "quotations", "barcodes", "fitments", "sales_flow", "crm", "pricing"],
    "store": ["dashboard", "inventory", "stock", "barcodes", "fitments", "purchase_orders", "warehouses", "reorder"],
}

def parse_body(request):
    try:
        return json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return None

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
                po.status="received"; po.save(update_fields=["status"])
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
        orders=[{"id":o.id,"order_no":o.order_no,"quote_no":o.quotation.quote_no if o.quotation else None,"customer_name":o.customer_name,"customer_company":o.customer_company,"total":float(o.total),"status":o.status,"invoice_no":getattr(getattr(o,"invoice",None),"invoice_no",None),"created_at":o.created_at.isoformat()} for o in SalesOrder.objects.select_related("quotation").order_by("-created_at")[:100]]
        invoices=[{"id":i.id,"invoice_no":i.invoice_no,"order_no":i.sales_order.order_no,"customer":i.sales_order.customer_company or i.sales_order.customer_name,"total":float(i.total),"status":i.status,"due_date":i.due_date.isoformat()} for i in Invoice.objects.select_related("sales_order").order_by("-created_at")[:100]]
        return JsonResponse({"orders":orders,"invoices":invoices})
    if request.method == "POST":
        data=parse_body(request) or {}; action=str(data.get("action","convert_quote"))
        try:
            if action == "convert_quote":
                quote=Quotation.objects.get(id=int(data["quote_id"]))
                order,created=SalesOrder.objects.get_or_create(quotation=quote,defaults={"order_no":f"SO-{timezone.now():%y%m%d}-{uuid4().hex[:4].upper()}","customer_name":quote.customer_name,"customer_company":quote.customer_company,"total":quote.total,"status":"confirmed","created_by":request.api_user})
                quote.status="approved"; quote.save(update_fields=["status"])
                item={"id":order.id,"order_no":order.order_no,"quote_no":quote.quote_no,"customer_name":order.customer_name,"customer_company":order.customer_company,"total":float(order.total),"status":order.status,"invoice_no":getattr(getattr(order,"invoice",None),"invoice_no",None),"created_at":order.created_at.isoformat()}
            elif action == "invoice":
                order=SalesOrder.objects.get(id=int(data["order_id"])); invoice,created=Invoice.objects.get_or_create(sales_order=order,defaults={"invoice_no":f"INV-{timezone.now():%y%m%d}-{uuid4().hex[:4].upper()}","total":order.total,"status":"issued","due_date":timezone.localdate()+timedelta(days=int(data.get("terms_days",30)))})
                item={"id":invoice.id,"invoice_no":invoice.invoice_no,"order_no":order.order_no,"customer":order.customer_company or order.customer_name,"total":float(invoice.total),"status":invoice.status,"due_date":invoice.due_date.isoformat()}
            else:
                raise ValueError("Unknown action")
        except Exception as exc:
            return JsonResponse({"detail":f"Could not complete sales action: {exc}"},status=400)
        return JsonResponse({"item":item,"action":action},status=201 if created else 200)
    return JsonResponse({"detail":"Method not allowed"},status=405)

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
