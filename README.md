# EvaUno Backend

API mínima en Flask para gestionar usuarios y productos.

- Health: `GET /api/health`
- Auth: `POST /api/auth/register`, `POST /api/auth/login`, `GET /api/auth/me`
- Users CRUD: bajo `GET|POST /api/users`, `GET|PUT|DELETE /api/users/<id>` (admin)
- Products CRUD: bajo `GET|POST /api/products`, `GET|PUT|DELETE /api/products/<id>` (roles admin/editor)

Coloca un `index.html` en la raíz para comprobar que la API está funcionando.
