import os
from datetime import datetime, timedelta, timezone
from functools import wraps

import jwt
from flask import current_app, jsonify, g, request
from werkzeug.security import check_password_hash, generate_password_hash


def hash_password(password):
    return generate_password_hash(password)


def verify_password(password, hashed_password):
    return check_password_hash(hashed_password, password)


def create_access_token(user_payload):
    secret_key = current_app.config.get("JWT_SECRET_KEY") or os.getenv("JWT_SECRET_KEY", "change-this-secret-key")
    algorithm = os.getenv("JWT_ALGORITHM", "HS256")
    expiration_minutes = int(os.getenv("JWT_EXPIRATION_MINUTES", "1440"))

    payload = {
        "sub": user_payload,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=expiration_minutes),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, secret_key, algorithm=algorithm)


def _extract_token():
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    return auth_header.split(" ", 1)[1].strip()


def token_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        token = _extract_token()
        if not token:
            return jsonify({"error": "Token requerido"}), 401

        secret_key = current_app.config.get("JWT_SECRET_KEY") or os.getenv("JWT_SECRET_KEY", "change-this-secret-key")
        algorithm = os.getenv("JWT_ALGORITHM", "HS256")

        try:
            decoded_token = jwt.decode(token, secret_key, algorithms=[algorithm])
            g.current_user = decoded_token["sub"]
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expirado"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Token inválido"}), 401

        return view_func(*args, **kwargs)

    return wrapper


def role_required(*allowed_roles):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(*args, **kwargs):
            current_user = getattr(g, "current_user", None)
            if not current_user:
                return jsonify({"error": "Token requerido"}), 401

            if current_user.get("rol") not in allowed_roles:
                return jsonify({"error": "No tienes permisos para realizar esta acción"}), 403

            return view_func(*args, **kwargs)

        return wrapper

    return decorator