import calendar
from datetime import date, timedelta

from dateutil.relativedelta import relativedelta
from django.db import models


def calculate_occurrences(series, from_date, to_date):
    """Calculate all occurrence dates for a series between from_date and to_date.

    Both endpoints are inclusive. Returns a list of date objects.
    """
    recurrence_type = series.recurrence_type
    interval = series.interval
    start_date = series.start_date
    end_date = series.end_date
    max_occurrences = series.max_occurrences

    # Effective upper bound
    effective_end = to_date
    if end_date is not None:
        effective_end = min(effective_end, end_date)

    if from_date > effective_end:
        return []

    results = []

    if recurrence_type == "daily":
        current = start_date
        total = 0
        while current <= effective_end:
            if max_occurrences is not None and total >= max_occurrences:
                break
            if current >= from_date:
                results.append(current)
            current += timedelta(days=interval)
            total += 1

    elif recurrence_type == "weekly":
        target_weekday = series.day_of_week
        if target_weekday is None:
            target_weekday = start_date.weekday()

        # Find the first occurrence on or after start_date with the target weekday
        days_ahead = (target_weekday - start_date.weekday()) % 7
        first_occurrence = start_date + timedelta(days=days_ahead)

        step = timedelta(weeks=interval)
        current = first_occurrence
        total = 0
        while current <= effective_end:
            if max_occurrences is not None and total >= max_occurrences:
                break
            if current >= from_date:
                results.append(current)
            current += step
            total += 1

    elif recurrence_type == "monthly":
        target_day = series.day_of_month
        if target_day is None:
            target_day = start_date.day

        # Start from the month of start_date
        current_year = start_date.year
        current_month = start_date.month
        total = 0

        while True:
            # Clamp day to the last day of the month
            max_day = calendar.monthrange(current_year, current_month)[1]
            actual_day = min(target_day, max_day)
            current = date(current_year, current_month, actual_day)

            if current > effective_end:
                break
            if max_occurrences is not None and total >= max_occurrences:
                break

            if current >= from_date:
                results.append(current)

            total += 1
            # Advance by interval months
            next_date = date(current_year, current_month, 1) + relativedelta(
                months=interval
            )
            current_year = next_date.year
            current_month = next_date.month

    elif recurrence_type == "yearly":
        target_month = series.month_of_year
        if target_month is None:
            target_month = start_date.month

        target_day = series.day_of_month
        if target_day is None:
            target_day = start_date.day

        current_year = start_date.year
        total = 0

        while True:
            # Handle Feb 29 on non-leap years
            max_day = calendar.monthrange(current_year, target_month)[1]
            actual_day = min(target_day, max_day)
            current = date(current_year, target_month, actual_day)

            if current > effective_end:
                break
            if max_occurrences is not None and total >= max_occurrences:
                break

            if current >= from_date:
                results.append(current)

            total += 1
            current_year += interval

    return results


def generate_instances(series, up_to_date):
    """Generate Task instances for a RecurrenceSeries up to the given date.

    - Only generates for dates between series.generation_horizon and up_to_date
    - Skips dates where a Task already exists (idempotent)
    - Skips dates where an existing Task has is_skipped=True
    - Does NOT overwrite detached instances
    - Sets start_date = occurrence_date, deadline = occurrence_date + deadline_offset
      (if deadline_offset is set)
    - Updates series.generation_horizon to up_to_date
    """
    from tasks.models import Task

    from_date = series.generation_horizon + timedelta(days=1)
    if from_date > up_to_date:
        return []

    occurrences = calculate_occurrences(series, from_date, up_to_date)

    # Get existing instance dates for this series to avoid duplicates
    existing_dates = set(
        Task.objects.filter(series=series).values_list("series_date", flat=True)
    )

    created = []
    # Calculate next position
    max_pos = Task.objects.filter(
        task_list=series.task_list, parent_task__isnull=True
    ).count()

    for i, occ_date in enumerate(occurrences):
        if occ_date in existing_dates:
            continue

        deadline = None
        if series.deadline_offset is not None:
            deadline = occ_date + timedelta(days=series.deadline_offset)

        task = Task.objects.create(
            title=series.title,
            description=series.description,
            task_list=series.task_list,
            series=series,
            series_date=occ_date,
            start_date=occ_date,
            deadline=deadline,
            position=max_pos + i,
        )
        created.append(task)

    series.generation_horizon = up_to_date
    series.save(update_fields=["generation_horizon"])

    return created


def ensure_series_generated(horizon_days=90):
    """Ensure all active RecurrenceSeries have instances generated up to horizon.

    Only processes series where generation_horizon < today + horizon_days.
    """
    from tasks.models import RecurrenceSeries

    target_date = date.today() + timedelta(days=horizon_days)
    series_to_update = RecurrenceSeries.objects.filter(
        generation_horizon__lt=target_date,
    )
    # Exclude series that have ended (end_date in the past)
    series_to_update = series_to_update.filter(
        models.Q(end_date__isnull=True) | models.Q(end_date__gte=date.today())
    )

    for series in series_to_update:
        generate_instances(series, target_date)
