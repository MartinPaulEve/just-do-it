from datetime import date

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class TaskList(models.Model):
    name = models.CharField(max_length=100)
    colour = models.CharField(max_length=7, default="#6366f1")
    icon = models.CharField(max_length=50, blank=True)
    position = models.PositiveIntegerField(default=0)
    column = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["column", "position"]

    def __str__(self):
        return self.name

    @property
    def active_tasks(self):
        return self.tasks.filter(parent_task__isnull=True).active()


class TaskQuerySet(models.QuerySet):
    def active(self):
        return self.filter(
            completed=False,
        ).exclude(
            start_date__gt=date.today(),
        )

    def due_today(self):
        return self.active().filter(
            deadline__lte=date.today(),
        )


class Task(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    task_list = models.ForeignKey(
        TaskList, on_delete=models.CASCADE, related_name="tasks"
    )
    parent_task = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="subtasks",
    )
    start_date = models.DateField(null=True, blank=True)
    deadline = models.DateField(null=True, blank=True)
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    follow_up_from = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="follow_ups",
    )
    position = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = TaskQuerySet.as_manager()

    class Meta:
        ordering = ["position"]

    def __str__(self):
        return self.title

    @property
    def is_overdue(self):
        if self.completed or not self.deadline:
            return False
        return self.deadline < date.today()

    @property
    def is_visible(self):
        if not self.start_date:
            return True
        return self.start_date <= date.today()

    def complete(self):
        self.completed = True
        self.completed_at = timezone.now()
        self.save(update_fields=["completed", "completed_at"])

    def uncomplete(self):
        self.completed = False
        self.completed_at = None
        self.save(update_fields=["completed", "completed_at"])

    def clean(self):
        if self.parent_task and self.parent_task.task_list_id != self.task_list_id:
            raise ValidationError(
                "Sub-task must belong to the same task list as its parent."
            )


class TaskAttachment(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="attachments")
    file = models.FileField(upload_to="attachments/%Y/%m/")
    filename = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.filename


class TaskLink(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="links")
    url = models.URLField()
    label = models.CharField(max_length=255, blank=True)
    position = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["position"]

    def __str__(self):
        return self.label or self.url
