from datetime import date, timedelta

from django.test import TestCase

from tasks.models import RecurrenceSeries
from tasks.templatetags.task_tags import deadline_class, deadline_display


class DeadlineClassTest(TestCase):
    def test_no_deadline_returns_normal(self):
        self.assertEqual(deadline_class(None), "task-card__badge--normal")

    def test_overdue_returns_overdue(self):
        self.assertEqual(
            deadline_class(date.today() - timedelta(days=1)),
            "task-card__badge--overdue",
        )

    def test_today_returns_overdue(self):
        self.assertEqual(deadline_class(date.today()), "task-card__badge--overdue")

    def test_within_3_days_returns_soon(self):
        self.assertEqual(
            deadline_class(date.today() + timedelta(days=2)),
            "task-card__badge--soon",
        )

    def test_far_future_returns_normal(self):
        self.assertEqual(
            deadline_class(date.today() + timedelta(days=10)),
            "task-card__badge--normal",
        )


class DeadlineDisplayTest(TestCase):
    def test_no_deadline(self):
        self.assertEqual(deadline_display(None), "No deadline")

    def test_today(self):
        self.assertEqual(deadline_display(date.today()), "Due today")

    def test_past_date(self):
        result = deadline_display(date.today() - timedelta(days=3))
        self.assertIn("Overdue", result)

    def test_future_date(self):
        future = date.today() + timedelta(days=5)
        result = deadline_display(future)
        self.assertIn("Due", result)


class RecurrenceDisplayTest(TestCase):
    def test_daily(self):
        series = RecurrenceSeries(recurrence_type="daily", interval=1)
        from tasks.templatetags.task_tags import recurrence_display

        self.assertEqual(recurrence_display(series), "Every day")

    def test_weekly_with_day(self):
        series = RecurrenceSeries(recurrence_type="weekly", interval=1, day_of_week=0)
        from tasks.templatetags.task_tags import recurrence_display

        self.assertEqual(recurrence_display(series), "Every week on Monday")

    def test_monthly_interval(self):
        series = RecurrenceSeries(
            recurrence_type="monthly", interval=2, day_of_month=15
        )
        from tasks.templatetags.task_tags import recurrence_display

        self.assertEqual(recurrence_display(series), "Every 2 months on day 15")

    def test_none_returns_empty(self):
        from tasks.templatetags.task_tags import recurrence_display

        self.assertEqual(recurrence_display(None), "")
