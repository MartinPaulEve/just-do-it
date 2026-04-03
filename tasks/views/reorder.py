import json

from django.http import HttpResponse
from django.views.decorators.http import require_POST

from tasks.models import Task, TaskList


@require_POST
def reorder_panels(request):
    data = json.loads(request.body)
    for item in data.get("layout", []):
        TaskList.objects.filter(pk=item["list_id"]).update(
            column=item["column"], position=item["position"]
        )
    return HttpResponse(status=204)


@require_POST
def reorder_tasks(request):
    data = json.loads(request.body)
    task_ids = data.get("task_ids", [])
    for position, task_id in enumerate(task_ids):
        Task.objects.filter(pk=task_id).update(position=position)
    return HttpResponse(status=204)
