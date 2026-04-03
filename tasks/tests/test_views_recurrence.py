from datetime import date, timedelta

from django.test import RequestFactory, TestCase

from tasks.models import RecurrenceSeries, Task, TaskList
from tasks.views.recurrence import recurrence_form_view
from tasks.views.task_crud import task_create, task_update


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


class RecurrenceEditScopeTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.work = TaskList.objects.create(
            name="Work", colour="#4f46e5", position=0, column=0
        )
        self.series = RecurrenceSeries.objects.create(
            title="Daily standup",
            task_list=self.work,
            recurrence_type="daily",
            interval=1,
            start_date=date.today(),
            generation_horizon=date.today() + timedelta(days=90),
        )
        self.task1 = Task.objects.create(
            title="Daily standup",
            task_list=self.work,
            position=0,
            series=self.series,
            series_date=date.today(),
        )
        self.task2 = Task.objects.create(
            title="Daily standup",
            task_list=self.work,
            position=1,
            series=self.series,
            series_date=date.today() + timedelta(days=1),
        )
        self.task3 = Task.objects.create(
            title="Daily standup",
            task_list=self.work,
            position=2,
            series=self.series,
            series_date=date.today() + timedelta(days=2),
        )

    def test_edit_this_only_detaches(self):
        from tasks.views.recurrence import recurrence_edit_apply

        request = self.factory.post(
            f"/task/{self.task2.pk}/recurrence/edit-apply/",
            {"scope": "this", "field_title": "Changed title"},
        )
        recurrence_edit_apply(request, self.task2.pk)
        self.task2.refresh_from_db()
        self.assertTrue(self.task2.is_detached)
        self.assertEqual(self.task2.title, "Changed title")
        # Other tasks unchanged
        self.task1.refresh_from_db()
        self.assertEqual(self.task1.title, "Daily standup")

    def test_edit_all_updates_series_and_future_instances(self):
        from tasks.views.recurrence import recurrence_edit_apply

        request = self.factory.post(
            f"/task/{self.task1.pk}/recurrence/edit-apply/",
            {"scope": "all", "field_title": "New title"},
        )
        recurrence_edit_apply(request, self.task1.pk)
        self.series.refresh_from_db()
        self.assertEqual(self.series.title, "New title")
        self.task2.refresh_from_db()
        self.assertEqual(self.task2.title, "New title")

    def test_edit_following_splits_series(self):
        from tasks.views.recurrence import recurrence_edit_apply

        request = self.factory.post(
            f"/task/{self.task2.pk}/recurrence/edit-apply/",
            {"scope": "following", "field_title": "Split title"},
        )
        recurrence_edit_apply(request, self.task2.pk)
        self.series.refresh_from_db()
        # Original series should have end_date set
        self.assertIsNotNone(self.series.end_date)
        # task2 and task3 should be in a new series
        self.task2.refresh_from_db()
        self.assertNotEqual(self.task2.series, self.series)
        self.assertEqual(self.task2.title, "Split title")


class RecurrenceDeleteScopeTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.work = TaskList.objects.create(
            name="Work", colour="#4f46e5", position=0, column=0
        )
        self.series = RecurrenceSeries.objects.create(
            title="Daily standup",
            task_list=self.work,
            recurrence_type="daily",
            interval=1,
            start_date=date.today(),
            generation_horizon=date.today() + timedelta(days=90),
        )
        self.task1 = Task.objects.create(
            title="Daily standup",
            task_list=self.work,
            position=0,
            series=self.series,
            series_date=date.today(),
        )
        self.task2 = Task.objects.create(
            title="Daily standup",
            task_list=self.work,
            position=1,
            series=self.series,
            series_date=date.today() + timedelta(days=1),
        )

    def test_delete_this_only_skips(self):
        from tasks.views.recurrence import recurrence_delete_apply

        request = self.factory.post(
            f"/task/{self.task1.pk}/recurrence/delete-apply/",
            {"scope": "this"},
        )
        recurrence_delete_apply(request, self.task1.pk)
        self.task1.refresh_from_db()
        self.assertTrue(self.task1.is_skipped)
        # Other task still exists
        self.assertTrue(Task.objects.filter(pk=self.task2.pk).exists())

    def test_delete_all_removes_series_and_instances(self):
        from tasks.views.recurrence import recurrence_delete_apply

        request = self.factory.post(
            f"/task/{self.task1.pk}/recurrence/delete-apply/",
            {"scope": "all"},
        )
        recurrence_delete_apply(request, self.task1.pk)
        self.assertFalse(RecurrenceSeries.objects.filter(pk=self.series.pk).exists())
        self.assertFalse(Task.objects.filter(series=self.series).exists())

    def test_delete_following_sets_end_date_and_deletes_future(self):
        from tasks.views.recurrence import recurrence_delete_apply

        request = self.factory.post(
            f"/task/{self.task1.pk}/recurrence/delete-apply/",
            {"scope": "following"},
        )
        recurrence_delete_apply(request, self.task1.pk)
        self.task1.refresh_from_db()
        self.assertTrue(self.task1.is_skipped)
        self.series.refresh_from_db()
        self.assertIsNotNone(self.series.end_date)
        # task2 (future) should be deleted
        self.assertFalse(Task.objects.filter(pk=self.task2.pk).exists())


class TaskUpdateRecurrenceTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.work = TaskList.objects.create(
            name="Work", colour="#4f46e5", position=0, column=0
        )
        self.series = RecurrenceSeries.objects.create(
            title="Daily",
            task_list=self.work,
            recurrence_type="daily",
            interval=1,
            start_date=date.today(),
            generation_horizon=date.today(),
        )

    def test_update_recurring_returns_scope_modal(self):
        task = Task.objects.create(
            title="Daily",
            task_list=self.work,
            position=0,
            series=self.series,
            series_date=date.today(),
        )
        request = self.factory.post(f"/task/{task.pk}/update/", {"title": "Changed"})
        response = task_update(request, task.pk)
        content = response.content.decode()
        self.assertIn("recurring task", content.lower())

    def test_update_detached_task_saves_normally(self):
        task = Task.objects.create(
            title="Daily",
            task_list=self.work,
            position=0,
            series=self.series,
            series_date=date.today(),
            is_detached=True,
        )
        request = self.factory.post(
            f"/task/{task.pk}/update/",
            {"title": "Changed", "description": ""},
        )
        task_update(request, task.pk)
        task.refresh_from_db()
        self.assertEqual(task.title, "Changed")
