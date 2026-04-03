from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render

from tasks.forms import TaskLinkForm
from tasks.models import Task, TaskLink


def link_form(request, task_id):
    task = get_object_or_404(Task, pk=task_id)
    form = TaskLinkForm()
    return render(
        request,
        "tasks/partials/link_form.html",
        {"form": form, "task": task},
    )


def link_create(request, task_id):
    task = get_object_or_404(Task, pk=task_id)
    form = TaskLinkForm(request.POST)
    if form.is_valid():
        link = form.save(commit=False)
        link.task = task
        link.position = task.links.count()
        link.save()
        return render(
            request,
            "tasks/partials/link_item.html",
            {"link": link},
        )
    return render(
        request,
        "tasks/partials/link_form.html",
        {"form": form, "task": task},
    )


def link_delete(request, link_id):
    link = get_object_or_404(TaskLink, pk=link_id)
    link.delete()
    return HttpResponse("")
