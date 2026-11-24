const draggables = document.querySelectorAll(".task");
const droppables = document.querySelectorAll(".swim-lane");
const status = document.getElementById("board-status");
const confirmBar = document.getElementById("board-confirm");
const confirmText = document.getElementById("board-confirm-text");
const confirmYes = document.getElementById("board-confirm-yes");
const confirmNo = document.getElementById("board-confirm-no");
let pending = null;

function say(message, kind) {
    if (!status) {
        return;
    }
    status.textContent = message;
    status.classList.remove("is-error", "is-ok", "is-busy");
    if (kind) {
        status.classList.add(kind);
    }
}

function lane(state) {
    return document.querySelector('.swim-lane[data-state="' + state + '"]');
}

function revert(task, origin) {
    const back = lane(origin);
    if (back) {
        back.appendChild(task);
    }
}

function hideConfirm() {
    pending = null;
    if (confirmBar) {
        confirmBar.hidden = true;
    }
}

function commit(task, newState, origin) {
    say("Guardando", "is-busy");
    fetch("/Tablero/update_task_state/" + task.getAttribute("data-id") + "/", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCookie("csrftoken"),
            "X-Requested-With": "fetch",
            "Accept": "application/json"
        },
        body: JSON.stringify({ estado: newState })
    })
        .then(function (response) {
            return response.json().then(function (data) {
                return { ok: response.ok && data.ok, data: data };
            }).catch(function () {
                return { ok: false, data: { message: "No se pudo guardar. La tarjeta volvió a su columna." } };
            });
        })
        .then(function (result) {
            if (!result.ok) {
                throw new Error(result.data.message || "No se pudo guardar. La tarjeta volvió a su columna.");
            }
            task.dataset.origin = newState;
            say(result.data.message || "Estado actualizado.", "is-ok");
        })
        .catch(function (error) {
            revert(task, origin);
            say(error.message || "Sin conexión. La tarjeta volvió a su columna.", "is-error");
        });
}

draggables.forEach(function (task) {
    task.addEventListener("dragstart", function () {
        if (pending) {
            return;
        }
        task.classList.add("is-dragging");
        task.dataset.origin = task.parentElement.getAttribute("data-state");
    });

    task.addEventListener("dragend", function () {
        task.classList.remove("is-dragging");
        if (pending) {
            return;
        }
        const newState = task.parentElement.getAttribute("data-state");
        const origin = task.dataset.origin;
        const taskId = task.getAttribute("data-id");
        if (!newState || !taskId || newState === origin) {
            return;
        }
        if (newState === "publicado" || newState === "rechazado") {
            pending = { task: task, newState: newState, origin: origin };
            if (confirmText) {
                confirmText.textContent = newState === "publicado"
                    ? "Vas a publicar esta nota. El cambio queda visible para los lectores."
                    : "Vas a rechazar esta nota. Deja de estar en revisión.";
            }
            if (confirmBar) {
                confirmBar.hidden = false;
            }
            return;
        }
        commit(task, newState, origin);
    });
});

if (confirmYes) {
    confirmYes.addEventListener("click", function () {
        if (!pending) {
            return;
        }
        const current = pending;
        hideConfirm();
        commit(current.task, current.newState, current.origin);
    });
}

if (confirmNo) {
    confirmNo.addEventListener("click", function () {
        if (!pending) {
            return;
        }
        revert(pending.task, pending.origin);
        hideConfirm();
        say("Cambio cancelado. La publicación sigue donde estaba.", "is-ok");
    });
}

droppables.forEach(function (zone) {
    zone.addEventListener("dragover", function (event) {
        event.preventDefault();
        if (pending) {
            return;
        }
        const current = document.querySelector(".is-dragging");
        if (current) {
            zone.appendChild(current);
        }
    });
});

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
        const cookies = document.cookie.split(";");
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === name + "=") {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
