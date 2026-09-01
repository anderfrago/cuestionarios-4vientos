from functools import wraps
from flask import abort
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from .extensions import db
from .models import User


def current_user():
    identity = get_jwt_identity()
    return db.session.get(User, int(identity)) if identity else None


def roles_required(*roles):
    def decorator(fn):
        @wraps(fn)
        def wrapped(*args, **kwargs):
            verify_jwt_in_request()
            user = current_user()
            if not user or not user.is_active or user.role not in roles:
                abort(403, description="No tienes permiso para realizar esta acción")
            return fn(*args, **kwargs)
        return wrapped
    return decorator
