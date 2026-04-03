from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render

from tasks.forms import TaskForm
from tasks.models import Task, TaskList


def task_create_form(request, list_id):
    task_list = get_object_or_404(TaskList, pk=list_id)
    form = TaskForm()
    return render(
        request,
        "tasks/partials/task_form.html",
        {"form": form, "task_list": task_list},
    )


def task_create(request, list_id):
    task_list = get_object_or_404(TaskList, pk=list_id)
    form = TaskForm(request.POST)
    if form.is_valid():
        task = form.save(commit=False)
        task.task_list = task_list
        max_pos = Task.objects.filter(
            task_list=task_list, parent_task__isnull=True
        ).count()
        task.position = max_pos
        task.save()
    tasks = Task.objects.filter(task_list=task_list, parent_task__isnull=True).active()
    return render(
        request,
        "tasks/partials/task_list_panel.html",
        {"task_list": task_list, "tasks": tasks},
    )


def task_expand(request, task_id):
    task = get_object_or_404(
        Task.objects.select_related(
            "task_list", "follow_up_from", "parent_task"
        ).prefetch_related("subtasks", "attachments", "links"),
        pk=task_id,
    )
    form = TaskForm(instance=task)
    return render(
        request,
        "tasks/partials/task_card_expanded.html",
        {"task": task, "form": form},
    )


def task_update(request, task_id):
    task = get_object_or_404(Task, pk=task_id)
    form = TaskForm(request.POST, instance=task)
    if form.is_valid():
        form.save()
    return render(
        request,
        "tasks/partials/task_card.html",
        {"task": task},
    )


def task_toggle(request, task_id):
    task = get_object_or_404(Task, pk=task_id)
    if task.completed:
        task.uncomplete()
    else:
        task.complete()
    return render(
        request,
        "tasks/partials/task_card.html",
        {"task": task},
    )


def task_collapse(request, task_id):
    task = get_object_or_404(
        Task.objects.select_related("task_list").prefetch_related(
            "subtasks", "attachments"
        ),
        pk=task_id,
    )
    return render(
        request,
        "tasks/partials/task_card.html",
        {"task": task},
    )


def task_delete(request, task_id):
    task = get_object_or_404(Task, pk=task_id)
    task.delete()
    return HttpResponse("")
