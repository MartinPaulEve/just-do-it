from django.contrib import admin

from tasks.models import RecurrenceSeries, Task, TaskAttachment, TaskLink, TaskList


@admin.register(RecurrenceSeries)
class RecurrenceSeriesAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "task_list",
        "recurrence_type",
        "interval",
        "start_date",
        "end_date",
    ]
    list_filter = ["recurrence_type", "task_list"]


class TaskInline(admin.TabularInline):
    model = Task
    extra = 0
    fields = ["title", "position", "deadline", "completed"]


@admin.register(TaskList)
class TaskListAdmin(admin.ModelAdmin):
    list_display = ["name", "colour", "column", "position"]
    list_editable = ["column", "position"]
    inlines = [TaskInline]


class TaskAttachmentInline(admin.TabularInline):
    model = TaskAttachment
    extra = 0


class TaskLinkInline(admin.TabularInline):
    model = TaskLink
    extra = 0


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ["title", "task_list", "deadline", "completed", "position"]
    list_filter = ["task_list", "completed"]
    inlines = [TaskAttachmentInline, TaskLinkInline]
