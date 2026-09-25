import hashlib
from datetime import timedelta
from functools import wraps
from uuid import uuid4
from django.conf import settings
from django.core import signing
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.utils import timezone

TOKEN_SALT = "partora.auth"

ROLE_MODULES = {
    "admin": ["dashboard", "inventory", "quotations", "suppliers", "stock", "barcodes", "fitments", "purchase_orders", "receiving", "mobile_warehouse", "warehouses", "reorder", "demand_planning", "rfq", "sales_flow", "fulfillment", "notifications", "copilot", "finance", "warranty_intelligence", "integrations", "pwa_admin", "tenancy", "permissions", "automation", "fleet", "security", "documents", "delivery", "partner_api", "predictive_fleet", "customer_service", "saas_billing", "observability", "inventory_network", "returns", "inventory_control", "supplier_performance", "portal", "crm", "pricing", "analytics", "governance"],
    "manager": ["dashboard", "inventory", "quotations", "suppliers", "stock", "barcodes", "fitments", "purchase_orders", "receiving", "mobile_warehouse", "warehouses", "reorder", "demand_planning", "rfq", "sales_flow", "fulfillment", "notifications", "copilot", "finance", "warranty_intelligence", "integrations", "tenancy", "automation", "fleet", "delivery", "customer_service", "inventory_network", "returns", "inventory_control", "supplier_performance", "portal", "crm", "pricing", "analytics", "governance"],
    "sales": ["dashboard", "inventory", "quotations", "barcodes", "fitments", "sales_flow", "fulfillment", "notifications", "copilot", "customer_service", "portal", "crm", "pricing", "analytics"],
    "store": ["dashboard", "inventory", "stock", "barcodes", "fitments", "purchase_orders", "receiving", "mobile_warehouse", "warehouses", "reorder", "fulfillment", "notifications", "returns", "inventory_control", "governance"],
}

PERMISSION_ACTIONS = ("view", "create", "edit", "approve", "export")


def permission_defaults(role, module, action):
    """Return the safe baseline used when a new permission has no override yet."""
    if module not in ROLE_MODULES.get(role, []):
        return False
    if role == "admin":
        return True
    if action == "view":
        return True
    if action == "export":
        return role == "manager"
    if action == "approve":
        return role == "manager"
    if action in {"create", "edit"}:
        return role in {"manager", "sales", "store"}
    return False


def get_permission_map(role):
    from .models import PermissionDefinition, RolePermission

    grants = {
        permission.permission.module + ":" + permission.permission.action: permission.allowed
        for permission in RolePermission.objects.filter(role=role).select_related("permission")
    }
    result = {}
    for permission in PermissionDefinition.objects.all():
        key = f"{permission.module}:{permission.action}"
        result[key] = grants.get(key, permission_defaults(role, permission.module, permission.action))
    return result


def has_permission(user, module, action, organization=None):
    role = get_effective_role(user, organization)
    from .models import PermissionDefinition, RolePermission

    permission = PermissionDefinition.objects.filter(module=module, action=action).first()
    if not permission:
        return permission_defaults(role, module, action)
    grant = RolePermission.objects.filter(role=role, permission=permission).values_list("allowed", flat=True).first()
    return permission_defaults(role, module, action) if grant is None else bool(grant)

def issue_token(user, request=None):
    token = signing.dumps({"uid": user.id, "nonce": uuid4().hex}, salt=TOKEN_SALT, compress=True)
    from .models import UserSession

    organization = get_current_organization(user)
    UserSession.objects.create(
        token_hash=hashlib.sha256(token.encode()).hexdigest(),
        user=user,
        organization=organization,
        device=(request.headers.get("User-Agent", "")[:160] if request else "API client"),
        ip_address=(request.META.get("REMOTE_ADDR") if request else None),
        user_agent=(request.headers.get("User-Agent", "")[:300] if request else ""),
        expires_at=timezone.now() + timedelta(seconds=settings.PARTORA_TOKEN_MAX_AGE),
    )
    return token

def get_user_from_request(request):
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        return None
    token = header[7:].strip()
    try:
        payload = signing.loads(token, salt=TOKEN_SALT, max_age=settings.PARTORA_TOKEN_MAX_AGE)
        from .models import UserSession
        session = UserSession.objects.filter(token_hash=hashlib.sha256(token.encode()).hexdigest(), revoked_at__isnull=True, expires_at__gt=timezone.now()).first()
        if not session or session.user_id != payload["uid"]:
            return None
        UserSession.objects.filter(id=session.id).update(last_seen=timezone.now())
        return User.objects.select_related("profile").get(id=payload["uid"], is_active=True)
    except Exception:
        return None


def get_current_organization(user):
    """Return the user's active organization, with a safe legacy fallback."""
    from .models import Organization, OrganizationMembership

    membership = user.organization_memberships.filter(active=True, organization__active=True).select_related("organization").order_by("organization_id").first()
    if membership:
        return membership.organization
    organization, _ = Organization.objects.get_or_create(slug="default", defaults={"name": "Partora Auto Parts India", "plan": "growth"})
    OrganizationMembership.objects.get_or_create(organization=organization, user=user, defaults={"role": user.profile.role, "approval_limit": 500000 if user.profile.role == "admin" else 150000})
    return organization


def get_current_branch(request, organization):
    from .models import Warehouse

    membership = request.api_user.organization_memberships.filter(organization=organization, active=True).first()
    if membership and not membership.all_branches and membership.primary_branch_id:
        restricted_branch = membership.primary_branch
    else:
        restricted_branch = None

    branch_code = request.headers.get("X-Partora-Branch", "").strip().upper()
    if not branch_code:
        return restricted_branch
    branch = Warehouse.objects.filter(organization=organization, code=branch_code, active=True).first()
    if restricted_branch and branch and branch.id != restricted_branch.id:
        return None
    return branch


def get_effective_role(user, organization=None):
    organization = organization or get_current_organization(user)
    membership = user.organization_memberships.filter(organization=organization, active=True).first()
    return membership.role if membership else user.profile.role

def api_login_required(view):
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        user = get_user_from_request(request)
        if not user:
            return JsonResponse({"detail": "Authentication required"}, status=401)
        request.api_user = user
        return view(request, *args, **kwargs)
    return wrapped

def roles_allowed(*roles):
    def decorator(view):
        @wraps(view)
        @api_login_required
        def wrapped(request, *args, **kwargs):
            request.organization = get_current_organization(request.api_user)
            request.effective_role = get_effective_role(request.api_user, request.organization)
            if request.effective_role not in roles:
                return JsonResponse({"detail": "You do not have access to this module"}, status=403)
            request.branch = get_current_branch(request, request.organization)
            if request.headers.get("X-Partora-Branch", "").strip() and request.branch is None:
                return JsonResponse({"detail": "You do not have access to this branch"}, status=403)
            return view(request, *args, **kwargs)
        return wrapped
    return decorator


def permission_required(module, action):
    def decorator(view):
        @wraps(view)
        @api_login_required
        def wrapped(request, *args, **kwargs):
            request.organization = get_current_organization(request.api_user)
            request.effective_role = get_effective_role(request.api_user, request.organization)
            if not has_permission(request.api_user, module, action, request.organization):
                return JsonResponse({"detail": f"Permission required: {module}.{action}"}, status=403)
            request.branch = get_current_branch(request, request.organization)
            if request.headers.get("X-Partora-Branch", "").strip() and request.branch is None:
                return JsonResponse({"detail": "You do not have access to this branch"}, status=403)
            return view(request, *args, **kwargs)
        return wrapped
    return decorator
