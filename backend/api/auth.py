from functools import wraps
from django.conf import settings
from django.core import signing
from django.http import JsonResponse
from django.contrib.auth.models import User

TOKEN_SALT = "partora.auth"

def issue_token(user):
    return signing.dumps({"uid": user.id}, salt=TOKEN_SALT, compress=True)

def get_user_from_request(request):
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        return None
    token = header[7:].strip()
    try:
        payload = signing.loads(token, salt=TOKEN_SALT, max_age=settings.PARTORA_TOKEN_MAX_AGE)
        return User.objects.select_related("profile").get(id=payload["uid"], is_active=True)
    except Exception:
        return None

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
            if request.api_user.profile.role not in roles:
                return JsonResponse({"detail": "You do not have access to this module"}, status=403)
            return view(request, *args, **kwargs)
        return wrapped
    return decorator
