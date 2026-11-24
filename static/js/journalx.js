(function () {
    const header = document.querySelector(".site-header");
    const toggle = document.querySelector(".nav-toggle");

    if (toggle && header) {
        toggle.addEventListener("click", function () {
            const open = header.classList.toggle("is-open");
            toggle.setAttribute("aria-expanded", open ? "true" : "false");
        });
    }

    document.addEventListener("click", function (event) {
        document.querySelectorAll("details.menu[open]").forEach(function (menu) {
            if (!menu.contains(event.target)) {
                menu.removeAttribute("open");
            }
        });
    });

    document.addEventListener("keydown", function (event) {
        if (event.key !== "Escape") {
            return;
        }
        document.querySelectorAll("details.menu[open]").forEach(function (menu) {
            menu.removeAttribute("open");
        });
        if (header) {
            header.classList.remove("is-open");
        }
        if (toggle) {
            toggle.setAttribute("aria-expanded", "false");
        }
    });

    document.querySelectorAll(".auth input, .auth textarea").forEach(function (field) {
        field.removeAttribute("placeholder");
    });

    document.addEventListener("click", function (event) {
        const likeButton = event.target.closest("[data-like]");
        if (likeButton) {
            event.preventDefault();
            alternarMeGusta(likeButton);
            return;
        }
        const deleteButton = event.target.closest("[data-delete]");
        if (deleteButton) {
            event.preventDefault();
            eliminarEnPagina(deleteButton);
        }
    });
})();

function csrfToken() {
    const input = document.querySelector("[name=csrfmiddlewaretoken]");
    if (input) {
        return input.value;
    }
    const match = document.cookie.match(/(?:^|; )csrftoken=([^;]+)/);
    return match ? decodeURIComponent(match[1]) : "";
}

function textoMeGusta(cantidad) {
    return cantidad === 1 ? "1 me gusta" : cantidad + " me gusta";
}

function alternarMeGusta(button) {
    if (button.disabled) {
        return;
    }
    const liked = button.getAttribute("aria-pressed") === "true";
    const url = liked ? button.dataset.unlikeUrl : button.dataset.likeUrl;
    const count = document.getElementById("like-count");
    const status = document.getElementById("like-status");
    button.disabled = true;
    if (status) {
        status.textContent = liked ? "Quitando me gusta…" : "Guardando me gusta…";
    }

    fetch(url, {
        method: "POST",
        headers: {
            "X-CSRFToken": csrfToken(),
            "X-Requested-With": "fetch",
            "Accept": "application/json"
        }
    })
        .then(function (response) {
            return response.json().then(function (data) {
                return { ok: response.ok, data: data };
            });
        })
        .then(function (result) {
            if (!result.ok) {
                throw new Error(result.data.message || "No se pudo actualizar.");
            }
            const ahora = result.data.liked === true;
            button.setAttribute("aria-pressed", ahora ? "true" : "false");
            button.classList.toggle("is-on", ahora);
            button.textContent = ahora ? "Quitar me gusta" : "Me gusta";
            if (count) {
                count.textContent = textoMeGusta(result.data.me_gustas);
            }
            if (status) {
                status.textContent = ahora ? "Sumaste un me gusta." : "Quitaste tu me gusta.";
            }
        })
        .catch(function (error) {
            if (status) {
                status.textContent = error.message || "No se pudo actualizar. Inténtalo otra vez.";
            }
        })
        .finally(function () {
            button.disabled = false;
        });
}

function eliminarEnPagina(button) {
    if (button.disabled) {
        return;
    }
    const mensaje = button.dataset.confirm || "¿Eliminar? Esta acción no se puede deshacer.";
    if (!window.confirm(mensaje)) {
        return;
    }
    button.disabled = true;
    button.textContent = "Eliminando…";

    fetch(button.dataset.delete, {
        method: "POST",
        headers: {
            "X-CSRFToken": csrfToken(),
            "X-Requested-With": "fetch",
            "Accept": "application/json"
        }
    })
        .then(function (response) {
            return response.json().then(function (data) {
                return { ok: response.ok, data: data };
            });
        })
        .then(function (result) {
            if (!result.ok) {
                throw new Error(result.data.message || "No se pudo eliminar.");
            }
            const pieza = button.closest(button.dataset.remove || "[data-removable]");
            if (button.dataset.after && pieza) {
                const aviso = document.createElement("div");
                aviso.className = "notice";
                aviso.innerHTML = "<h2>Listo, se eliminó.</h2><p><a href=\"" + button.dataset.after + "\">Volver</a></p>";
                pieza.replaceWith(aviso);
                return;
            }
            if (pieza) {
                pieza.remove();
            }
        })
        .catch(function (error) {
            button.disabled = false;
            button.textContent = button.dataset.label || "Eliminar";
            window.alert(error.message || "No se pudo eliminar.");
        });
}

