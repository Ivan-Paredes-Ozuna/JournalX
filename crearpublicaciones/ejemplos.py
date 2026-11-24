"""Textos de ejemplo que viajan con el código.

La migración inicial y el comando `preparar` los crean como publicaciones
normales. Si alguien los borra, no vuelven solos.
"""

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
