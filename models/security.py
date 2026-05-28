import os

from datetime import datetime, timedelta, timezone
from functools import wraps

import bcrypt as bcrypt_lib
import jwt
from flask import current_app, jsonify, g, request


def hash_password(password: str) -> str:
    return bcrypt_lib.hashpw(password.encode("utf-8"), bcrypt_lib.gensalt()).decode("utf-8")


def verify_password(password: str, hashed_password: str) -> bool:
    try:
        if not hashed_password:
            return False

        if hashed_password.startswith("$2"):
            return bcrypt_lib.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))

        return password == hashed_password
    except Exception:
        return False


def create_access_token(user_payload):
    secret_key = current_app.config.get("JWT_SECRET_KEY") or os.getenv("JWT_SECRET_KEY", "change-this-secret-key")
    algorithm = os.getenv("JWT_ALGORITHM", "HS256")
    expiration_minutes = int(os.getenv("JWT_EXPIRATION_MINUTES", "1440"))

    payload = {
        "sub": user_payload,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=expiration_minutes),
        "iat": datetime.now(timezone.utc),
    }
    token = jwt.encode(payload, secret_key, algorithm=algorithm)
    if isinstance(token, bytes):
        return token.decode()
    return token


def _extract_token():
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header.split(" ", 1)[1].strip().strip('"')

    token_header = request.headers.get("X-Access-Token", "")
    if token_header:
        return token_header.strip().strip('"')

    return auth_header.strip().strip('"') or None


def token_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        token = _extract_token()
        if not token:
            return jsonify({"error": "Token requerido"}), 401

        secret_key = current_app.config.get("JWT_SECRET_KEY") or os.getenv("JWT_SECRET_KEY", "change-this-secret-key")
        algorithm = os.getenv("JWT_ALGORITHM", "HS256")

        try:
            decoded_token = jwt.decode(
                token,
                secret_key,
                algorithms=[algorithm],
                options={"verify_aud": False},
            )
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