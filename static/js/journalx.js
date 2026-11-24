(function () {
    const header = document.querySelector(".site-header");
    const toggle = document.querySelector(".nav-toggle");

    if (toggle && header) {
        toggle.addEventListener("click", function () {
            const open = header.classList.toggle("is-open");
            toggle.setAttribute("aria-expanded", open ? "true" : "false");
        });
    }

    document.querySelectorAll("details.menu").forEach(function (menu) {
        const summary = menu.querySelector("summary");
        if (!summary) {
            return;
        }
        summary.addEventListener("click", function (event) {
            if (menu.classList.contains("is-closing")) {
                event.preventDefault();
                menu.classList.remove("is-closing");
                return;
            }
            if (!menu.open) {
                return;
            }
            event.preventDefault();
            closeMenu(menu);
        });
    });

    document.addEventListener("click", function (event) {
        document.querySelectorAll("details.menu[open]").forEach(function (menu) {
            if (!menu.contains(event.target)) {
                closeMenu(menu);
            }
        });
    });

    document.addEventListener("keydown", function (event) {
        if (event.key !== "Escape") {
            return;
        }
        document.querySelectorAll("details.menu[open]").forEach(function (menu) {
            closeMenu(menu);
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
            return;
        }
        const undoLink = event.target.closest("[data-undo]");
        if (undoLink) {
            event.preventDefault();
            cerrarDeshacer(true);
            abrirDeshacer(undoLink.dataset.undo || "Se eliminará.", function () {}, function () {
                const form = document.createElement("form");
                form.method = "POST";
                form.action = undoLink.href;
                const input = document.createElement("input");
                input.type = "hidden";
                input.name = "csrfmiddlewaretoken";
                input.value = csrfToken();
                form.appendChild(input);
                document.body.appendChild(form);
                form.submit();
            });
        }
    });
})();

function closeMenu(menu) {
    if (!menu.open) {
        return;
    }
    const panel = menu.querySelector(".menu-panel");
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (!panel || reduce) {
        menu.classList.remove("is-closing");
        menu.removeAttribute("open");
        return;
    }
    if (menu.classList.contains("is-closing")) {
        return;
    }
    menu.classList.add("is-closing");
    const finish = function () {
        if (!menu.classList.contains("is-closing")) {
            return;
        }
        menu.classList.remove("is-closing");
        menu.removeAttribute("open");
    };
    panel.addEventListener("transitionend", function done(event) {
        if (event.target !== panel) {
            return;
        }
        panel.removeEventListener("transitionend", done);
        finish();
    });
    window.setTimeout(finish, 280);
}

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

function ocupar(elemento) {
    if (!elemento) {
        return;
    }
    elemento.classList.add("is-busy");
    elemento.setAttribute("aria-busy", "true");
    if ("disabled" in elemento) {
        elemento.disabled = true;
    }
}

function liberar(elemento) {
    if (!elemento) {
        return;
    }
    elemento.classList.remove("is-busy");
    elemento.removeAttribute("aria-busy");
    if ("disabled" in elemento) {
        elemento.disabled = false;
    }
}

function esqueletoHistoria() {
    const article = document.createElement("article");
    article.className = "story skeleton-card";
    article.setAttribute("aria-hidden", "true");
    ["is-short", "is-title", "", "is-mid"].forEach(function (extra) {
        const line = document.createElement("span");
        line.className = "skeleton" + (extra ? " " + extra : "");
        article.appendChild(line);
    });
    return article;
}

function esqueletoComentario() {
    const article = document.createElement("article");
    article.className = "comment skeleton-card";
    article.setAttribute("aria-hidden", "true");
    ["is-short", "", "is-mid"].forEach(function (extra) {
        const line = document.createElement("span");
        line.className = "skeleton" + (extra ? " " + extra : "");
        article.appendChild(line);
    });
    return article;
}

function alternarMeGusta(button) {
    if (button.disabled) {
        return;
    }
    const liked = button.getAttribute("aria-pressed") === "true";
    const url = liked ? button.dataset.unlikeUrl : button.dataset.likeUrl;
    const count = document.getElementById("like-count");
    const status = document.getElementById("like-status");
    ocupar(button);
    if (status) {
        status.textContent = "";
        status.classList.remove("is-error", "is-ok");
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
            liberar(button);
        });
}

