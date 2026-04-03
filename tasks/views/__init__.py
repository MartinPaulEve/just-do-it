from tasks.views.all_tasks import all_tasks_view
from tasks.views.attachments import attachment_create, attachment_delete
from tasks.views.calendar import calendar_events, calendar_view
from tasks.views.dashboard import dashboard_view, task_list_panel_partial
from tasks.views.followup import followup_create, followup_form
from tasks.views.links import link_create, link_delete, link_form
from tasks.views.reorder import reorder_panels, reorder_tasks
from tasks.views.subtask import subtask_create, subtask_form, subtask_toggle
from tasks.views.task_crud import (
    task_collapse,
    task_create,
    task_create_form,
    task_delete,
    task_expand,
    task_toggle,
    task_update,
)
from tasks.views.task_list_crud import (
    task_list_create,
    task_list_delete,
    task_list_form,
    task_list_update,
)
from tasks.views.today import today_view

__all__ = [
    "all_tasks_view",
    "attachment_create",
    "attachment_delete",
    "calendar_events",
    "calendar_view",
    "dashboard_view",
    "today_view",
    "followup_create",
    "followup_form",
    "link_create",
    "link_delete",
    "link_form",
    "reorder_panels",
    "reorder_tasks",
    "subtask_create",
    "subtask_form",
    "subtask_toggle",
    "task_collapse",
    "task_create",
    "task_create_form",
    "task_delete",
    "task_expand",
    "task_list_create",
    "task_list_delete",
    "task_list_form",
    "task_list_panel_partial",
    "task_list_update",
    "task_toggle",
    "task_update",
]
