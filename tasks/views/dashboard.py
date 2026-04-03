from collections import defaultdict

from django.shortcuts import get_object_or_404, render

from tasks.models import Task, TaskList
from tasks.recurrence import ensure_series_generated


def dashboard_view(request):
    ensure_series_generated()
    task_lists = TaskList.objects.all()
    columns = defaultdict(list)
    for tl in task_lists:
        columns[tl.column].append(tl)
    max_col = max(columns.keys(), default=0)
    ordered_columns = [columns.get(i, []) for i in range(max_col + 1)]
    # Ensure at least 2 columns for the grid
    while len(ordered_columns) < 2:
        ordered_columns.append([])
    return render(
        request,
        "tasks/dashboard.html",
        {
            "columns": ordered_columns,
            "nav_active": "dashboard",
        },
    )


def task_list_panel_partial(request, list_id):
    task_list = get_object_or_404(TaskList, pk=list_id)
    tasks = Task.objects.filter(task_list=task_list, parent_task__isnull=True).active()
    return render(
        request,
        "tasks/partials/task_list_panel.html",
        {"task_list": task_list, "tasks": tasks},
    )
