from datetime import date, timedelta
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from tasks.models import RecurrenceSeries, Task, TaskAttachment, TaskLink, TaskList


class TaskListModelTest(TestCase):
    def test_str_returns_name(self):
        task_list = TaskList(name="Work", colour="#4f46e5")
        self.assertEqual(str(task_list), "Work")

    def test_default_ordering_by_column_then_position(self):
        TaskList.objects.create(name="B", colour="#000000", position=1, column=1)
        TaskList.objects.create(name="A", colour="#000000", position=0, column=0)
        TaskList.objects.create(name="C", colour="#000000", position=0, column=1)
        names = list(TaskList.objects.values_list("name", flat=True))
        self.assertEqual(names, ["A", "C", "B"])


class TaskModelTest(TestCase):
    def setUp(self):
        self.task_list = TaskList.objects.create(
            name="Work", colour="#4f46e5", position=0, column=0
        )

    def test_str_returns_title(self):
        task = Task(title="Do something", task_list=self.task_list)
        self.assertEqual(str(task), "Do something")

    def test_is_overdue_when_deadline_past_and_not_completed(self):
        task = Task(
            title="Late",
            task_list=self.task_list,
            deadline=date.today() - timedelta(days=1),
        )
        self.assertTrue(task.is_overdue)

    def test_is_not_overdue_when_completed(self):
        task = Task(
            title="Done",
            task_list=self.task_list,
            deadline=date.today() - timedelta(days=1),
            completed=True,
        )
        self.assertFalse(task.is_overdue)

    def test_is_not_overdue_when_no_deadline(self):
        task = Task(title="Open", task_list=self.task_list)
        self.assertFalse(task.is_overdue)

    def test_is_visible_when_no_start_date(self):
        task = Task(title="Now", task_list=self.task_list)
        self.assertTrue(task.is_visible)

    def test_is_not_visible_when_start_date_in_future(self):
        task = Task(
            title="Later",
            task_list=self.task_list,
            start_date=date.today() + timedelta(days=5),
        )
        self.assertFalse(task.is_visible)

    def test_is_visible_when_start_date_today_or_past(self):
        task = Task(
            title="Now",
            task_list=self.task_list,
            start_date=date.today(),
        )
        self.assertTrue(task.is_visible)

    def test_complete_sets_completed_and_timestamp(self):
        task = Task.objects.create(title="Todo", task_list=self.task_list, position=0)
        now = timezone.now()
        with patch("django.utils.timezone.now", return_value=now):
            task.complete()
        task.refresh_from_db()
        self.assertTrue(task.completed)
        self.assertEqual(task.completed_at, now)

    def test_uncomplete_clears_completed_and_timestamp(self):
        task = Task.objects.create(
            title="Done",
            task_list=self.task_list,
            position=0,
            completed=True,
            completed_at=timezone.now(),
        )
        task.uncomplete()
        task.refresh_from_db()
        self.assertFalse(task.completed)
        self.assertIsNone(task.completed_at)

    def test_subtask_must_share_task_list_with_parent(self):
        other_list = TaskList.objects.create(
            name="Home", colour="#059669", position=1, column=1
        )
        parent = Task.objects.create(
            title="Parent", task_list=self.task_list, position=0
        )
        child = Task(
            title="Child", task_list=other_list, parent_task=parent, position=0
        )
        with self.assertRaises(ValidationError):
            child.full_clean()

    def test_active_tasks_queryset(self):
        Task.objects.create(title="Visible", task_list=self.task_list, position=0)
        Task.objects.create(
            title="Future",
            task_list=self.task_list,
            position=1,
            start_date=date.today() + timedelta(days=30),
        )
        Task.objects.create(
            title="Done",
            task_list=self.task_list,
            position=2,
            completed=True,
        )
        active = Task.objects.active()
        self.assertEqual(active.count(), 1)
        self.assertEqual(active.first().title, "Visible")

    def test_due_today_queryset(self):
        Task.objects.create(
            title="Due",
            task_list=self.task_list,
            position=0,
            deadline=date.today(),
        )
        Task.objects.create(
            title="Overdue",
            task_list=self.task_list,
            position=1,
            deadline=date.today() - timedelta(days=2),
        )
        Task.objects.create(
            title="Future",
            task_list=self.task_list,
            position=2,
            deadline=date.today() + timedelta(days=5),
        )
        due = Task.objects.due_today()
        self.assertEqual(due.count(), 2)

    def test_default_ordering_by_position(self):
        Task.objects.create(title="Second", task_list=self.task_list, position=1)
        Task.objects.create(title="First", task_list=self.task_list, position=0)
        titles = list(Task.objects.values_list("title", flat=True))
        self.assertEqual(titles, ["First", "Second"])


