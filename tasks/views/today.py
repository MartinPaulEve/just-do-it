from django.shortcuts import render

from tasks.models import Task, TaskList


def today_view(request):
    task_lists = TaskList.objects.all()
    groups = []
    for tl in task_lists:
        tasks = Task.objects.filter(task_list=tl, parent_task__isnull=True).due_today()
        if tasks.exists():
            groups.append({"task_list": tl, "tasks": tasks})
    return render(
        request,
        "tasks/today.html",
        {"groups": groups, "nav_active": "today"},
    )