function eliminarEnPagina(button) {
    if (button.disabled || button.classList.contains("is-busy")) {
        return;
    }
    const pieza = button.closest(button.dataset.remove || "[data-removable]");
    if (!pieza || !pieza.parentNode) {
        return;
    }
    const padre = pieza.parentNode;
    const siguiente = pieza.nextSibling;
    const url = button.dataset.delete;
    const despues = button.dataset.after;
    cerrarDeshacer(true);
    pieza.remove();
    abrirDeshacer("Se eliminó.", function () {
        if (siguiente && siguiente.parentNode === padre) {
            padre.insertBefore(pieza, siguiente);
        } else {
            padre.appendChild(pieza);
        }
    }, function () {
        return fetch(url, {
            method: "POST",
            headers: {
                "X-CSRFToken": csrfToken(),
                "X-Requested-With": "fetch",
                "Accept": "application/json"
            },
            keepalive: true
        }).then(function (response) {
            return response.json().then(function (data) {
                if (!response.ok) {
                    throw new Error(data.message || "No se pudo eliminar.");
                }
                if (despues) {
                    const aviso = document.createElement("div");
                    aviso.className = "notice";
                    const titulo = document.createElement("h2");
                    titulo.textContent = "Listo, se eliminó.";
                    const parrafo = document.createElement("p");
                    const link = document.createElement("a");
                    link.href = despues;
                    link.textContent = "Volver";
                    parrafo.appendChild(link);
                    aviso.append(titulo, parrafo);
                    if (siguiente && siguiente.parentNode === padre) {
                        padre.insertBefore(aviso, siguiente);
                    } else if (padre) {
                        padre.appendChild(aviso);
                    }
                }
            });
        }).catch(function (error) {
            if (siguiente && siguiente.parentNode === padre) {
                padre.insertBefore(pieza, siguiente);
            } else if (padre) {
                padre.appendChild(pieza);
            }
            window.alert(error.message || "No se pudo eliminar.");
        });
    });
}

let deshacerTimer = null;
let deshacerCerrar = null;

function abrirDeshacer(mensaje, deshacer, confirmar) {
    let barra = document.getElementById("undo-bar");
    if (!barra) {
        barra = document.createElement("div");
        barra.id = "undo-bar";
        barra.className = "undo-bar";
        barra.setAttribute("role", "status");
        const texto = document.createElement("p");
        const boton = document.createElement("button");
        boton.type = "button";
        boton.className = "btn-ghost";
        boton.textContent = "Deshacer";
        barra.append(texto, boton);
        document.body.appendChild(barra);
    }
    barra.hidden = false;
    barra.querySelector("p").textContent = mensaje;
    const boton = barra.querySelector("button");
    deshacerCerrar = function (ejecutar) {
        clearTimeout(deshacerTimer);
        deshacerTimer = null;
        barra.hidden = true;
        if (ejecutar && confirmar) {
            const accion = confirmar;
            confirmar = null;
            deshacer = null;
            accion();
        }
    };
    boton.onclick = function () {
        clearTimeout(deshacerTimer);
        deshacerTimer = null;
        barra.hidden = true;
        if (deshacer) deshacer();
        deshacer = null;
        confirmar = null;
    };
    deshacerTimer = setTimeout(function () {
        if (deshacerCerrar) deshacerCerrar(true);
    }, 5000);
}

function cerrarDeshacer(ejecutar) {
    if (deshacerCerrar) deshacerCerrar(ejecutar);
}

window.addEventListener("pagehide", function () {
    cerrarDeshacer(true);
});

function sincronizarFiltros(url) {
    const campos = {
        keyword: "keyword",
        category: "categoria",
        "date-from": "fecha",
        autor: "autor"
    };
    let params;
    try {
        params = new URL(url, window.location.origin).searchParams;
    } catch (error) {
        return;
    }
    Object.keys(campos).forEach(function (nombre) {
        const campo = document.getElementById(campos[nombre]);
        if (campo) {
            campo.value = params.get(nombre) || "";
        }
    });
    const buscador = document.querySelector(".header-search [name=keyword]");
    if (buscador) {
        buscador.value = params.get("keyword") || "";
    }
    if (window.pintarFiltros) {
        window.pintarFiltros();
    }
}

