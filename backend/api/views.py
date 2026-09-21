import json
from django.contrib.auth import authenticate
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .auth import api_login_required, issue_token

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
