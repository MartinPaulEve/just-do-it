from datetime import date, timedelta

from django.test import TestCase

from tasks.models import RecurrenceSeries, Task, TaskList
from tasks.recurrence import (
    calculate_occurrences,
    ensure_series_generated,
    generate_instances,
)


def make_series(task_list, recurrence_type="daily", interval=1, **kwargs):
    """Helper to create a RecurrenceSeries with sensible defaults."""
    defaults = {
        "title": "Test Task",
        "description": "",
        "task_list": task_list,
        "recurrence_type": recurrence_type,
        "interval": interval,
        "start_date": date(2025, 1, 1),
        "generation_horizon": date(2024, 12, 31),
    }
    defaults.update(kwargs)
    return RecurrenceSeries.objects.create(**defaults)


class CalculateOccurrencesTest(TestCase):
    def setUp(self):
        self.task_list = TaskList.objects.create(
            name="Work", colour="#4f46e5", position=0, column=0
        )

    def test_daily_every_day(self):
        series = make_series(
            self.task_list,
            recurrence_type="daily",
            interval=1,
            start_date=date(2025, 1, 1),
        )
        result = calculate_occurrences(series, date(2025, 1, 1), date(2025, 1, 5))
        self.assertEqual(
            result,
            [
                date(2025, 1, 1),
                date(2025, 1, 2),
                date(2025, 1, 3),
                date(2025, 1, 4),
                date(2025, 1, 5),
            ],
        )

    def test_daily_every_3_days(self):
        series = make_series(
            self.task_list,
            recurrence_type="daily",
            interval=3,
            start_date=date(2025, 1, 1),
        )
        result = calculate_occurrences(series, date(2025, 1, 1), date(2025, 1, 14))
        self.assertEqual(
            result,
            [
                date(2025, 1, 1),
                date(2025, 1, 4),
                date(2025, 1, 7),
                date(2025, 1, 10),
                date(2025, 1, 13),
            ],
        )

    def test_weekly_every_week(self):
        # Start on Wednesday 2025-01-01, day_of_week=2 (Wed)
        series = make_series(
            self.task_list,
            recurrence_type="weekly",
            interval=1,
            start_date=date(2025, 1, 1),
            day_of_week=2,
        )
        result = calculate_occurrences(series, date(2025, 1, 1), date(2025, 1, 22))
        self.assertEqual(
            result,
            [date(2025, 1, 1), date(2025, 1, 8), date(2025, 1, 15), date(2025, 1, 22)],
        )

    def test_weekly_every_2_weeks(self):
        series = make_series(
            self.task_list,
            recurrence_type="weekly",
            interval=2,
            start_date=date(2025, 1, 1),
            day_of_week=2,
        )
        result = calculate_occurrences(series, date(2025, 1, 1), date(2025, 1, 29))
        self.assertEqual(
            result,
            [date(2025, 1, 1), date(2025, 1, 15), date(2025, 1, 29)],
        )

    def test_monthly_every_month(self):
        series = make_series(
            self.task_list,
            recurrence_type="monthly",
            interval=1,
            start_date=date(2025, 1, 15),
            day_of_month=15,
        )
        result = calculate_occurrences(series, date(2025, 1, 15), date(2025, 4, 15))
        self.assertEqual(
            result,
            [
                date(2025, 1, 15),
                date(2025, 2, 15),
                date(2025, 3, 15),
                date(2025, 4, 15),
            ],
        )

    def test_monthly_31st_clamps_to_shorter_months(self):
        series = make_series(
            self.task_list,
            recurrence_type="monthly",
            interval=1,
            start_date=date(2025, 1, 31),
            day_of_month=31,
        )
        result = calculate_occurrences(series, date(2025, 1, 31), date(2025, 4, 30))
        self.assertEqual(
            result,
            [
                date(2025, 1, 31),
                date(2025, 2, 28),  # Feb clamped
                date(2025, 3, 31),
                date(2025, 4, 30),  # April has 30 days
            ],
        )

    def test_yearly_every_year(self):
        series = make_series(
            self.task_list,
            recurrence_type="yearly",
            interval=1,
            start_date=date(2025, 3, 10),
            month_of_year=3,
            day_of_month=10,
        )
        result = calculate_occurrences(series, date(2025, 3, 10), date(2027, 3, 10))
        self.assertEqual(
            result,
            [date(2025, 3, 10), date(2026, 3, 10), date(2027, 3, 10)],
        )

    def test_yearly_leap_day(self):
        # Feb 29 in a leap year; non-leap years should clamp to Feb 28
        series = make_series(
            self.task_list,
            recurrence_type="yearly",
            interval=1,
            start_date=date(2024, 2, 29),
            month_of_year=2,
            day_of_month=29,
        )
        result = calculate_occurrences(series, date(2024, 2, 29), date(2026, 3, 1))
        self.assertEqual(
            result,
            [date(2024, 2, 29), date(2025, 2, 28), date(2026, 2, 28)],
        )

    def test_respects_end_date(self):
        series = make_series(
            self.task_list,
            recurrence_type="daily",
            interval=1,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 3),
        )
        result = calculate_occurrences(series, date(2025, 1, 1), date(2025, 1, 10))
        self.assertEqual(
            result,
            [date(2025, 1, 1), date(2025, 1, 2), date(2025, 1, 3)],
        )

    def test_respects_max_occurrences(self):
        series = make_series(
            self.task_list,
            recurrence_type="daily",
            interval=1,
            start_date=date(2025, 1, 1),
            max_occurrences=3,
        )
        result = calculate_occurrences(series, date(2025, 1, 1), date(2025, 1, 10))
        self.assertEqual(
            result,
            [date(2025, 1, 1), date(2025, 1, 2), date(2025, 1, 3)],
        )

    def test_max_occurrences_counts_from_start_not_from_date(self):
        """max_occurrences counts total from start_date, so from_date offset matters."""
        series = make_series(
            self.task_list,
            recurrence_type="daily",
            interval=1,
            start_date=date(2025, 1, 1),
            max_occurrences=5,
        )
        # From date is partway through; only dates 3,4,5 fall in range
        result = calculate_occurrences(series, date(2025, 1, 3), date(2025, 1, 10))
        self.assertEqual(
            result,
            [date(2025, 1, 3), date(2025, 1, 4), date(2025, 1, 5)],
        )

    def test_empty_when_from_after_end_date(self):
        series = make_series(
            self.task_list,
            recurrence_type="daily",
            interval=1,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 5),
        )
        result = calculate_occurrences(series, date(2025, 1, 10), date(2025, 1, 20))
        self.assertEqual(result, [])

    def test_weekly_from_date_after_start_finds_next_occurrence(self):
        """Weekly occurrences fall on the correct weekday even when from_date is
        after start_date."""
        # Start Monday 2025-01-06; day_of_week=0 (Mon); from_date=2025-01-13
        series = make_series(
            self.task_list,
            recurrence_type="weekly",
            interval=1,
            start_date=date(2025, 1, 6),
            day_of_week=0,
        )
        result = calculate_occurrences(series, date(2025, 1, 13), date(2025, 1, 20))
        self.assertEqual(result, [date(2025, 1, 13), date(2025, 1, 20)])


