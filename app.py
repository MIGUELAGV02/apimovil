import os

from dotenv import load_dotenv
from flask import Flask, jsonify
from flask_cors import CORS

from controllers.authController import auth_bp
from controllers.productController import product_bp
from controllers.userController import user_bp


load_dotenv()


def create_app():
	app = Flask(__name__)
	app.config["JSON_SORT_KEYS"] = False
	app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "change-this-secret-key")
	CORS(app)

	app.register_blueprint(auth_bp, url_prefix="/api/auth")
	app.register_blueprint(user_bp, url_prefix="/api/users")
	app.register_blueprint(product_bp, url_prefix="/api/products")

	@app.get("/api/health")
	def health_check():
		return jsonify({"status": "ok"}), 200

	@app.errorhandler(400)
	def bad_request(error):
		return jsonify({"error": "Solicitud inválida"}), 400

	@app.errorhandler(401)
	def unauthorized(error):
		return jsonify({"error": "No autorizado"}), 401

	@app.errorhandler(403)
	def forbidden(error):
		return jsonify({"error": "Acceso denegado"}), 403

	@app.errorhandler(404)
	def not_found(error):
		return jsonify({"error": "Recurso no encontrado"}), 404

	@app.errorhandler(500)
	def internal_error(error):
		return jsonify({"error": "Error interno del servidor"}), 500

	return app


app = create_app()


if __name__ == "__main__":
	port = int(os.getenv("PORT", 5000))
	app.run(host="0.0.0.0", port=port, debug=os.getenv("FLASK_DEBUG", "false").lower() == "true")
