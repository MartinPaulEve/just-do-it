// tasks/static/tasks/js/app.js

// === HTMX Configuration ===

// Get CSRF token from cookie
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
        const cookies = document.cookie.split(";");
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === name + "=") {
                cookieValue = decodeURIComponent(
                    cookie.substring(name.length + 1)
                );
                break;
            }
        }
    }
    return cookieValue;
}

// Include CSRF token in all HTMX requests
document.body.addEventListener("htmx:configRequest", function (event) {
    if (event.detail.verb !== "get") {
        event.detail.headers["X-CSRFToken"] = getCookie("csrftoken");
    }
});

// === SortableJS Initialization ===

// Initialize sortable on task lists within panels
function initTaskSortable(container) {
    if (!container || container._sortable) return;
    container._sortable = new Sortable(container, {
        animation: 150,
        ghostClass: "task-card--dragging",
        handle: ".task-card",
        draggable: ".task-card",
        onEnd: function (evt) {
            const taskIds = Array.from(
                evt.to.querySelectorAll(".task-card")
            ).map(function (el) { return el.dataset.taskId; });
            const panelEl = evt.to.closest("[data-list-id]");
            const panelId = panelEl ? panelEl.dataset.listId : null;
            if (panelId) {
                fetch("/reorder/tasks/", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "X-CSRFToken": getCookie("csrftoken"),
                    },
                    body: JSON.stringify({
                        list_id: panelId,
                        task_ids: taskIds,
                    }),
                });
            }
        },
    });
}

// Initialize sortable on dashboard columns for panel reordering
function initPanelSortable(column) {
    if (!column || column._sortable) return;
    column._sortable = new Sortable(column, {
        animation: 150,
        ghostClass: "panel--dragging",
        group: "panels",
        draggable: ".panel",
        handle: ".panel__header",
        onEnd: function () {
            var columns = document.querySelectorAll(".dashboard__column");
            var layout = [];
            columns.forEach(function (col, colIndex) {
                col.querySelectorAll(".panel").forEach(function (panel, pos) {
                    layout.push({
                        list_id: panel.dataset.listId,
                        column: colIndex,
                        position: pos,
                    });
                });
            });
            fetch("/reorder/panels/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": getCookie("csrftoken"),
                },
                body: JSON.stringify({ layout: layout }),
            });
        },
    });
}

// Re-initialize sortables after HTMX swaps
document.body.addEventListener("htmx:afterSwap", function () {
    document.querySelectorAll(".panel__tasks").forEach(initTaskSortable);
    document.querySelectorAll(".dashboard__column").forEach(initPanelSortable);
});

// === Recurrence Form Conditional Fields ===

function updateRecurrenceFields() {
    var typeSelect = document.querySelector("[name='recurrence_type']");
    if (!typeSelect) return;
    var type = typeSelect.value;
    var dowRow = document.getElementById("recurrence-day-of-week");
    var domRow = document.getElementById("recurrence-day-of-month");
    if (dowRow) dowRow.style.display = type === "weekly" ? "flex" : "none";
    if (domRow) domRow.style.display = (type === "monthly" || type === "yearly") ? "flex" : "none";
}

document.body.addEventListener("change", function (event) {
    if (event.target.name === "recurrence_type") {
        updateRecurrenceFields();
    }
});

document.body.addEventListener("htmx:afterSwap", function () {
    updateRecurrenceFields();
});

// Initial setup
document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".panel__tasks").forEach(initTaskSortable);
    document.querySelectorAll(".dashboard__column").forEach(initPanelSortable);
});
