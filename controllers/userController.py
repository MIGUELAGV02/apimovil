from flask import Blueprint, jsonify, request
from mysql.connector import Error

from models.db import get_cursor
from models.security import hash_password, role_required, token_required


user_bp = Blueprint("user_bp", __name__)


def serialize_user(row):
	return {
		"id": row["id"],
		"nombre": row["nombre"],
		"apellido": row["apellido"],
		"email": row["email"],
		"rol": row["rol"],
	}


@user_bp.get("")
@token_required
@role_required("admin")
def list_users():
	try:
		with get_cursor() as (_, cursor):
			cursor.execute("SELECT id, nombre, apellido, email, rol FROM usuarios ORDER BY id DESC")
			users = cursor.fetchall()
		return jsonify({"users": [serialize_user(user) for user in users]}), 200
	except Error as error:
		return jsonify({"error": str(error)}), 500


@user_bp.get("/<int:user_id>")
@token_required
@role_required("admin")
def get_user(user_id):
	try:
		with get_cursor() as (_, cursor):
			cursor.execute("SELECT id, nombre, apellido, email, rol FROM usuarios WHERE id = %s", (user_id,))
			user = cursor.fetchone()
		if not user:
			return jsonify({"error": "Usuario no encontrado"}), 404
		return jsonify({"user": serialize_user(user)}), 200
	except Error as error:
		return jsonify({"error": str(error)}), 500


@user_bp.post("")
@token_required
@role_required("admin")
def create_user():
	data = request.get_json(silent=True) or {}
	nombre = (data.get("nombre") or "").strip()
	apellido = (data.get("apellido") or "").strip()
	email = (data.get("email") or "").strip().lower()
	contrasena = data.get("contrasena") or data.get("password") or ""
	rol = (data.get("rol") or "usuario").strip().lower()

	if not nombre or not apellido or not email or not contrasena:
		return jsonify({"error": "nombre, apellido, email y contrasena son obligatorios"}), 400

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
				(nombre, apellido, email, hash_password(contrasena), rol),
			)
			connection.commit()
			user_id = cursor.lastrowid

		return jsonify({"message": "Usuario creado correctamente", "user": {"id": user_id, "nombre": nombre, "apellido": apellido, "email": email, "rol": rol}}), 201
	except Error as error:
		return jsonify({"error": str(error)}), 500


@user_bp.put("/<int:user_id>")
@token_required
@role_required("admin")
def update_user(user_id):
	data = request.get_json(silent=True) or {}
	nombre = (data.get("nombre") or "").strip()
	apellido = (data.get("apellido") or "").strip()
	email = (data.get("email") or "").strip().lower()
	contrasena = data.get("contrasena") or data.get("password") or ""
	rol = (data.get("rol") or "").strip().lower()

	updates = []
	values = []

	if nombre:
		updates.append("nombre = %s")
		values.append(nombre)
	if apellido:
		updates.append("apellido = %s")
		values.append(apellido)
	if email:
		updates.append("email = %s")
		values.append(email)
	if contrasena:
		updates.append("contrasena = %s")
		values.append(hash_password(contrasena))
	if rol:
		updates.append("rol = %s")
		values.append(rol)

	if not updates:
		return jsonify({"error": "No hay datos para actualizar"}), 400

	try:
		with get_cursor() as (connection, cursor):
			if email:
				cursor.execute("SELECT id FROM usuarios WHERE email = %s AND id <> %s", (email, user_id))
				if cursor.fetchone():
					return jsonify({"error": "El email ya está registrado"}), 409

			cursor.execute("SELECT id FROM usuarios WHERE id = %s", (user_id,))
			if not cursor.fetchone():
				return jsonify({"error": "Usuario no encontrado"}), 404

			values.append(user_id)
			cursor.execute(f"UPDATE usuarios SET {', '.join(updates)} WHERE id = %s", tuple(values))
			connection.commit()

		return jsonify({"message": "Usuario actualizado correctamente"}), 200
	except Error as error:
		return jsonify({"error": str(error)}), 500


@user_bp.delete("/<int:user_id>")
@token_required
@role_required("admin")
def delete_user(user_id):
	try:
		with get_cursor() as (connection, cursor):
			cursor.execute("SELECT id FROM usuarios WHERE id = %s", (user_id,))
			if not cursor.fetchone():
				return jsonify({"error": "Usuario no encontrado"}), 404

			cursor.execute("DELETE FROM usuarios WHERE id = %s", (user_id,))
			connection.commit()

		return jsonify({"message": "Usuario eliminado correctamente"}), 200
	except Error as error:
		return jsonify({"error": str(error)}), 500
