from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from crearpublicaciones.ejemplos import EJEMPLOS
from crearpublicaciones.models import Historial, Publicacion
from login.models import Categoria, Permiso, Rol, UsuarioRolCategoria
from Perfil.models import Usuario


PERMISOS = [
    ("crear usuarios", "Permite crear nuevos usuarios en el sistema."),
    ("editar usuarios", "Permite modificar la informacion de usuarios existentes."),
    ("eliminar usuarios", "Permite eliminar usuarios del sistema."),
    ("asignar roles", "Permite asignar o cambiar los roles de los usuarios."),
    ("crear contenido", "Permite crear nuevas publicaciones."),
    ("gestionar contenido otros", "Permite modificar o eliminar contenido creado por otros."),
    ("aprobar contenido", "Permite aprobar contenido para su publicacion."),
    ("rechazar contenido", "Permite rechazar contenido."),
    ("publicar contenido", "Permite hacer visible el contenido aprobado."),
    ("cambiar estado publicacion", "Permite mover una publicacion de estado."),
    ("visualizar historial cambios", "Permite ver el historial de una publicacion."),
    ("gestionar categorias", "Permite crear, modificar y eliminar categorias."),
    ("gestionar plantillas", "Permite crear y modificar plantillas."),
    ("acceder reportes", "Permite ver los reportes."),
    ("ver contenido publicado", "Permite ver lo que ya esta publicado."),
    ("interactuar publicaciones", "Permite comentar y marcar me gusta."),
    ("editar perfil", "Permite modificar el propio perfil."),
    ("gestionar roles", "Permite crear, modificar y eliminar roles."),
]

ROLES = [
    (
        "Administrador",
        "Acceso a la gestion de usuarios, roles, categorias, contenido y reportes.",
        [nombre for nombre, _descripcion in PERMISOS],
    ),
    (
        "Editor",
        "Revisa y puede modificar contenido de otras personas.",
        [
            "crear contenido",
            "gestionar contenido otros",
            "aprobar contenido",
            "visualizar historial cambios",
            "gestionar plantillas",
            "ver contenido publicado",
            "interactuar publicaciones",
            "editar perfil",
        ],
    ),
    (
        "Autor",
        "Crea y edita su propio contenido.",
        [
            "crear contenido",
            "ver contenido publicado",
            "interactuar publicaciones",
            "editar perfil",
        ],
    ),
    (
        "Publicador",
        "Mueve el contenido de estado y lo deja visible.",
        [
            "gestionar contenido otros",
            "aprobar contenido",
            "rechazar contenido",
            "publicar contenido",
            "cambiar estado publicacion",
            "visualizar historial cambios",
            "gestionar plantillas",
            "ver contenido publicado",
            "interactuar publicaciones",
            "editar perfil",
        ],
    ),
    (
        "Suscriptor",
        "Lee lo publicado y puede comentar o marcar me gusta.",
        ["ver contenido publicado", "interactuar publicaciones", "editar perfil"],
    ),
]

CATEGORIAS = [
    ("Robótica", "Textos sobre robots, sensores y cómo se programan."),
    ("TIC", "Tecnologías de la información y la comunicación."),
    ("Energías Renovables", "Energía solar, eólica y otras fuentes que se renuevan."),
    ("Ciencia de datos", "Datos, métricas y cómo leerlas sin sacarlas de contexto."),
    ("Inteligencia Artificial", "Modelos, aprendizaje y sus límites."),
    ("Ciberseguridad", "Riesgos, accesos y cuidado de la información."),
]


class Command(BaseCommand):
    help = "Crea permisos, roles, categorías y las dos publicaciones de ejemplo."

    @transaction.atomic
    def handle(self, *args, **options):
        permisos = {}
        for nombre, descripcion in PERMISOS:
            permiso, _creado = Permiso.objects.get_or_create(
                nombre=nombre,
                defaults={"descripcion": descripcion},
            )
            permisos[nombre] = permiso

        for nombre, descripcion, nombres_permiso in ROLES:
            rol, creado = Rol.objects.get_or_create(
                nombre=nombre,
                defaults={"descripcion": descripcion},
            )
            if creado:
                rol.permisos.set(permisos[nombre_permiso] for nombre_permiso in nombres_permiso)

        for corta, larga in CATEGORIAS:
            Categoria.objects.get_or_create(
                descripcion_corta=corta,
                defaults={"descripcion_larga": larga, "estado": "Activo"},
            )

        admin = Rol.objects.get(nombre="Administrador")
        for user in User.objects.filter(is_superuser=True):
            perfil, _creado = Usuario.objects.get_or_create(user=user)
            for categoria in Categoria.objects.all():
                UsuarioRolCategoria.objects.get_or_create(
                    usuario=perfil,
                    rol=admin,
                    categoria=categoria,
                )

        autor = (
            User.objects.filter(is_superuser=True).order_by("id").first()
            or User.objects.order_by("id").first()
        )
        if autor is None:
            self.stdout.write(self.style.WARNING(
                "Permisos, roles y categorías listos. Falta un usuario: "
                "ejecuta createsuperuser y vuelve a correr preparar."
            ))
            return

        ahora = timezone.now()
        usadas = []
        for ejemplo in EJEMPLOS:
            if Publicacion.objects.filter(titulo=ejemplo["titulo"]).exists():
                continue
            categoria = self._categoria(ejemplo["categoria"], usadas)
            if categoria is None:
                self.stdout.write(self.style.WARNING("No hay categorías activas."))
                return
            usadas.append(categoria.pk)
            publicacion = Publicacion.objects.create(
                titulo=ejemplo["titulo"],
                contenido_html=ejemplo["contenido_html"],
                estado="publicado",
                user=autor,
                fecha_publicacion=ahora,
                categoria=categoria,
            )
            Historial.objects.create(
                publicacion=publicacion,
                usuario=autor,
                accion="creado",
                estado_nuevo="borrador",
            )
            Historial.objects.create(
                publicacion=publicacion,
                usuario=autor,
                accion="cambio_estado",
                estado_anterior="borrador",
                estado_nuevo="publicado",
            )

        self.stdout.write(self.style.SUCCESS("Journal X quedó listo para usarse."))

    def _categoria(self, nombre, usadas):
        encontrada = Categoria.objects.filter(estado="Activo", descripcion_corta=nombre).first()
        if encontrada is not None:
            return encontrada
        siguiente = Categoria.objects.filter(estado="Activo").exclude(pk__in=usadas).order_by("id").first()
        if siguiente is not None:
            return siguiente
        return Categoria.objects.filter(estado="Activo").order_by("id").first()
