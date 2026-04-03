from django.db.models import F
from django.shortcuts import render

from tasks.models import Task, TaskList


def all_tasks_view(request):
    tasks = Task.objects.filter(parent_task__isnull=True).select_related("task_list")
    task_lists = TaskList.objects.all()

    list_filter = request.GET.get("list")
    status_filter = request.GET.get("status")

    if list_filter:
        tasks = tasks.filter(task_list_id=list_filter)
    if status_filter == "active":
        tasks = tasks.filter(completed=False)
    elif status_filter == "completed":
        tasks = tasks.filter(completed=True)

    tasks = tasks.order_by(
        F("deadline").asc(nulls_last=True),
        "position",
    )

    return render(
        request,
        "tasks/all_tasks.html",
        {
            "tasks": tasks,
            "task_lists": task_lists,
            "nav_active": "all",
            "current_list": list_filter,
            "current_status": status_filter or "",
        },
    )
