from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from tasks.forms import TaskListForm
from tasks.models import TaskList


def task_list_form(request, list_id=None):
    if list_id:
        task_list = get_object_or_404(TaskList, pk=list_id)
        form = TaskListForm(instance=task_list)
    else:
        task_list = None
        form = TaskListForm()
    return render(
        request,
        "tasks/partials/task_list_form.html",
        {"form": form, "task_list": task_list},
    )


def task_list_create(request):
    form = TaskListForm(request.POST)
    if form.is_valid():
        task_list = form.save(commit=False)
        task_list.position = TaskList.objects.count()
        task_list.column = task_list.position % 2
        task_list.save()
        return redirect("tasks:dashboard")
    return render(
        request,
        "tasks/partials/task_list_form.html",
        {"form": form, "task_list": None},
    )


def task_list_update(request, list_id):
    task_list = get_object_or_404(TaskList, pk=list_id)
    form = TaskListForm(request.POST, instance=task_list)
    if form.is_valid():
        form.save()
        return redirect("tasks:dashboard")
    return render(
        request,
        "tasks/partials/task_list_form.html",
        {"form": form, "task_list": task_list},
    )


def task_list_delete(request, list_id):
    task_list = get_object_or_404(TaskList, pk=list_id)
    task_list.delete()
    return HttpResponse("")