class GenerateInstancesTest(TestCase):
    def setUp(self):
        self.task_list = TaskList.objects.create(
            name="Work", colour="#4f46e5", position=0, column=0
        )

    def _make_series(self, **kwargs):
        return make_series(self.task_list, **kwargs)

    def test_generates_daily_instances(self):
        series = self._make_series(
            recurrence_type="daily",
            interval=1,
            start_date=date(2025, 1, 1),
            generation_horizon=date(2024, 12, 31),
        )
        created = generate_instances(series, date(2025, 1, 3))
        self.assertEqual(len(created), 3)
        dates = [t.series_date for t in created]
        self.assertEqual(
            dates,
            [date(2025, 1, 1), date(2025, 1, 2), date(2025, 1, 3)],
        )

    def test_idempotent_no_duplicates(self):
        series = self._make_series(
            recurrence_type="daily",
            interval=1,
            start_date=date(2025, 1, 1),
            generation_horizon=date(2024, 12, 31),
        )
        generate_instances(series, date(2025, 1, 3))
        # Call again for an overlapping range; horizon is now 2025-01-03,
        # so this call only covers 2025-01-04..2025-01-05
        series.refresh_from_db()
        created2 = generate_instances(series, date(2025, 1, 5))
        total = Task.objects.filter(series=series).count()
        self.assertEqual(total, 5)
        self.assertEqual(len(created2), 2)

    def test_skips_existing_skipped_dates(self):
        """If a task for a date exists and is_skipped=True, do not create another."""
        series = self._make_series(
            recurrence_type="daily",
            interval=1,
            start_date=date(2025, 1, 1),
            generation_horizon=date(2024, 12, 31),
        )
        # Pre-create a skipped task for Jan 2
        Task.objects.create(
            title="Test Task",
            task_list=self.task_list,
            series=series,
            series_date=date(2025, 1, 2),
            is_skipped=True,
            position=0,
        )
        created = generate_instances(series, date(2025, 1, 3))
        dates = [t.series_date for t in created]
        # Jan 2 already exists (skipped), so only Jan 1 and Jan 3 should be created
        self.assertIn(date(2025, 1, 1), dates)
        self.assertNotIn(date(2025, 1, 2), dates)
        self.assertIn(date(2025, 1, 3), dates)

    def test_does_not_overwrite_detached(self):
        """Detached tasks for a date should not be replaced."""
        series = self._make_series(
            recurrence_type="daily",
            interval=1,
            start_date=date(2025, 1, 1),
            generation_horizon=date(2024, 12, 31),
        )
        Task.objects.create(
            title="Custom title",
            task_list=self.task_list,
            series=series,
            series_date=date(2025, 1, 1),
            is_detached=True,
            position=0,
        )
        generate_instances(series, date(2025, 1, 3))
        # Should still only have one task for Jan 1
        jan1_tasks = Task.objects.filter(series=series, series_date=date(2025, 1, 1))
        self.assertEqual(jan1_tasks.count(), 1)
        self.assertEqual(jan1_tasks.first().title, "Custom title")

    def test_sets_deadline_with_offset(self):
        series = self._make_series(
            recurrence_type="daily",
            interval=1,
            start_date=date(2025, 1, 1),
            generation_horizon=date(2024, 12, 31),
            deadline_offset=3,
        )
        created = generate_instances(series, date(2025, 1, 1))
        self.assertEqual(len(created), 1)
        self.assertEqual(created[0].deadline, date(2025, 1, 4))

    def test_no_deadline_when_offset_is_none(self):
        series = self._make_series(
            recurrence_type="daily",
            interval=1,
            start_date=date(2025, 1, 1),
            generation_horizon=date(2024, 12, 31),
            deadline_offset=None,
        )
        created = generate_instances(series, date(2025, 1, 1))
        self.assertEqual(len(created), 1)
        self.assertIsNone(created[0].deadline)

    def test_updates_generation_horizon(self):
        series = self._make_series(
            recurrence_type="daily",
            interval=1,
            start_date=date(2025, 1, 1),
            generation_horizon=date(2024, 12, 31),
        )
        generate_instances(series, date(2025, 1, 5))
        series.refresh_from_db()
        self.assertEqual(series.generation_horizon, date(2025, 1, 5))

    def test_returns_empty_when_horizon_already_covers_date(self):
        series = self._make_series(
            recurrence_type="daily",
            interval=1,
            start_date=date(2025, 1, 1),
            generation_horizon=date(2025, 1, 10),
        )
        created = generate_instances(series, date(2025, 1, 5))
        self.assertEqual(created, [])


