"""
Vistas de la aplicación 'crearpublicaciones'.

Este archivo define las vistas para manejar la creación, modificación,
previsualización, y eliminación de publicaciones, así como la selección
de plantillas y la personalización de las publicaciones.
"""
from login.utils import *
from django.shortcuts import render
from .forms import *
from .models import *
from login.models import Categoria
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from utils.decorators import *
import time
import json
from bs4 import BeautifulSoup
from django.http import JsonResponse, Http404
from django.shortcuts import redirect
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from login.utils import *

from django.db.models import Q
from datetime import timedelta
from django.utils import timezone
import pytz
import traceback

@login_required
def crear_publicacion(request, categoria_id):
    """
    Vista para crear una nueva publicación.

    Si se envía una solicitud POST, se procesa el formulario de la publicación
    y se guarda la nueva publicación asociada al usuario autenticado.
    Luego, redirige a la página 'Mis Publicaciones'. Si es una solicitud GET,
    se muestra el formulario vacío para crear una nueva publicación.

    Args:
        request (HttpRequest): La solicitud HTTP recibida.
        categoria_id (int): ID de la categoría a la cual pertenece la publicación.

    Returns:
        HttpResponse: Renderiza la página de creación de publicaciones o
        redirige a 'mis_publicaciones' después de guardar.
    """

    if not verificar_permisos_categoria_id(request, ['crear contenido'], categoria_id):
        return render(request, 'sin_permiso.html')

    if request.method == 'POST':
        form = PublicacionForm(request.POST, request.FILES)
        if form.is_valid():
            publicacion = form.save(commit=False)
            publicacion.user = request.user  # Asigna el usuario autenticado
            publicacion.categoria = Categoria.objects.get(id=categoria_id)
            publicacion.fecha_publicacion = None
            publicacion.save()  # Guarda la publicación
            

            time.sleep(1)
            return redirect('mis_publicaciones')  # Redirige a la página "Mis Publicaciones"
    else:
        form = PublicacionForm()

    return render(request, 'crearpublicacion.html', {
        'form': form,
        'categoria_id': categoria_id
        })

@login_required
def previsualizar_publicacion(request, publicacion_id):
    """
    Vista para previsualizar una publicación existente.

    Muestra la publicación y sus comentarios asociados, y permite saber si el usuario ha dado "Me gusta".

    Args:
        request (HttpRequest): La solicitud HTTP recibida.
        publicacion_id (int): ID de la publicación a previsualizar.

    Returns:
        HttpResponse: Renderiza la plantilla de previsualización con la publicación y sus datos.
    """
    
    # Obtener la publicación por su ID
    try:
        publicacion = get_object_or_404(Publicacion, id=publicacion_id)

        if (request.user != publicacion.user and publicacion.estado != 'publicado') or publicacion.categoria.estado == 'Inactivo':
            print('aprobao')
            if not verificar_permisos_categoria_id(request, ['cambiar estado publicacion', 'visualizar historial cambios', 'gestionar contenido otros'], publicacion.categoria_id):
                return render(request, 'publicacion_no_disponible.html')

        comentarios = Comentario.objects.filter(publicacion=publicacion_id)
        #publicacion.vistas += 1
        #publicacion.save()
        likeado = Likes.objects.filter(user=request.user, publicacion=publicacion_id).exists()
        # Renderizar la plantilla de previsualización
        

        return render(request, 'previsualizacion.html', {
            'publicacion': publicacion,
            'comentarios': comentarios,
            'likeado': likeado
            })
    except Http404:
        # Renderiza un HTML específico si la publicación no existe
        return render(request, 'publicacion_no_existe.html')

@csrf_exempt
def incrementar_vistas(request, publicacion_id):
    """
    Vista para incrementar el contador de vistas de una publicación.

    Args:
        request (HttpRequest): La solicitud HTTP recibida.
        publicacion_id (int): ID de la publicación.

    Returns:
        JsonResponse: Respuesta en formato JSON con el resultado de la operación.
    """

    if request.method == 'POST':
        try:
            publicacion = get_object_or_404(Publicacion, id=publicacion_id)
            publicacion.vistas += 1
            publicacion.save()
            return JsonResponse({'status': 'success', 'vistas': publicacion.vistas})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)

