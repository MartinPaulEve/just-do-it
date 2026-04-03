from django.http import HttpResponse
from django.urls import path

from tasks.views import dashboard_view, task_list_panel_partial

app_name = "tasks"


def _stub(request, *args, **kwargs):
    return HttpResponse(status=501)


urlpatterns = [
    path("", dashboard_view, name="dashboard"),
    path("panel/<int:list_id>/", task_list_panel_partial, name="panel"),
    # Stubs — replaced in later tasks
    path("today/", _stub, name="today"),
    path("calendar/", _stub, name="calendar"),
    path("all/", _stub, name="all_tasks"),
    path("lists/new/", _stub, name="task_list_form"),
    path("tasks/<int:task_id>/toggle/", _stub, name="task_toggle"),
    path("tasks/<int:task_id>/expand/", _stub, name="task_expand"),
    path("lists/<int:list_id>/tasks/new/", _stub, name="task_create_form"),
]
