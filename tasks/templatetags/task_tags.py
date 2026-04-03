from datetime import date, timedelta

from django import template

register = template.Library()


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
