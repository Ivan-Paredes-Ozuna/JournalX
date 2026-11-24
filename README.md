# Journal X

Sitio para leer, escribir y revisar textos. El inicio muestra lo publicado. Cada texto tiene categoría, estado, historial, comentarios y me gusta.

## Qué hace falta

- Python 3.12
- PostgreSQL 14 o más nuevo, instalado en la máquina o con Docker

## Instalar

Desde la carpeta del proyecto:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

En Windows el entorno se activa con `.venv\Scripts\activate`.

### Base de datos

Con Docker:

```bash
docker compose up -d
```

Eso levanta PostgreSQL en `localhost:5432`, con base `is2_proyecto`, usuario `postgres` y contraseña `postgres`. Esos son los valores de `.env.example`.

Sin Docker, crea la misma base en el PostgreSQL que ya tengas y ajusta `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST` y `DB_PORT` en `.env`.

### Datos iniciales

```bash
python3 manage.py migrate
python3 manage.py createsuperuser
python3 manage.py preparar
```

`preparar` crea los permisos, los roles (Administrador, Editor, Autor, Publicador y Suscriptor), seis categorías y dos publicaciones de ejemplo. Esas publicaciones son textos normales: se editan, se cambian de estado y se eliminan como el resto. El superusuario queda como administrador en todas las categorías.

Si `preparar` se corre antes de crear el usuario, avisa y no crea los textos. Se vuelve a ejecutar después de `createsuperuser`.

## Arrancar

```bash
python3 manage.py runserver
```

Abre http://127.0.0.1:8000/ e inicia sesión. El panel de Django está en http://127.0.0.1:8000/admin/.

En local, el correo de recuperación de contraseña se imprime en la terminal. No hace falta configurar un servidor de correo para probar.

La entrada con Google usa la aplicación del proyecto. Con usuario y contraseña no hace falta.

## Pruebas

```bash
pytest
```