function cargarResultados(url, push) {
    const resultados = document.getElementById("resultados");
    const aviso = document.getElementById("resultados-status");
    if (!resultados) {
        window.location.href = url;
        return;
    }
    const turno = (resultados._turno || 0) + 1;
    resultados._turno = turno;
    if (push !== false) {
        history.pushState(null, "", url);
    }
    sincronizarFiltros(url);
    if (!resultados.classList.contains("is-loading")) {
        resultados.dataset.previous = resultados.innerHTML;
    }
    resultados.classList.add("is-loading");
    resultados.setAttribute("aria-busy", "true");
    resultados.replaceChildren();
    const lista = document.createElement("div");
    lista.className = "story-list";
    lista.append(esqueletoHistoria(), esqueletoHistoria(), esqueletoHistoria());
    resultados.appendChild(lista);
    if (aviso) {
        aviso.textContent = "";
        aviso.classList.remove("is-error", "is-ok", "is-busy");
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
            if (turno !== resultados._turno) {
                return;
            }
            if (!result.ok || !result.data.html) {
                throw new Error((result.data && result.data.message) || "No se pudo actualizar la lista.");
            }
            resultados.innerHTML = result.data.html;
            delete resultados.dataset.previous;
            if (aviso) {
                aviso.textContent = "";
            }
        })
        .catch(function (error) {
            if (turno !== resultados._turno) {
                return;
            }
            if (resultados.dataset.previous) {
                resultados.innerHTML = resultados.dataset.previous;
                delete resultados.dataset.previous;
            }
            if (aviso) {
                aviso.textContent = error.message || "No se pudo actualizar la lista.";
                aviso.classList.add("is-error");
            }
        })
        .finally(function () {
            if (turno !== resultados._turno) {
                return;
            }
            resultados.classList.remove("is-loading");
            resultados.removeAttribute("aria-busy");
        });
}

