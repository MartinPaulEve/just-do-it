from django.test import TestCase

from tasks.forms import TaskForm, TaskLinkForm, TaskListForm
from tasks.models import TaskList


class TaskListFormTest(TestCase):
    def test_valid_form(self):
        form = TaskListForm(data={"name": "Work", "colour": "#4f46e5"})
        self.assertTrue(form.is_valid())

    def test_name_required(self):
        form = TaskListForm(data={"name": "", "colour": "#4f46e5"})
        self.assertFalse(form.is_valid())
        self.assertIn("name", form.errors)


class TaskFormTest(TestCase):
    def setUp(self):
        self.task_list = TaskList.objects.create(
            name="Work", colour="#4f46e5", position=0, column=0
        )

    def test_valid_form_minimal(self):
        form = TaskForm(data={"title": "Do something"})
        self.assertTrue(form.is_valid())

    def test_title_required(self):
        form = TaskForm(data={"title": ""})
        self.assertFalse(form.is_valid())
        self.assertIn("title", form.errors)

    def test_valid_form_with_dates(self):
        form = TaskForm(
            data={
                "title": "Do something",
                "start_date": "2026-04-01",
                "deadline": "2026-04-10",
            }
        )
        self.assertTrue(form.is_valid())


class TaskLinkFormTest(TestCase):
    def test_valid_form(self):
        form = TaskLinkForm(data={"url": "https://example.com", "label": "Example"})
        self.assertTrue(form.is_valid())

    def test_url_required(self):
        form = TaskLinkForm(data={"url": "", "label": "Example"})
        self.assertFalse(form.is_valid())

    def test_label_optional(self):
        form = TaskLinkForm(data={"url": "https://example.com", "label": ""})
        self.assertTrue(form.is_valid())
