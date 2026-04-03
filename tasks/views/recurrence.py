from django.shortcuts import get_object_or_404, render

from tasks.forms import RecurrenceForm
from tasks.models import TaskList


def recurrence_form_view(request, list_id):
    get_object_or_404(TaskList, pk=list_id)
    form = RecurrenceForm()
    return render(
        request,
        "tasks/partials/recurrence_form_partial.html",
        {"recurrence_form": form},
    )
