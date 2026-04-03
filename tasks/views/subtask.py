from django.shortcuts import get_object_or_404, render

from tasks.models import Task


def subtask_form(request, parent_id):
    parent = get_object_or_404(Task, pk=parent_id)
    return render(
        request,
        "tasks/partials/subtask_form.html",
        {"parent": parent},
    )


def subtask_create(request, parent_id):
    parent = get_object_or_404(Task, pk=parent_id)
    title = request.POST.get("title", "").strip()
    if title:
        max_pos = Task.objects.filter(parent_task=parent).count()
        subtask = Task.objects.create(
            title=title,
            task_list=parent.task_list,
            parent_task=parent,
            position=max_pos,
        )
        return render(
            request,
            "tasks/partials/subtask_item.html",
            {"task": subtask},
        )
    return render(
        request,
        "tasks/partials/subtask_form.html",
        {"parent": parent},
    )


def subtask_toggle(request, task_id):
    task = get_object_or_404(Task, pk=task_id)
    if task.completed:
        task.uncomplete()
    else:
        task.complete()
    return render(
        request,
        "tasks/partials/subtask_item.html",
        {"task": task},
    )
