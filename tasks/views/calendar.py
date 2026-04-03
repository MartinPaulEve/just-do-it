from django.http import JsonResponse
from django.shortcuts import render

from tasks.models import Task
from tasks.recurrence import ensure_series_generated


def calendar_view(request):
    return render(
        request,
        "tasks/calendar.html",
        {"nav_active": "calendar"},
    )


def calendar_events(request):
    start = request.GET.get("start")
    end = request.GET.get("end")
    ensure_series_generated()
    tasks = Task.objects.filter(
        deadline__isnull=False,
        parent_task__isnull=True,
        is_skipped=False,
    ).select_related("task_list", "series")
    if start:
        tasks = tasks.filter(deadline__gte=start)
    if end:
        tasks = tasks.filter(deadline__lte=end)
    events = []
    for task in tasks:
        event = {
            "id": task.pk,
            "title": task.title,
            "start": task.deadline.isoformat(),
            "allDay": True,
            "backgroundColor": task.task_list.colour,
            "borderColor": task.task_list.colour,
            "extendedProps": {
                "taskId": task.pk,
                "completed": task.completed,
                "listName": task.task_list.name,
                "recurring": task.series_id is not None,
            },
        }
        if task.completed:
            event["classNames"] = ["fc-event--completed"]
        events.append(event)
    return JsonResponse(events, safe=False)
