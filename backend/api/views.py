import json
from datetime import date
from uuid import uuid4
from django.contrib.auth import authenticate
from django.db.models import DecimalField, ExpressionWrapper, F, Q, Sum
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from .auth import api_login_required, issue_token, roles_allowed
from .models import Product, Quotation, StockMovement, Supplier
from .serializers import product_dict, quotation_dict, supplier_dict

ROLE_MODULES = {
    "admin": ["dashboard", "inventory", "quotations", "suppliers", "stock", "barcodes"],
    "manager": ["dashboard", "inventory", "quotations", "suppliers", "stock", "barcodes"],
    "sales": ["dashboard", "inventory", "quotations", "barcodes"],
    "store": ["dashboard", "inventory", "stock", "barcodes"],
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