function cargarResultados(url, push) {
    const resultados = document.getElementById("resultados");
    const aviso = document.getElementById("resultados-status");
    if (!resultados) {
        window.location.href = url;
        return;
    }
    if (push !== false) {
        history.pushState(null, "", url);
    }
    resultados.classList.add("is-loading");
    resultados.setAttribute("aria-busy", "true");
    if (aviso) {
        aviso.textContent = "Buscando…";
        aviso.classList.remove("is-error", "is-ok");
    }
    fetch(url, {
        headers: {
            "X-Requested-With": "fetch",
            "Accept": "application/json"
        }
    })
        .then(function (response) {
            return response.json().then(function (data) {
                return { ok: response.ok, data: data };
            });
        })
        .then(function (result) {
            if (!result.ok || !result.data.html) {
                throw new Error((result.data && result.data.message) || "No se pudo actualizar la lista.");
            }
            resultados.innerHTML = result.data.html;
            if (aviso) {
                aviso.textContent = "";
            }
        })
        .catch(function (error) {
            if (aviso) {
                aviso.textContent = error.message || "No se pudo actualizar la lista.";
                aviso.classList.add("is-error");
            }
        })
        .finally(function () {
            resultados.classList.remove("is-loading");
            resultados.removeAttribute("aria-busy");
        });
}

function publicarComentario(form) {
    const status = document.getElementById("comment-status");
    const button = form.querySelector("button[type=submit]");
    const lista = document.getElementById("comentario-lista");
    const vacio = document.getElementById("comentario-vacio");
    if (button) {
        button.disabled = true;
    }
    if (status) {
        status.textContent = "Publicando el comentario…";
        status.classList.remove("is-error", "is-ok");
    }
    fetch(form.action, {
        method: "POST",
        headers: {
            "X-CSRFToken": csrfToken(),
            "X-Requested-With": "fetch",
            "Accept": "application/json"
        },
        body: new FormData(form)
    })
        .then(function (response) {
            return response.json().then(function (data) {
                return { ok: response.ok, data: data };
            });
        })
        .then(function (result) {
            if (!result.ok || !result.data.comentario) {
                throw new Error(result.data.message || "No se pudo publicar el comentario.");
            }
            const dato = result.data.comentario;
            const article = document.createElement("article");
            article.className = "comment";
            article.id = "comentario_" + dato.id;
            const title = document.createElement("h3");
            const link = document.createElement("a");
            link.href = dato.perfil;
            link.textContent = dato.username;
            title.appendChild(link);
            const when = document.createElement("p");
            when.className = "when";
            when.textContent = dato.fecha;
            const body = document.createElement("p");
            body.textContent = dato.descripcion;
            const remove = document.createElement("button");
            remove.type = "button";
            remove.className = "btn-danger";
            remove.dataset.delete = dato.eliminar;
            remove.dataset.remove = ".comment";
            remove.dataset.label = "Eliminar comentario";
            remove.dataset.confirm = "¿Eliminar este comentario?";
            remove.textContent = "Eliminar comentario";
            article.append(title, when, body, remove);
            if (vacio) {
                vacio.remove();
            }
            if (lista) {
                lista.prepend(article);
            }
            form.reset();
            if (status) {
                status.textContent = "Comentario publicado.";
                status.classList.add("is-ok");
            }
        })
        .catch(function (error) {
            if (status) {
                status.textContent = error.message || "No se pudo publicar el comentario.";
                status.classList.add("is-error");
            }
        })
        .finally(function () {
            if (button) {
                button.disabled = false;
            }
        });
}

(function () {
    const resultados = document.getElementById("resultados");
    if (resultados) {
        const headerSearch = document.querySelector(".header-search");
        if (headerSearch) {
            headerSearch.addEventListener("submit", function (event) {
                event.preventDefault();
                const params = new URLSearchParams(new FormData(headerSearch));
                cargarResultados(headerSearch.action + "?" + params.toString());
            });
        }
        const filters = document.getElementById("search-filters");
        if (filters) {
            filters.addEventListener("submit", function (event) {
                event.preventDefault();
                const params = new URLSearchParams(new FormData(filters));
                cargarResultados(filters.action + "?" + params.toString());
            });
        }
        const clearFilters = document.getElementById("clear-filters");
        if (clearFilters) {
            clearFilters.addEventListener("click", function (event) {
                event.preventDefault();
                if (filters) {
                    filters.reset();
                }
                if (headerSearch) {
                    headerSearch.reset();
                }
                cargarResultados(clearFilters.href);
            });
        }
        resultados.addEventListener("click", function (event) {
            const link = event.target.closest("a");
            if (!link || !resultados.contains(link)) {
                return;
            }
            if (link.closest(".pagination") || link.closest(".empty")) {
                event.preventDefault();
                cargarResultados(link.href);
            }
        });
        window.addEventListener("popstate", function () {
            cargarResultados(window.location.href, false);
        });
    }

    const commentForm = document.getElementById("comment-form");
    if (commentForm) {
        commentForm.addEventListener("submit", function (event) {
            event.preventDefault();
            publicarComentario(commentForm);
        });
    }
})();

