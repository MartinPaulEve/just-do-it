from django import forms

from tasks.models import RecurrenceSeries, Task, TaskLink, TaskList


class TaskListForm(forms.ModelForm):
    class Meta:
        model = TaskList
        fields = ["name", "colour", "icon"]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "inline-form__input",
                    "placeholder": "List name",
                    "autofocus": True,
                }
            ),
            "colour": forms.TextInput(
                attrs={"type": "color", "class": "inline-form__input"}
            ),
            "icon": forms.TextInput(
                attrs={
                    "class": "inline-form__input",
                    "placeholder": "Icon (emoji or name)",
                }
            ),
        }


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ["title", "description", "start_date", "deadline"]
        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": "inline-form__input",
                    "placeholder": "Task title",
                    "autofocus": True,
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "inline-form__input",
                    "placeholder": "Description (optional)",
                    "rows": 2,
                }
            ),
            "start_date": forms.DateInput(
                attrs={"type": "date", "class": "inline-form__input"}
            ),
            "deadline": forms.DateInput(
                attrs={"type": "date", "class": "inline-form__input"}
            ),
        }


class RecurrenceForm(forms.ModelForm):
    class Meta:
        model = RecurrenceSeries
        fields = [
            "recurrence_type",
            "interval",
            "day_of_week",
            "day_of_month",
            "end_date",
        ]
        widgets = {
            "recurrence_type": forms.Select(attrs={"class": "inline-form__input"}),
            "interval": forms.NumberInput(
                attrs={
                    "class": "inline-form__input",
                    "min": 1,
                    "value": 1,
                    "style": "width: 60px;",
                }
            ),
            "day_of_week": forms.Select(
                choices=[(None, "---")]
                + [
                    (i, name)
                    for i, name in enumerate(
                        [
                            "Monday",
                            "Tuesday",
                            "Wednesday",
                            "Thursday",
                            "Friday",
                            "Saturday",
                            "Sunday",
                        ]
                    )
                ],
                attrs={"class": "inline-form__input"},
            ),
            "day_of_month": forms.NumberInput(
                attrs={
                    "class": "inline-form__input",
                    "min": 1,
                    "max": 31,
                    "style": "width: 60px;",
                }
            ),
            "end_date": forms.DateInput(
                attrs={"type": "date", "class": "inline-form__input"}
            ),
        }


class TaskLinkForm(forms.ModelForm):
    class Meta:
        model = TaskLink
        fields = ["url", "label"]
        widgets = {
            "url": forms.URLInput(
                attrs={
                    "class": "inline-form__input",
                    "placeholder": "https://...",
                }
            ),
            "label": forms.TextInput(
                attrs={
                    "class": "inline-form__input",
                    "placeholder": "Label (optional)",
                }
            ),
        }
