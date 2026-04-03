from django.urls import path

from tasks.views import (
    attachment_create,
    attachment_delete,
    dashboard_view,
    followup_create,
    followup_form,
    link_create,
    link_delete,
    link_form,
    reorder_panels,
    reorder_tasks,
    subtask_create,
    subtask_form,
    subtask_toggle,
    task_collapse,
    task_create,
    task_create_form,
    task_delete,
    task_expand,
    task_list_create,
    task_list_delete,
    task_list_form,
    task_list_panel_partial,
    task_list_update,
    task_toggle,
    task_update,
)

app_name = "tasks"

urlpatterns = [
    path("", dashboard_view, name="dashboard"),
    path("panel/<int:list_id>/", task_list_panel_partial, name="panel"),
    # Task CRUD
    path("task/create-form/<int:list_id>/", task_create_form, name="task_create_form"),
    path("task/create/<int:list_id>/", task_create, name="task_create"),
    path("task/<int:task_id>/expand/", task_expand, name="task_expand"),
    path("task/<int:task_id>/collapse/", task_collapse, name="task_collapse"),
    path("task/<int:task_id>/update/", task_update, name="task_update"),
    path("task/<int:task_id>/toggle/", task_toggle, name="task_toggle"),
    path("task/<int:task_id>/delete/", task_delete, name="task_delete"),
    # Sub-tasks
    path("subtask/form/<int:parent_id>/", subtask_form, name="subtask_form"),
    path("subtask/create/<int:parent_id>/", subtask_create, name="subtask_create"),
    path("subtask/<int:task_id>/toggle/", subtask_toggle, name="subtask_toggle"),
    # Follow-up
    path("followup/form/<int:task_id>/", followup_form, name="followup_form"),
    path("followup/create/<int:task_id>/", followup_create, name="followup_create"),
    # Attachments
    path(
        "attachment/create/<int:task_id>/",
        attachment_create,
        name="attachment_create",
    ),
    path(
        "attachment/<int:attachment_id>/delete/",
        attachment_delete,
        name="attachment_delete",
    ),
    # Links
    path("link/form/<int:task_id>/", link_form, name="link_form"),
    path("link/create/<int:task_id>/", link_create, name="link_create"),
    path("link/<int:link_id>/delete/", link_delete, name="link_delete"),
    # Reorder
    path("reorder/panels/", reorder_panels, name="reorder_panels"),
    path("reorder/tasks/", reorder_tasks, name="reorder_tasks"),
    # TaskList CRUD
    path("lists/form/", task_list_form, name="task_list_form"),
    path("lists/form/<int:list_id>/", task_list_form, name="task_list_form_edit"),
    path("lists/create/", task_list_create, name="task_list_create"),
    path("lists/<int:list_id>/update/", task_list_update, name="task_list_update"),
    path("lists/<int:list_id>/delete/", task_list_delete, name="task_list_delete"),
    # Stub routes for future tasks
    path("today/", dashboard_view, name="today"),
    path("calendar/", dashboard_view, name="calendar"),
    path("all/", dashboard_view, name="all_tasks"),
]