def _es_fetch(request):
    return request.headers.get('X-Requested-With') == 'fetch'


def _respuesta_accion(request, payload, status=200, redirect_to=None):
    if _es_fetch(request) or status >= 400:
        return JsonResponse(payload, status=status)
    return redirect(redirect_to or 'home')


@login_required
@require_POST
def likear(request, publicacion_id):
    """
    Registra un me gusta. Solo acepta POST: abrir la URL no cambia nada.
    """

    publicacion = get_object_or_404(Publicacion, id=publicacion_id)
    if not verificar_permisos_categoria_id(request, ['interactuar publicaciones'], publicacion.categoria_id):
        return JsonResponse({'ok': False, 'message': 'No puedes interactuar con esta publicación.'}, status=403)

    likeado = Likes.objects.filter(user=request.user, publicacion=publicacion).exists()
    if not likeado:
        Likes.objects.create(user=request.user, publicacion=publicacion)
        publicacion.me_gustas += 1
        publicacion.save(update_fields=['me_gustas'])
    return JsonResponse({'ok': True, 'liked': True, 'me_gustas': publicacion.me_gustas})

@login_required
@require_POST
def dislikear(request, publicacion_id):
    """
    Quita un me gusta. Solo acepta POST: abrir la URL no cambia nada.
    """

    publicacion = get_object_or_404(Publicacion, id=publicacion_id)
    if not verificar_permisos_categoria_id(request, ['interactuar publicaciones'], publicacion.categoria_id):
        return JsonResponse({'ok': False, 'message': 'No puedes interactuar con esta publicación.'}, status=403)

    eliminados, _ = Likes.objects.filter(user=request.user, publicacion=publicacion).delete()
    if eliminados:
        publicacion.me_gustas = max(0, publicacion.me_gustas - 1)
        publicacion.save(update_fields=['me_gustas'])
    return JsonResponse({'ok': True, 'liked': False, 'me_gustas': publicacion.me_gustas})

@login_required
def mis_publicaciones(request):
    """
    Vista para mostrar las publicaciones del usuario autenticado.

    Recupera todas las publicaciones creadas por el usuario actual y las muestra
    en la página 'Mis Publicaciones'.

    Args:
        request (HttpRequest): La solicitud HTTP recibida.

    Returns:
        HttpResponse: Renderiza la página 'Mis Publicaciones' con todas las publicaciones del usuario.
    """

    publicaciones = Publicacion.objects.filter(user=request.user)
    return render(request, 'misPublicaciones.html', {'publicaciones': publicaciones})

@login_required
def gestionPublicacionOtros(request, categoria_id):
    """
    Vista para gestionar las publicaciones de otros usuarios dentro de una categoría.

    Permite al usuario autenticado visualizar todas las publicaciones en una categoría
    específica si tiene los permisos adecuados.

    Args:
        request (HttpRequest): La solicitud HTTP recibida.
        categoria_id (int): ID de la categoría.

    Returns:
        HttpResponse: Renderiza la página de gestión de publicaciones de terceros.
    """

    if not verificar_permisos_categoria_id(request, ['gestionar contenido otros'], categoria_id):
        return render(request, 'sin_permiso.html')
    
    publicaciones_gestionables = Publicacion.objects.filter(categoria=categoria_id)

    return render(request, 'GestionPublicaciones3ros.html', {
        'publicaciones': publicaciones_gestionables,
        'categoria_nombre': get_object_or_404(Categoria, id=categoria_id).descripcion_corta
        })

