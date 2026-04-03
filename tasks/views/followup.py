from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render

from tasks.models import Task


def followup_form(request, task_id):
    task = get_object_or_404(Task, pk=task_id)
    return render(
        request,
        "tasks/partials/followup_form.html",
        {
            "task": task,
            "default_title": f"Follow-up: {task.title}",
        },
    )


def followup_create(request, task_id):
    task = get_object_or_404(Task, pk=task_id)
    title = request.POST.get("title", "").strip()
    start_date = request.POST.get("start_date") or None
    deadline = request.POST.get("deadline") or None
    if title:
        max_pos = Task.objects.filter(
            task_list=task.task_list, parent_task__isnull=True
        ).count()
        Task.objects.create(
            title=title,
            task_list=task.task_list,
            follow_up_from=task,
            start_date=start_date,
            deadline=deadline,
            position=max_pos,
        )
        return HttpResponse(
            '<p class="followup-chain" style="color: var(--success);">'
            "Follow-up scheduled!</p>"
        )
    return render(
        request,
        "tasks/partials/followup_form.html",
        {"task": task, "default_title": f"Follow-up: {task.title}"},
    )
