from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from crearpublicaciones.models import Publicacion, Historial
from login.models import Categoria, UsuarioRolCategoria, Permiso
from django.http import JsonResponse
import json
from login.utils import *
from datetime import datetime
from django.utils import timezone

ESTADOS_PUBLICACION = {'borrador', 'revision', 'publicado', 'rechazado', 'inactivo'}

@login_required
def kanban_board(request, categoria_id=None):
    """
    View para mostrar el tablero Kanban con publicaciones organizadas por estado.

    Args:
        request (HttpRequest): El objeto de solicitud HTTP.
        categoria_id (int, opcional): El ID de la categoría seleccionada. Si no se proporciona, se selecciona la primera categoría activa.

    Returns:
        HttpResponse: Renderiza la plantilla 'index.html' con el contexto que incluye las publicaciones en diferentes estados y las categorías activas.
    """

    if not verificar_permisos_categoria_id(request, ['cambiar estado publicacion'], categoria_id):
        return render(request, 'sin_permiso.html')
    # Obtener el usuario actual
    usuario_actual = request.user

    # Obtener los roles del usuario
    roles_usuario = UsuarioRolCategoria.objects.filter(usuario_id=usuario_actual.id).values_list('rol_id', flat=True)

    # Obtener los permisos 11, 12 o 13
    permisos_requeridos = Permiso.objects.filter(id__in=[11, 12, 13])

    # Filtrar las categorías que están asociadas con los roles que tienen los permisos 11, 12 o 13
    categorias_usuario = Categoria.objects.filter(
        usuariorolcategoria__rol__in=roles_usuario, 
        usuariorolcategoria__rol__permisos__in=permisos_requeridos,
        estado='Activo'
    ).distinct()

    # Si no se especifica una categoría, seleccionamos la primera categoría activa
    if request.GET.get('categoria_id'):
        categoria_id = request.GET.get('categoria_id')

    if categoria_id:
        categoria = get_object_or_404(Categoria, id=categoria_id, estado='Activo')
    else:
        # Selecciona automáticamente la primera categoría activa si no se especifica ninguna
        categoria = categorias_usuario.first()

    # Asegúrate de que siempre haya una categoría válida
    if not categoria:
        categoria = categorias_usuario.first()

    # Filtrar publicaciones por estado y categoría seleccionadaaaa
    borrador = Publicacion.objects.filter(estado='borrador', categoria=categoria)
    revision = Publicacion.objects.filter(estado='revision', categoria=categoria)
    publicado = Publicacion.objects.filter(estado='publicado', categoria=categoria)
    rechazado = Publicacion.objects.filter(estado='rechazado', categoria=categoria)
    inactivo = Publicacion.objects.filter(estado='inactivo', categoria=categoria)

    context = {
        'categoria': categoria,  # La categoría seleccionada o la primera por defecto
        'borrador': borrador,
        'revision': revision,
        'publicado': publicado,
        'rechazado': rechazado,
        'inactivo': inactivo,
        'categorias_activas': categorias_usuario,  # Solo las categorías permitidas para el usuario
    }

    return render(request, 'index.html', context)

@login_required
@require_POST
def update_task_state(request, task_id):
    """
    Cambia el estado de una publicación y deja el motivo en la respuesta.
    """
    try:
        data = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'ok': False, 'message': 'No se pudo leer el cambio.'}, status=400)

    new_state = data.get('estado')
    if new_state not in ESTADOS_PUBLICACION:
        return JsonResponse({'ok': False, 'message': 'Ese estado no existe.'}, status=400)

    publicacion = get_object_or_404(Publicacion, id=task_id)
    if not verificar_permisos_categoria_id(request, ['cambiar estado publicacion'], publicacion.categoria_id):
        return JsonResponse({'ok': False, 'message': 'No puedes cambiar el estado de esta publicación.'}, status=403)

    estado_anterior = publicacion.estado
    publicacion.estado = new_state
    if new_state == 'publicado':
        publicacion.fecha_publicacion = timezone.now()
    publicacion.save()
    Historial.objects.create(
        publicacion=publicacion,
        usuario=request.user,
        accion='cambio_estado',
        estado_anterior=estado_anterior,
        estado_nuevo=new_state,
    )
    return JsonResponse({'ok': True, 'estado': new_state, 'message': 'Estado actualizado.'})