def parse_content(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    blocks = []

    for element in soup.contents:
        if element.name == 'p':
            blocks.append({'type': 'paragraph', 'content': element.text})
        elif element.name == 'h2':
            blocks.append({'type': 'heading', 'level': 'h2', 'content': element.text})
        elif element.name == 'h3':
            blocks.append({'type': 'heading', 'level': 'h3', 'content': element.text})
        elif element.name == 'blockquote':
            blocks.append({'type': 'quote', 'content': element.text})
        elif element.name == 'ul':
            items = [li.text for li in element.find_all('li')]
            blocks.append({'type': 'list', 'items': items})
        elif element.name == 'img':
            blocks.append({'type': 'image', 'src': element['src']})
        # Agrega más casos si es necesario

    return blocks

@login_required
def modificar_publicacion(request, publicacion_id):
    """
    Vista para modificar una publicación existente.

    Permite al usuario editar el título y el contenido de una publicación.
    Si la solicitud es GET, se muestra el formulario con los datos actuales.
    Si la solicitud es POST, se actualizan los datos de la publicación.

    Args:
        request (HttpRequest): La solicitud HTTP recibida.
        publicacion_id (int): ID de la publicación a modificar.

    Returns:
        HttpResponse: Renderiza la página de modificación o devuelve una respuesta JSON.
    """

    # Obtener la publicación por su ID
    publicacion = get_object_or_404(Publicacion, id=publicacion_id)

    # Verificar permisos
    if not verificar_permisos_categoria_id(request, ['crear contenido'], publicacion.categoria_id):
        return render(request, 'sin_permiso.html')

    # Si la publicación está publicada, no se puede editar
    if publicacion.estado == 'publicado':
        return render(request, 'no_editable.html', {'categoria_publicacion': publicacion.categoria_id})

    # Método GET: mostrar el formulario de modificación
    if request.method == 'GET':
        blocks = parse_content(publicacion.contenido_html)
        context = {
            'publicacion': publicacion,
            'blocks': blocks,
        }
        return render(request, 'modificarpublicacion.html', context)

    # Método POST: guardar cambios
    elif request.method == 'POST':
        # Verificar si la solicitud viene en formato JSON
        if request.content_type == 'application/json':
            data = json.loads(request.body)
            publicacion.titulo = data.get('title', publicacion.titulo)
            publicacion.contenido_html = data.get('content', publicacion.contenido_html)
        else:
            # Si no es JSON, tomamos los datos del formulario
            publicacion.titulo = request.POST.get('title', publicacion.titulo)
            publicacion.contenido_html = request.POST.get('content', publicacion.contenido_html)

        # Guardar los cambios en la base de datos
        publicacion.save()

        # Respuesta de éxito
        return JsonResponse({'status': 'success'})

    # Si no es un método permitido
    return JsonResponse({'status': 'error', 'message': 'Método no permitido.'}, status=405)

@csrf_exempt
def modificar_publicacion_ajax(request, id):
    """
    Vista para modificar una publicación existente mediante una solicitud AJAX.

    Permite actualizar los datos de una publicación como el título, contenido
    y categoría. La solicitud debe incluir un JSON con los campos que se
    desean modificar.

    Args:
        request (HttpRequest): La solicitud HTTP recibida.
        id (int): ID de la publicación a modificar.

    Returns:
        JsonResponse: Respuesta en formato JSON indicando el estado de la operación. Incluye un mensaje de éxito o error.
    """
    if request.method == 'POST':
        publicacion = get_object_or_404(Publicacion, id=id)

        try:
            data = json.loads(request.body)
            publicacion.titulo = data.get('title', publicacion.titulo)
            publicacion.contenido_html = data.get('content', publicacion.contenido_html)

            # Guardar los cambios en la publicación
            publicacion.save()

            return JsonResponse({'message': '¡Publicación actualizada con éxito!'})
        except Exception as e:
            return JsonResponse({'message': str(e)}, status=400)

    return JsonResponse({'message': 'Método no permitido.'}, status=405)

def _puede_eliminar(request, publicacion):
    if publicacion.user_id == request.user.id:
        return True
    return verificar_permisos_categoria_id(
        request,
        ['crear contenido', 'gestionar contenido otros'],
        publicacion.categoria_id,
    )


@login_required
@require_POST
def eliminar_publicacion(request, publicacion_id):
    """
    Elimina una publicación propia o una que el rol permite gestionar.
    Solo acepta POST: visitar la URL no borra nada.
    """
    publicacion = get_object_or_404(Publicacion, id=publicacion_id)
    if not _puede_eliminar(request, publicacion):
        return _respuesta_accion(request, {'ok': False, 'message': 'No puedes eliminar esta publicación.'}, status=403)

    publicacion.delete()
    return _respuesta_accion(request, {'ok': True}, redirect_to='mis_publicaciones')

@login_required
@require_POST
def eliminar_publicacion_otros(request, publicacion_id):
    """
    Elimina la publicación de otra persona si el rol lo permite.
    Solo acepta POST: visitar la URL no borra nada.
    """

    publicacion = get_object_or_404(Publicacion, id=publicacion_id)
    if not verificar_permisos_categoria_id(request, ['gestionar contenido otros'], publicacion.categoria_id):
        return _respuesta_accion(request, {'ok': False, 'message': 'No puedes eliminar esta publicación.'}, status=403)

    publicacion.delete()
    return _respuesta_accion(request, {'ok': True}, redirect_to='home')

@login_required
def seleccionar_plantilla(request, categoria_id):
    """
    Vista para seleccionar una plantilla para la publicación.

    Muestra las opciones de plantillas disponibles para ser usadas
    en la creación de publicaciones.

    Args:
        request (HttpRequest): La solicitud HTTP recibida.
        categoria_id (int): ID de la categoría de la publicación.

    Returns:
        HttpResponse: Renderiza la página de selección de plantillas.
    """

    if not verificar_permisos_categoria_id(request, ['crear contenido'], categoria_id):
        return render(request, 'sin_permiso.html')

    return render(request, 'seleccionar_plantilla.html', {
        'categoria_id': categoria_id
    })


@login_required
def personalizable(request, categoria_id):
    """
    Vista para crear una nueva publicación en modo borrador o reutilizar una existente.

    Permite al usuario personalizar una publicación existente o crear una nueva en modo borrador.

    Args:
        request (HttpRequest): La solicitud HTTP recibida.
        categoria_id (int): ID de la categoría a la que pertenece la publicación.

    Returns:
        HttpResponse: Renderiza la página de personalización de publicaciones.
    """

    # Obtener la categoría
    categoria = get_object_or_404(Categoria, id=categoria_id)

    if not verificar_permisos_categoria_id(request, ['crear contenido'], categoria_id):
        return render(request, 'sin_permiso.html')

    # Crear una nueva publicación en borrador o reutilizar una existente
    # publicacion, created = Publicacion.objects.get_or_create(
    #     user=request.user,
    #     categoria=categoria,
    #     estado='borrador',
    #     defaults={'titulo': '', 'contenido_html': ''}
    # )

    # # Crear un registro en el historial si la publicación es nueva
    # Historial.objects.create(
    #     publicacion=publicacion,
    #     usuario=publicacion.user,
    #     accion='creado'
    #     )

    # blocks = parse_content(publicacion.contenido_html) if publicacion.contenido_html else []

    return render(request, 'personalizable.html', {
        # 'publicacion': publicacion,
        # 'blocks': blocks,
        'categoria': categoria,
        # 'publicacion_id': publicacion.id,
    })

from django.http import JsonResponse
from .models import Publicacion

@login_required
@require_POST
def crear_publicacion_ajax(request):
    """
    Crea el borrador una sola vez y devuelve su id.
    """
    try:
        data_id = json.loads(request.body or '{}')
        categoria_id = data_id.get('categoria_id')
        if not categoria_id:
            return JsonResponse({'ok': False, 'message': 'Falta la categoría.'}, status=400)
        if not verificar_permisos_categoria_id(request, ['crear contenido'], categoria_id):
            return JsonResponse({'ok': False, 'message': 'No puedes crear contenido en esta categoría.'}, status=403)
        publicacion = Publicacion.objects.create(
            categoria_id=categoria_id,
            estado='borrador',
            user=request.user,
            titulo='',
            contenido_html='',
        )
        return JsonResponse({'ok': True, 'publicacion_id': publicacion.id}, status=201)
    except Exception as e:
        error_message = traceback.format_exc()
        print(error_message)
        return JsonResponse({'ok': False, 'message': str(e)}, status=400)


@login_required
def guardar_publicacion_ajax(request, publicacion_id):
    """
    Vista para guardar una publicación mediante una solicitud AJAX.

    Permite actualizar el título y contenido de una publicación utilizando una solicitud POST.

    Args:
        request (HttpRequest): La solicitud HTTP recibida.
        publicacion_id (int): ID de la publicación a guardar.

    Returns:
        JsonResponse: Respuesta en formato JSON con el estado de la operación.
    """

    if request.method == 'POST':
        publicacion = get_object_or_404(Publicacion, id=publicacion_id)
        if publicacion.user_id != request.user.id and not verificar_permisos_categoria_id(
            request, ['gestionar contenido otros'], publicacion.categoria_id
        ):
            return JsonResponse({'ok': False, 'message': 'No puedes editar esta publicación.'}, status=403)

        publicacion_antigua_contenido = publicacion.contenido_html
        publicacion_antigua_titulo = publicacion.titulo

        data = json.loads(request.body)
        publicacion.titulo = data.get('title', publicacion.titulo)
        publicacion.contenido_html = data.get('content', publicacion.contenido_html)
        publicacion.save()
        
        # Si la publicación es nueva, se crea un registro en el historial
        if publicacion_antigua_titulo == "" and publicacion_antigua_contenido == "" and not Historial.objects.filter(publicacion=publicacion).exists():
            Historial.objects.create(
                publicacion=publicacion,
                usuario=request.user,
                accion='creado'
            )

        #Si solo el contenido de la publicacion se cambio, se crea un registro en el historial
        elif publicacion_antigua_contenido != publicacion.contenido_html and publicacion_antigua_titulo == publicacion.titulo:
            Historial.objects.create(
                publicacion=publicacion,
                usuario=request.user,
                accion='modificado_cuerpo'
            )
        # Si solo el titulo de la publicacion se cambio, se crea un registro en el historial
        elif publicacion_antigua_titulo != publicacion.titulo and publicacion_antigua_contenido == publicacion.contenido_html:
            Historial.objects.create(
                publicacion=publicacion,
                usuario=request.user,
                accion='modificado_titulo'
            )
        # Si se cambio tanto el contenido como el titulo de la publicacion, se crea un registro en el historial
        elif publicacion_antigua_titulo != publicacion.titulo and publicacion_antigua_contenido != publicacion.contenido_html:
            Historial.objects.create(
                publicacion=publicacion,
                usuario=request.user,
                accion='modificado_titulo_cuerpo'
            )


        # tiempo_limite = timezone.now() - timedelta(seconds=12)
        # if not Historial.objects.filter(publicacion=publicacion, fecha_evento__gt=tiempo_limite, accion='creado').exists():
        #     Historial.objects.create(
        #         publicacion=publicacion,
        #         usuario=request.user,
        #         accion='modificado'
        #     )


        return JsonResponse({'ok': True, 'publicacion_id': publicacion.id, 'message': 'Guardado.'})
    return JsonResponse({'ok': False, 'message': 'Método no permitido.'}, status=405)

@login_required
def comentario(request, publicacion_id):
    """
    Vista para agregar un comentario a una publicación.

    Permite al usuario autenticado agregar un comentario a la publicación especificada.

    Args:
        request (HttpRequest): La solicitud HTTP recibida.
        publicacion_id (int): ID de la publicación a comentar.

    Returns:
        HttpResponse: Renderiza la página de comentarios o redirige tras agregar el comentario.
    """

    # Obtener la publicación en base al id
    publicacion = get_object_or_404(Publicacion, id=publicacion_id)
    if not verificar_permisos_categoria_id(request, ['interactuar publicaciones'], publicacion.categoria_id):
        if _es_fetch(request):
            return JsonResponse({'ok': False, 'message': 'No puedes comentar en esta categoría.'}, status=403)
        return render(request, 'sin_permiso.html')
    ##
    # Si el formulario ha sido enviado
    if request.method == 'POST':
        form = ComentarioForm(request.POST)
        if not form.is_valid():
            if _es_fetch(request):
                return JsonResponse({'ok': False, 'message': 'Escribe un comentario antes de publicarlo.'}, status=400)
            return render(request, 'comentar.html', {'form': form, 'publicacion': publicacion})
        comentario = form.save(commit=False)
        comentario.user = request.user
        comentario.publicacion = publicacion
        comentario.save()
        if _es_fetch(request):
            return JsonResponse({
                'ok': True,
                'comentario': {
                    'id': comentario.id,
                    'username': comentario.user.username,
                    'perfil': reverse('perfil', args=[comentario.user.username]),
                    'fecha': timezone.localtime(comentario.fecha_creacion).strftime('%d %b %Y, %H:%M'),
                    'descripcion': comentario.descripcion,
                    'eliminar': reverse('eliminar_comentario', args=[comentario.id]),
                },
            })
        return redirect(f"{reverse('previsualizar_publicacion', args=[publicacion_id])}#comentario_{comentario.id}")
    else:
        form = ComentarioForm()

    # Renderizar el template y pasar el formulario y la publicación al contexto
    return render(request, 'comentar.html', {
        'form': form, 
        'publicacion': publicacion
        })

@login_required
@require_POST
def eliminar_comentario(request, comentario_id):
    """
    Elimina un comentario propio, o uno ajeno si el rol lo permite.
    Solo acepta POST: visitar la URL no borra nada.
    """

    comentario = get_object_or_404(Comentario, id=comentario_id)
    publicacion = comentario.publicacion
    if comentario.user_id != request.user.id:
        if not verificar_permisos_categoria_id(request, ['gestionar contenido otros'], publicacion.categoria_id):
            return _respuesta_accion(request, {'ok': False, 'message': 'No puedes eliminar este comentario.'}, status=403)

    publicacion_id = publicacion.id
    comentario.delete()
    if _es_fetch(request):
        return JsonResponse({'ok': True})
    return redirect('previsualizar_publicacion', publicacion_id=publicacion_id)
    
@csrf_exempt
def modificar_publicacion_ajax(request, id):
    """
    Vista para modificar una publicación existente mediante una solicitud AJAX.

    Permite actualizar el título, contenido y categoría de una publicación.

    Args:
        request (HttpRequest): La solicitud HTTP recibida.
        id (int): ID de la publicación a modificar.

    Returns:
        JsonResponse: Respuesta en formato JSON con el estado de la operación.
    """

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            publicacion = Publicacion.objects.get(id=id)
            publicacion.titulo = data.get('title', publicacion.titulo)
            publicacion.contenido_html = data.get('content', publicacion.contenido_html)
            publicacion.categoria_id = data.get('categoria_id', publicacion.categoria_id)
            publicacion.save()

            return JsonResponse({'message': 'Publicación actualizada con éxito.'}, status=200)
        except Publicacion.DoesNotExist:
            return JsonResponse({'message': 'Publicación no encontrada.'}, status=404)
        except Exception as e:
            return JsonResponse({'message': f'Error: {str(e)}'}, status=500)
    return JsonResponse({'message': 'Método no permitido.'}, status=405)

@login_required
def historial_publicacion(request, publicacion_id):
    """
    Vista para mostrar el historial de una publicación.
    """
    publicacion = get_object_or_404(Publicacion, id=publicacion_id)

    if(publicacion.user_id != request.user.id):
            if not verificar_permisos_categoria_id(request, ['acceder reportes'], publicacion.categoria_id):
                return render(request, 'sin_permiso.html')

    historial = Historial.objects.filter(publicacion=publicacion).order_by('-fecha_evento')

    
    context = {
        'publicacion': publicacion,
        'historial': historial,
    }
    return render(request, 'historial_publicacion.html', context)

