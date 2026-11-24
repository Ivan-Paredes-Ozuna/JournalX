from django.db import migrations
from django.utils import timezone


EJEMPLOS = [
    {
        "titulo": "Qué queda después de publicar",
        "categoria": "Ciencia de datos",
        "contenido_html": (
            "<p>Este texto viene con el proyecto para que el inicio no arranque vacío. "
            "Se edita, se cambia de estado y se elimina como cualquier otra publicación.</p>"
            "<p>Publicar no cierra el texto. A partir de ahí cuenta quién lo abre, "
            "quién lo deja a la mitad y qué frase se lleva. Un número solo, sin esa lectura, "
            "dice poco: cien visitas pueden ser cien personas o la misma persona cien veces.</p>"
            "<h2>Qué mirar primero</h2>"
            "<p>La fecha, la categoría y el estado alcanzan para situar un texto. "
            "Después importa el recorrido: borrador, revisión, publicado o inactivo. "
            "Cada paso queda en el historial, con quién lo movió.</p>"
            "<blockquote>Un reporte sirve cuando se puede volver al texto que lo produjo.</blockquote>"
            "<ul>"
            "<li>El estado dice en qué punto está.</li>"
            "<li>Las lecturas y los me gusta se cuentan sobre la publicación, no sobre el archivo.</li>"
            "<li>Si deja de servir como ejemplo, se elimina y no vuelve.</li>"
            "</ul>"
        ),
    },
    {
        "titulo": "Tres preguntas antes de cerrar un borrador",
        "categoria": "Robótica",
        "contenido_html": (
            "<p>Este texto también viene con el proyecto. Es una publicación más: "
            "tiene autor, categoría, estado y se gestiona desde las mismas pantallas.</p>"
            "<p>Antes de mandar un borrador a revisión conviene poder contestar tres cosas "
            "sin abrir el editor. Si una falla, el texto todavía no está listo.</p>"
            "<h2>Las tres</h2>"
            "<ul>"
            "<li>¿De qué trata, en una frase que otra persona pueda repetir?</li>"
            "<li>¿Qué tiene que hacer quien lo lee al terminar?</li>"
            "<li>¿Qué sobra y se puede borrar sin que se pierda esa frase?</li>"
            "</ul>"
            "<p>La revisión no arregla un texto que el autor no puede resumir. "
            "Sirve para discutir un resumen que ya existe.</p>"
            "<blockquote>Cerrar un borrador es poder dejarlo en manos de otra persona.</blockquote>"
        ),
    },
]


def _categoria(Categoria, nombre, usadas):
    encontrada = Categoria.objects.filter(estado="Activo", descripcion_corta=nombre).first()
    if encontrada is not None:
        return encontrada
    siguiente = (
        Categoria.objects.filter(estado="Activo").exclude(pk__in=usadas).order_by("id").first()
    )
    if siguiente is not None:
        return siguiente
    return Categoria.objects.filter(estado="Activo").order_by("id").first()


def cargar_ejemplos(apps, schema_editor):
    User = apps.get_model("auth", "User")
    Categoria = apps.get_model("login", "Categoria")
    Publicacion = apps.get_model("crearpublicaciones", "Publicacion")
    Historial = apps.get_model("crearpublicaciones", "Historial")

    autor = (
        User.objects.filter(is_superuser=True).order_by("id").first()
        or User.objects.order_by("id").first()
    )
    if autor is None:
        return

    ahora = timezone.now()
    usadas = []
    for ejemplo in EJEMPLOS:
        if Publicacion.objects.filter(titulo=ejemplo["titulo"]).exists():
            continue
        categoria = _categoria(Categoria, ejemplo["categoria"], usadas)
        if categoria is None:
            return
        usadas.append(categoria.pk)
        publicacion = Publicacion.objects.create(
            titulo=ejemplo["titulo"],
            contenido_html=ejemplo["contenido_html"],
            estado="publicado",
            user_id=autor.pk,
            fecha_publicacion=ahora,
            categoria_id=categoria.pk,
            vistas=0,
            me_gustas=0,
        )
        Historial.objects.create(
            publicacion_id=publicacion.pk,
            usuario_id=autor.pk,
            accion="creado",
            estado_nuevo="borrador",
        )
        Historial.objects.create(
            publicacion_id=publicacion.pk,
            usuario_id=autor.pk,
            accion="cambio_estado",
            estado_anterior="borrador",
            estado_nuevo="publicado",
        )


def quitar_ejemplos(apps, schema_editor):
    Publicacion = apps.get_model("crearpublicaciones", "Publicacion")
    Publicacion.objects.filter(titulo__in=[ejemplo["titulo"] for ejemplo in EJEMPLOS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("crearpublicaciones", "0015_alter_historial_accion_alter_publicacion_estado"),
        ("login", "0002_usuariorolcategoria_delete_usuario"),
    ]

    operations = [
        migrations.RunPython(cargar_ejemplos, quitar_ejemplos),
    ]