class RecurrenceSeriesModelTest(TestCase):
    def setUp(self):
        self.task_list = TaskList.objects.create(
            name="Work", colour="#4f46e5", position=0, column=0
        )

    def test_str_representation(self):
        series = RecurrenceSeries(
            title="Standup",
            task_list=self.task_list,
            recurrence_type="daily",
            interval=1,
            start_date=date.today(),
            generation_horizon=date.today(),
        )
        self.assertIn("Standup", str(series))
        self.assertIn("Daily", str(series))

    def test_create_series(self):
        series = RecurrenceSeries.objects.create(
            title="Weekly review",
            task_list=self.task_list,
            recurrence_type="weekly",
            interval=1,
            day_of_week=0,
            start_date=date.today(),
            generation_horizon=date.today(),
        )
        self.assertEqual(series.recurrence_type, "weekly")
        self.assertEqual(series.interval, 1)


class TaskRecurrenceFieldsTest(TestCase):
    def setUp(self):
        self.task_list = TaskList.objects.create(
            name="Work", colour="#4f46e5", position=0, column=0
        )
        self.series = RecurrenceSeries.objects.create(
            title="Daily standup",
            task_list=self.task_list,
            recurrence_type="daily",
            interval=1,
            start_date=date.today(),
            generation_horizon=date.today(),
        )

    def test_task_linked_to_series(self):
        task = Task.objects.create(
            title="Daily standup",
            task_list=self.task_list,
            series=self.series,
            series_date=date.today(),
            position=0,
        )
        self.assertEqual(task.series, self.series)
        self.assertEqual(task.series_date, date.today())

    def test_skipped_task_excluded_from_active(self):
        Task.objects.create(
            title="Skipped",
            task_list=self.task_list,
            series=self.series,
            series_date=date.today(),
            is_skipped=True,
            position=0,
        )
        Task.objects.create(
            title="Active",
            task_list=self.task_list,
            series=self.series,
            series_date=date.today() + timedelta(days=1),
            position=1,
        )
        active = Task.objects.active()
        self.assertEqual(active.count(), 1)
        self.assertEqual(active.first().title, "Active")

    def test_series_cascade_on_delete(self):
        task = Task.objects.create(
            title="Instance",
            task_list=self.task_list,
            series=self.series,
            series_date=date.today(),
            position=0,
        )
        # SET_NULL: deleting series should null the FK, not delete the task
        self.series.delete()
        task.refresh_from_db()
        self.assertIsNone(task.series)


class TaskAttachmentModelTest(TestCase):
    def test_str_returns_filename(self):
        attachment = TaskAttachment(filename="report.pdf")
        self.assertEqual(str(attachment), "report.pdf")


class TaskLinkModelTest(TestCase):
    def test_str_returns_label_when_set(self):
        link = TaskLink(url="https://example.com", label="Example")
        self.assertEqual(str(link), "Example")

    def test_str_returns_url_when_no_label(self):
        link = TaskLink(url="https://example.com", label="")
        self.assertEqual(str(link), "https://example.com")
