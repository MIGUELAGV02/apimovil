from flask import Blueprint, g, jsonify, request
from mysql.connector import Error

from models.db import get_cursor
from models.security import create_access_token, hash_password, token_required, verify_password


auth_bp = Blueprint("auth_bp", __name__)


@auth_bp.post("/register")
def register():
	data = request.get_json(silent=True) or {}
	nombre = (data.get("nombre") or "").strip()
	apellido = (data.get("apellido") or "").strip()
	email = (data.get("email") or "").strip().lower()
	contrasena = data.get("contrasena") or ""
	rol = (data.get("rol") or "usuario").strip().lower()

	if not nombre or not apellido or not email or not contrasena:
		return jsonify({"error": "nombre, apellido, email y contrasena son obligatorios"}), 400

	hashed_password = hash_password(contrasena)

	try:
		with get_cursor() as (connection, cursor):
			cursor.execute("SELECT id FROM usuarios WHERE email = %s", (email,))
			if cursor.fetchone():
				return jsonify({"error": "El email ya está registrado"}), 409

			cursor.execute(
				"""
				INSERT INTO usuarios (nombre, apellido, email, contrasena, rol)
				VALUES (%s, %s, %s, %s, %s)
				""",
				(nombre, apellido, email, hashed_password, rol),
			)
			connection.commit()
			user_id = cursor.lastrowid

		token = create_access_token({"id": user_id, "nombre": nombre, "apellido": apellido, "email": email, "rol": rol})
		return jsonify({
			"message": "Usuario creado correctamente",
			"access_token": token,
			"token_type": "Bearer",
			"user": {"id": user_id, "nombre": nombre, "apellido": apellido, "email": email, "rol": rol},
		}), 201
	except Error as error:
		return jsonify({"error": str(error)}), 500


@auth_bp.post("/login")
def login():
	data = request.get_json(silent=True) or {}
	email = (data.get("email") or "").strip().lower()
	contrasena = data.get("contrasena") or ""

	if not email or not contrasena:
		return jsonify({"error": "email y contrasena son obligatorios"}), 400

	try:
		with get_cursor() as (_, cursor):
			cursor.execute(
				"SELECT id, nombre, apellido, email, contrasena, rol FROM usuarios WHERE email = %s",
				(email,),
			)
			user = cursor.fetchone()

		if not user or not verify_password(contrasena, user["contrasena"]):
			return jsonify({"error": "Credenciales inválidas"}), 401

		payload = {
			"id": user["id"],
			"nombre": user["nombre"],
			"apellido": user["apellido"],
			"email": user["email"],
			"rol": user["rol"],
		}
		token = create_access_token(payload)

		return jsonify({"message": "Inicio de sesión correcto", "access_token": token, "token_type": "Bearer", "user": payload}), 200
	except Error as error:
		return jsonify({"error": str(error)}), 500


@auth_bp.get("/me")
@token_required
def me():
	return jsonify({"user": g.current_user}), 200
