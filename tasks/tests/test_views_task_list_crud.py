from django.test import RequestFactory, TestCase

from tasks.models import TaskList
from tasks.views.task_list_crud import (
    task_list_create,
    task_list_delete,
    task_list_form,
    task_list_update,
)


class TaskListFormViewTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_returns_create_form(self):
        request = self.factory.get("/lists/form/")
        response = task_list_form(request)
        self.assertEqual(response.status_code, 200)

    def test_returns_edit_form_for_existing(self):
        tl = TaskList.objects.create(
            name="Work", colour="#4f46e5", position=0, column=0
        )
        request = self.factory.get(f"/lists/form/{tl.pk}/")
        response = task_list_form(request, tl.pk)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Work", response.content)


class TaskListCreateTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_creates_task_list(self):
        request = self.factory.post(
            "/lists/create/",
            data={"name": "Medical", "colour": "#dc2626"},
        )
        task_list_create(request)
        self.assertTrue(TaskList.objects.filter(name="Medical").exists())

    def test_sets_position_and_column(self):
        TaskList.objects.create(name="Work", colour="#4f46e5", position=0, column=0)
        request = self.factory.post(
            "/lists/create/",
            data={"name": "Home", "colour": "#059669"},
        )
        task_list_create(request)
        home = TaskList.objects.get(name="Home")
        self.assertEqual(home.position, 1)


class TaskListUpdateTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.tl = TaskList.objects.create(
            name="Work", colour="#4f46e5", position=0, column=0
        )

    def test_updates_name(self):
        request = self.factory.post(
            f"/lists/{self.tl.pk}/update/",
            data={"name": "Office", "colour": "#4f46e5"},
        )
        task_list_update(request, self.tl.pk)
        self.tl.refresh_from_db()
        self.assertEqual(self.tl.name, "Office")


class TaskListDeleteTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.tl = TaskList.objects.create(
            name="Work", colour="#4f46e5", position=0, column=0
        )

    def test_deletes_task_list(self):
        request = self.factory.delete(f"/lists/{self.tl.pk}/delete/")
        task_list_delete(request, self.tl.pk)
        self.assertFalse(TaskList.objects.filter(pk=self.tl.pk).exists())
