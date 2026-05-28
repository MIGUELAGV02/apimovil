from flask import Blueprint, jsonify, request
from mysql.connector import Error

from models.db import get_cursor
from models.security import role_required, token_required


product_bp = Blueprint("product_bp", __name__)


def serialize_product(row):
	return {
		"id": row["id"],
		"producto": row["producto"],
		"cantidad": row["cantidad"],
		"precio": float(row["precio"]),
	}


@product_bp.get("")
@token_required
def list_products():
	try:
		with get_cursor() as (_, cursor):
			cursor.execute("SELECT id, producto, cantidad, precio FROM productos ORDER BY id DESC")
			products = cursor.fetchall()
		return jsonify({"products": [serialize_product(product) for product in products]}), 200
	except Error as error:
		return jsonify({"error": str(error)}), 500


@product_bp.get("/<int:product_id>")
@token_required
def get_product(product_id):
	try:
		with get_cursor() as (_, cursor):
			cursor.execute("SELECT id, producto, cantidad, precio FROM productos WHERE id = %s", (product_id,))
			product = cursor.fetchone()
		if not product:
			return jsonify({"error": "Producto no encontrado"}), 404
		return jsonify({"product": serialize_product(product)}), 200
	except Error as error:
		return jsonify({"error": str(error)}), 500


@product_bp.post("")
@token_required
@role_required("admin", "editor")
def create_product():
	data = request.get_json(silent=True) or {}
	producto = (data.get("producto") or "").strip()
	cantidad = data.get("cantidad")
	precio = data.get("precio")

	if not producto or cantidad is None or precio is None:
		return jsonify({"error": "producto, cantidad y precio son obligatorios"}), 400

	try:
		cantidad = int(cantidad)
		precio = float(precio)
	except (TypeError, ValueError):
		return jsonify({"error": "cantidad debe ser entero y precio numérico"}), 400

	try:
		with get_cursor() as (connection, cursor):
			cursor.execute(
				"INSERT INTO productos (producto, cantidad, precio) VALUES (%s, %s, %s)",
				(producto, cantidad, precio),
			)
			connection.commit()
			product_id = cursor.lastrowid

		return jsonify({"message": "Producto creado correctamente", "product": {"id": product_id, "producto": producto, "cantidad": cantidad, "precio": precio}}), 201
	except Error as error:
		return jsonify({"error": str(error)}), 500


@product_bp.put("/<int:product_id>")
@token_required
@role_required("admin", "editor")
def update_product(product_id):
	data = request.get_json(silent=True) or {}
	updates = []
	values = []

	producto = (data.get("producto") or "").strip()
	cantidad = data.get("cantidad")
	precio = data.get("precio")

	if producto:
		updates.append("producto = %s")
		values.append(producto)
	if cantidad is not None:
		try:
			cantidad = int(cantidad)
		except (TypeError, ValueError):
			return jsonify({"error": "cantidad debe ser entero"}), 400
		updates.append("cantidad = %s")
		values.append(cantidad)
	if precio is not None:
		try:
			precio = float(precio)
		except (TypeError, ValueError):
			return jsonify({"error": "precio debe ser numérico"}), 400
		updates.append("precio = %s")
		values.append(precio)

	if not updates:
		return jsonify({"error": "No hay datos para actualizar"}), 400

	try:
		with get_cursor() as (connection, cursor):
			cursor.execute("SELECT id FROM productos WHERE id = %s", (product_id,))
			if not cursor.fetchone():
				return jsonify({"error": "Producto no encontrado"}), 404

			values.append(product_id)
			cursor.execute(f"UPDATE productos SET {', '.join(updates)} WHERE id = %s", tuple(values))
			connection.commit()

		return jsonify({"message": "Producto actualizado correctamente"}), 200
	except Error as error:
		return jsonify({"error": str(error)}), 500


@product_bp.delete("/<int:product_id>")
@token_required
@role_required("admin", "editor")
def delete_product(product_id):
	try:
		with get_cursor() as (connection, cursor):
			cursor.execute("SELECT id FROM productos WHERE id = %s", (product_id,))
			if not cursor.fetchone():
				return jsonify({"error": "Producto no encontrado"}), 404

			cursor.execute("DELETE FROM productos WHERE id = %s", (product_id,))
			connection.commit()

		return jsonify({"message": "Producto eliminado correctamente"}), 200
	except Error as error:
		return jsonify({"error": str(error)}), 500
