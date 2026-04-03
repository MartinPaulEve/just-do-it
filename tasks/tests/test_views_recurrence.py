from datetime import date, timedelta

from django.test import RequestFactory, TestCase

from tasks.models import RecurrenceSeries, Task, TaskList
from tasks.views.recurrence import recurrence_form_view
from tasks.views.task_crud import task_create


class RecurrenceFormViewTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.work = TaskList.objects.create(
            name="Work", colour="#4f46e5", position=0, column=0
        )

    def test_returns_form(self):
        request = self.factory.get(f"/recurrence/form/{self.work.pk}/")
        response = recurrence_form_view(request, self.work.pk)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"recurrence_type", response.content)


class RecurringTaskCreateTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.work = TaskList.objects.create(
            name="Work", colour="#4f46e5", position=0, column=0
        )

    def test_creates_series_and_instances(self):
        request = self.factory.post(
            f"/task/create/{self.work.pk}/",
            data={
                "title": "Daily standup",
                "recurrence_type": "daily",
                "interval": "1",
            },
        )
        task_create(request, self.work.pk)
        self.assertEqual(RecurrenceSeries.objects.count(), 1)
        series = RecurrenceSeries.objects.first()
        self.assertEqual(series.title, "Daily standup")
        self.assertEqual(series.recurrence_type, "daily")
        # Should have generated instances for ~90 days
        self.assertGreater(Task.objects.filter(series=series).count(), 0)

    def test_non_recurring_task_unchanged(self):
        request = self.factory.post(
            f"/task/create/{self.work.pk}/",
            data={"title": "Normal task"},
        )
        task_create(request, self.work.pk)
        self.assertEqual(RecurrenceSeries.objects.count(), 0)
        self.assertEqual(Task.objects.filter(title="Normal task").count(), 1)

    def test_creates_series_with_deadline_offset(self):
        request = self.factory.post(
            f"/task/create/{self.work.pk}/",
            data={
                "title": "Weekly report",
                "recurrence_type": "weekly",
                "interval": "1",
                "day_of_week": "4",  # Friday
                "start_date": str(date.today()),
                "deadline": str(date.today() + timedelta(days=2)),
            },
        )
        task_create(request, self.work.pk)
        series = RecurrenceSeries.objects.first()
        self.assertEqual(series.deadline_offset, 2)
