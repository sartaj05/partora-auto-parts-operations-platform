import json
from django.contrib.auth import authenticate
from django.db.models import Q, Sum
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .auth import api_login_required, issue_token, roles_allowed
from .models import Product, Quotation, StockMovement, Supplier
from .serializers import product_dict, quotation_dict, supplier_dict

ROLE_MODULES = {
    "admin": ["dashboard", "inventory", "quotations", "suppliers", "stock"],
    "manager": ["dashboard", "inventory", "quotations", "suppliers", "stock"],
    "sales": ["dashboard", "inventory", "quotations"],
    "store": ["dashboard", "inventory", "stock"],
}

def health(request):
    return JsonResponse({"status": "ok", "service": "partora-api"})

@csrf_exempt
def login_view(request):
    if request.method != "POST":
        return JsonResponse({"detail": "POST required"}, status=405)
    try:
        data = json.loads(request.body or "{}")
    except json.JSONDecodeError:
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
    total_inventory_value = Product.objects.aggregate(total=Sum("price"))["total"] or 0
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

@api_login_required
def inventory_view(request):
    qs = Product.objects.select_related("supplier").all().order_by("name")
    q = request.GET.get("q", "").strip()
    if q:
        qs = qs.filter(Q(sku__icontains=q) | Q(name__icontains=q) | Q(brand__icontains=q) | Q(category__icontains=q) | Q(supplier__name__icontains=q))
    return JsonResponse({"items": [product_dict(p) for p in qs[:250]], "count": qs.count()})

@roles_allowed("admin", "manager")
def suppliers_view(request):
    qs = Supplier.objects.order_by("name")
    return JsonResponse({"items": [supplier_dict(s) for s in qs], "count": qs.count()})

@roles_allowed("admin", "manager", "sales")
def quotations_view(request):
    qs = Quotation.objects.select_related("created_by").order_by("-created_at")
    return JsonResponse({"items": [quotation_dict(q) for q in qs], "count": qs.count()})

@roles_allowed("admin", "manager", "store")
def stock_view(request):
    movements = StockMovement.objects.select_related("product").order_by("-created_at")[:25]
    return JsonResponse({
        "items": [{
            "id": m.id,
            "sku": m.product.sku,
            "product": m.product.name,
            "type": m.movement_type,
            "quantity": m.quantity,
            "reference": m.reference,
            "created_at": m.created_at.isoformat(),
        } for m in movements]
    })
