from datetime import date, timedelta

from django import template

register = template.Library()


@register.filter
def recurrence_display(series):
    """Return human-readable recurrence description."""
    if not series:
        return ""
    type_labels = {
        "daily": "day",
        "weekly": "week",
        "monthly": "month",
        "yearly": "year",
    }
    unit = type_labels.get(series.recurrence_type, series.recurrence_type)
    if series.interval == 1:
        base = f"Every {unit}"
    else:
        base = f"Every {series.interval} {unit}s"

    if series.recurrence_type == "weekly" and series.day_of_week is not None:
        days = [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ]
        base += f" on {days[series.day_of_week]}"
    elif series.recurrence_type == "monthly" and series.day_of_month is not None:
        base += f" on day {series.day_of_month}"

    return base


@register.filter
def deadline_class(deadline_date):
    if not deadline_date:
        return "task-card__badge--normal"
    today = date.today()
    if deadline_date <= today:
        return "task-card__badge--overdue"
    if deadline_date <= today + timedelta(days=3):
        return "task-card__badge--soon"
    return "task-card__badge--normal"


@register.filter
def deadline_display(deadline_date):
    if not deadline_date:
        return "No deadline"
    today = date.today()
    if deadline_date == today:
        return "Due today"
    if deadline_date < today:
        days = (today - deadline_date).days
        return f"Overdue by {days}d"
    return f"Due {deadline_date.strftime('%b %-d')}"
