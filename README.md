# EvaUno Backend

API mínima en Flask para gestionar usuarios y productos.

- Health: `GET /api/health`
- Auth: `POST /api/auth/register`, `POST /api/auth/login`, `GET /api/auth/me`
- Users CRUD: bajo `GET|POST /api/users`, `GET|PUT|DELETE /api/users/<id>` (admin)
- Products CRUD: bajo `GET|POST /api/products`, `GET|PUT|DELETE /api/products/<id>` (roles admin/editor)

Coloca un `index.html` en la raíz para comprobar que la API está funcionando.

Autenticación (Bearer JWT):

- El login devuelve `access_token` y `token_type: Bearer` en la respuesta JSON.
- Usa el header `Authorization: Bearer <access_token>` para acceder a rutas protegidas.

Ejemplo de login:

```bash
curl -X POST http://3.17.29.83/api/auth/login \
	-H "Content-Type: application/json" \
	-d '{"email":"admin@ejemplo.com","contrasena":"tuPass"}'
```

Ejemplo con token:

```bash
curl http://3.17.29.83/api/auth/me -H "Authorization: Bearer <ACCESS_TOKEN>"
```
