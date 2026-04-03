from datetime import date, timedelta

from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render

from tasks.forms import RecurrenceForm
from tasks.models import RecurrenceSeries, Task, TaskList


def recurrence_form_view(request, list_id):
    get_object_or_404(TaskList, pk=list_id)
    form = RecurrenceForm()
    return render(
        request,
        "tasks/partials/recurrence_form_partial.html",
        {"recurrence_form": form},
    )


def recurrence_edit_scope(request, task_id):
    """Return the scope modal for editing a recurring task."""
    task = get_object_or_404(Task, pk=task_id)
    form_data = {k: v for k, v in request.POST.items() if k != "csrfmiddlewaretoken"}
    return render(
        request,
        "tasks/partials/recurrence_scope_modal.html",
        {"task": task, "action": "edit", "form_data": form_data},
    )


def recurrence_edit_apply(request, task_id):
    """Apply an edit to a recurring task with the given scope."""
    task = get_object_or_404(Task.objects.select_related("series"), pk=task_id)
    scope = request.POST.get("scope")
    series = task.series

    # Extract original form data (prefixed with field_)
    field_data = {}
    for key, value in request.POST.items():
        if key.startswith("field_"):
            field_data[key[6:]] = value  # strip "field_" prefix

    if scope == "this":
        # Detach and edit this task only
        task.is_detached = True
        if "title" in field_data:
            task.title = field_data["title"]
        if "description" in field_data:
            task.description = field_data["description"]
        if "start_date" in field_data:
            task.start_date = field_data["start_date"] or None
        if "deadline" in field_data:
            task.deadline = field_data["deadline"] or None
        task.save()

    elif scope == "following":
        # Split series: create new series from this date
        new_series = RecurrenceSeries.objects.create(
            title=field_data.get("title", series.title) or series.title,
            description=field_data.get("description", series.description),
            task_list=series.task_list,
            recurrence_type=series.recurrence_type,
            interval=series.interval,
            day_of_week=series.day_of_week,
            day_of_month=series.day_of_month,
            month_of_year=series.month_of_year,
            start_date=task.series_date,
            end_date=series.end_date,
            max_occurrences=series.max_occurrences,
            deadline_offset=series.deadline_offset,
            generation_horizon=series.generation_horizon,
        )
        # Move this and future non-detached, non-completed instances to new series
        Task.objects.filter(
            series=series,
            series_date__gte=task.series_date,
            is_detached=False,
            completed=False,
        ).update(series=new_series)

        # Update moved instances with new field values
        update_fields = {}
        if field_data.get("title"):
            update_fields["title"] = field_data["title"]
            new_series.title = field_data["title"]
            new_series.save(update_fields=["title"])
        if "description" in field_data:
            update_fields["description"] = field_data["description"]
            new_series.description = field_data["description"]
            new_series.save(update_fields=["description"])
        if update_fields:
            Task.objects.filter(
                series=new_series,
                is_detached=False,
                completed=False,
            ).update(**update_fields)

        # End the original series just before this date
        series.end_date = task.series_date - timedelta(days=1)
        series.save(update_fields=["end_date"])

        task.refresh_from_db()

    elif scope == "all":
        # Update series template and all non-detached future instances
        if field_data.get("title"):
            series.title = field_data["title"]
        if "description" in field_data:
            series.description = field_data["description"]
        series.save()

        update_fields = {}
        if field_data.get("title"):
            update_fields["title"] = field_data["title"]
        if "description" in field_data:
            update_fields["description"] = field_data["description"]
        if update_fields:
            Task.objects.filter(
                series=series,
                is_detached=False,
                completed=False,
                series_date__gte=date.today(),
            ).update(**update_fields)

        task.refresh_from_db()

    return render(request, "tasks/partials/task_card.html", {"task": task})


def recurrence_delete_scope(request, task_id):
    """Return the scope modal for deleting a recurring task."""
    task = get_object_or_404(Task, pk=task_id)
    return render(
        request,
        "tasks/partials/recurrence_scope_modal.html",
        {"task": task, "action": "delete", "form_data": {}},
    )


def recurrence_delete_apply(request, task_id):
    """Delete a recurring task with the given scope."""
    task = get_object_or_404(Task.objects.select_related("series"), pk=task_id)
    scope = request.POST.get("scope")
    series = task.series

    if scope == "this":
        task.is_skipped = True
        task.save(update_fields=["is_skipped"])
        return HttpResponse("")

    elif scope == "following":
        # Skip this task
        task.is_skipped = True
        task.save(update_fields=["is_skipped"])
        # Set series end date
        series.end_date = task.series_date - timedelta(days=1)
        series.save(update_fields=["end_date"])
        # Delete future non-completed instances
        Task.objects.filter(
            series=series,
            series_date__gt=task.series_date,
            completed=False,
        ).delete()
        return HttpResponse("")

    elif scope == "all":
        # Our FK is SET_NULL, so delete instances first then the series
        Task.objects.filter(series=series).delete()
        series.delete()
        return HttpResponse("")

    return HttpResponse("")
