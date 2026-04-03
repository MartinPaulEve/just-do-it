from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render

from tasks.models import Task, TaskAttachment


def attachment_create(request, task_id):
    task = get_object_or_404(Task, pk=task_id)
    uploaded_file = request.FILES.get("file")
    if uploaded_file:
        attachment = TaskAttachment.objects.create(
            task=task,
            file=uploaded_file,
            filename=uploaded_file.name,
        )
        return render(
            request,
            "tasks/partials/attachment_item.html",
            {"attachment": attachment},
        )
    return HttpResponse("")


def attachment_delete(request, attachment_id):
    attachment = get_object_or_404(TaskAttachment, pk=attachment_id)
    attachment.file.delete(save=False)
    attachment.delete()
    return HttpResponse("")
