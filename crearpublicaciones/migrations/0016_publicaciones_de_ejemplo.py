from django.db import migrations
from django.utils import timezone

from crearpublicaciones.ejemplos import EJEMPLOS


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