class EnsureSeriesGeneratedTest(TestCase):
    def setUp(self):
        self.task_list = TaskList.objects.create(
            name="Work", colour="#4f46e5", position=0, column=0
        )

    def _make_series(self, **kwargs):
        return make_series(self.task_list, **kwargs)

    def test_generates_for_series_needing_update(self):
        """Series behind the target horizon should have instances generated."""
        series = self._make_series(
            recurrence_type="daily",
            interval=1,
            start_date=date.today(),
            generation_horizon=date.today() - timedelta(days=1),
        )
        ensure_series_generated(horizon_days=7)
        series.refresh_from_db()
        self.assertGreaterEqual(
            series.generation_horizon, date.today() + timedelta(days=7)
        )

    def test_skips_series_already_generated(self):
        """Series already generated beyond the target should not be touched."""
        future = date.today() + timedelta(days=180)
        series = self._make_series(
            recurrence_type="daily",
            interval=1,
            start_date=date.today(),
            generation_horizon=future,
        )
        ensure_series_generated(horizon_days=7)
        series.refresh_from_db()
        # Horizon should not have moved (it was already ahead)
        self.assertEqual(series.generation_horizon, future)

    def test_skips_ended_series(self):
        """Series whose end_date is in the past should be excluded."""
        series = self._make_series(
            recurrence_type="daily",
            interval=1,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            generation_horizon=date(2024, 1, 31),
        )
        ensure_series_generated(horizon_days=7)
        series.refresh_from_db()
        # Horizon should remain unchanged since end_date < today
        self.assertEqual(series.generation_horizon, date(2024, 1, 31))