function publicarComentario(form) {
    const status = document.getElementById("comment-status");
    const button = form.querySelector("button[type=submit]");
    const lista = document.getElementById("comentario-lista");
    const vacio = document.getElementById("comentario-vacio");
    ocupar(button);
    const espera = esqueletoComentario();
    if (vacio) {
        vacio.hidden = true;
    }
    if (lista) {
        lista.prepend(espera);
    }
    if (status) {
        status.textContent = "";
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
            espera.remove();
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
            espera.remove();
            if (vacio) {
                vacio.hidden = false;
            }
            if (status) {
                status.textContent = error.message || "No se pudo publicar el comentario.";
                status.classList.add("is-error");
            }
        })
        .finally(function () {
            liberar(button);
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

    iniciarTooltips();

    const commentForm = document.getElementById("comment-form");
    if (commentForm) {
        commentForm.addEventListener("submit", function (event) {
            event.preventDefault();
            publicarComentario(commentForm);
        });
    }

    function iniciarTooltips() {
        const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
        const fine = window.matchMedia("(hover: hover) and (pointer: fine)").matches;
        if (!fine) return;
        document.querySelectorAll("[data-warm-group]").forEach(function (group) {
            const buttons = group.querySelectorAll("[data-tip]");
            if (!buttons.length) return;
            const tip = document.createElement("div");
            tip.className = "warm-tip";
            tip.setAttribute("role", "tooltip");
            tip.hidden = true;
            tip.innerHTML = '<div class="warm-tip-box"><span class="warm-tip-text"></span><span class="warm-tip-arrow" aria-hidden="true"></span></div>';
            document.body.appendChild(tip);
            const text = tip.querySelector(".warm-tip-text");
            const arrow = tip.querySelector(".warm-tip-arrow");
            let current = null;
            let fuse = null;
            let openTimer = 0;
            let closeTimer = 0;
            let warmUntil = 0;

            function buttonOf(node) {
                if (!node || !node.closest) return null;
                const button = node.closest("[data-tip]");
                return button && group.contains(button) ? button : null;
            }

            function isWarm() {
                return (current && !tip.hidden) || performance.now() < warmUntil;
            }

            function clearFuse() {
                if (!fuse) return;
                fuse.remove();
                fuse = null;
            }

            function place(button, travel) {
                tip.hidden = false;
                if (!travel) tip.style.transition = "none";
                const width = Math.ceil(text.scrollWidth + 20);
                const height = Math.ceil(text.offsetHeight + 12);
                const rect = button.getBoundingClientRect();
                let x = rect.left + rect.width / 2 - width / 2;
                let y = rect.top - height - 10;
                x = Math.max(8, Math.min(x, window.innerWidth - width - 8));
                let side = "top";
                if (y < 8) {
                    y = rect.bottom + 10;
                    side = "bottom";
                }
                tip.dataset.side = side;
                tip.style.width = width + "px";
                tip.style.height = height + "px";
                tip.style.transform = "translate(" + x + "px, " + y + "px)";
                const center = rect.left + rect.width / 2 - x;
                arrow.style.left = Math.max(12, Math.min(center, width - 12)) + "px";
                if (!travel) {
                    tip.offsetHeight;
                    tip.style.transition = "";
                }
            }

            function show(button, travel) {
                window.clearTimeout(openTimer);
                window.clearTimeout(closeTimer);
                clearFuse();
                const label = button.getAttribute("data-tip") || "";
                if (travel && text.textContent !== label) text.style.opacity = "0";
                text.textContent = label;
                const moving = travel && current && current !== button && !tip.hidden;
                current = button;
                place(button, moving && !reduce);
                tip.classList.add("is-in");
                tip.id = "warm-tip";
                button.setAttribute("aria-describedby", "warm-tip");
                if (text.style.opacity === "0") {
                    window.requestAnimationFrame(function () {
                        text.style.opacity = "1";
                    });
                }
            }

            function hide(instant) {
                window.clearTimeout(openTimer);
                window.clearTimeout(closeTimer);
                clearFuse();
                if (!current) return;
                const closing = current;
                warmUntil = performance.now() + 300;
                closing.removeAttribute("aria-describedby");
                if (instant || reduce) {
                    tip.classList.remove("is-in");
                    tip.hidden = true;
                    current = null;
                    return;
                }
                tip.classList.remove("is-in");
                closeTimer = window.setTimeout(function () {
                    if (current !== closing) return;
                    tip.hidden = true;
                    current = null;
                }, 180);
            }

            function arm(button) {
                if (current === button && !tip.hidden && tip.classList.contains("is-in")) return;
                window.clearTimeout(openTimer);
                window.clearTimeout(closeTimer);
                if (isWarm()) {
                    show(button, true);
                    return;
                }
                clearFuse();
                if (!reduce) {
                    fuse = document.createElement("span");
                    fuse.className = "warm-fuse";
                    fuse.setAttribute("aria-hidden", "true");
                    button.appendChild(fuse);
                    window.requestAnimationFrame(function () {
                        window.requestAnimationFrame(function () {
                            if (fuse) fuse.dataset.fuse = "arming";
                        });
                    });
                }
                openTimer = window.setTimeout(function () {
                    show(button, false);
                }, reduce ? 0 : 400);
            }

            group.addEventListener("pointerover", function (event) {
                const button = buttonOf(event.target);
                if (!button || buttonOf(event.relatedTarget) === button) return;
                arm(button);
            });

            group.addEventListener("pointerout", function (event) {
                const button = buttonOf(event.target);
                if (!button || buttonOf(event.relatedTarget) === button) return;
                window.clearTimeout(openTimer);
                clearFuse();
                if (buttonOf(event.relatedTarget)) return;
                hide(false);
            });

            group.addEventListener("focusin", function (event) {
                const button = buttonOf(event.target);
                if (button) arm(button);
            });

            group.addEventListener("focusout", function (event) {
                if (!buttonOf(event.target) || buttonOf(event.relatedTarget)) return;
                hide(false);
            });

            document.addEventListener("keydown", function (event) {
                if (event.key === "Escape") hide(true);
            });

            window.addEventListener("scroll", function () {
                if (current && !tip.hidden) place(current, false);
            }, true);

            window.addEventListener("resize", function () {
                if (current && !tip.hidden) place(current, false);
            });
        });
    }
})();

