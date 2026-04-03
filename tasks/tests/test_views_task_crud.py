from django.test import RequestFactory, TestCase

from tasks.models import Task, TaskList
from tasks.views.task_crud import (
    task_create,
    task_create_form,
    task_delete,
    task_expand,
    task_toggle,
    task_update,
)


class TaskCreateFormTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.work = TaskList.objects.create(
            name="Work", colour="#4f46e5", position=0, column=0
        )

    def test_returns_form_html(self):
        request = self.factory.get(f"/task/create-form/{self.work.pk}/")
        response = task_create_form(request, self.work.pk)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"title", response.content)


class TaskCreateTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.work = TaskList.objects.create(
            name="Work", colour="#4f46e5", position=0, column=0
        )

    def test_creates_task_and_returns_panel(self):
        request = self.factory.post(
            f"/task/create/{self.work.pk}/",
            data={"title": "New task"},
        )
        response = task_create(request, self.work.pk)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Task.objects.filter(title="New task").exists())

    def test_sets_position_to_next_in_list(self):
        Task.objects.create(title="Existing", task_list=self.work, position=0)
        request = self.factory.post(
            f"/task/create/{self.work.pk}/",
            data={"title": "New"},
        )
        task_create(request, self.work.pk)
        new_task = Task.objects.get(title="New")
        self.assertEqual(new_task.position, 1)


class TaskExpandTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.work = TaskList.objects.create(
            name="Work", colour="#4f46e5", position=0, column=0
        )
        self.task = Task.objects.create(title="Test", task_list=self.work, position=0)

    def test_returns_expanded_card(self):
        request = self.factory.get(f"/task/{self.task.pk}/expand/")
        response = task_expand(request, self.task.pk)
        self.assertEqual(response.status_code, 200)


class TaskUpdateTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.work = TaskList.objects.create(
            name="Work", colour="#4f46e5", position=0, column=0
        )
        self.task = Task.objects.create(title="Old", task_list=self.work, position=0)

    def test_updates_title(self):
        request = self.factory.post(
            f"/task/{self.task.pk}/update/",
            data={"title": "New Title", "description": ""},
        )
        response = task_update(request, self.task.pk)
        self.assertEqual(response.status_code, 200)
        self.task.refresh_from_db()
        self.assertEqual(self.task.title, "New Title")


class TaskToggleTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.work = TaskList.objects.create(
            name="Work", colour="#4f46e5", position=0, column=0
        )
        self.task = Task.objects.create(title="Todo", task_list=self.work, position=0)

    def test_toggle_completes_task(self):
        request = self.factory.post(f"/task/{self.task.pk}/toggle/")
        task_toggle(request, self.task.pk)
        self.task.refresh_from_db()
        self.assertTrue(self.task.completed)

    def test_toggle_uncompletes_task(self):
        self.task.completed = True
        self.task.save()
        request = self.factory.post(f"/task/{self.task.pk}/toggle/")
        task_toggle(request, self.task.pk)
        self.task.refresh_from_db()
        self.assertFalse(self.task.completed)


class TaskDeleteTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.work = TaskList.objects.create(
            name="Work", colour="#4f46e5", position=0, column=0
        )
        self.task = Task.objects.create(
            title="Delete me", task_list=self.work, position=0
        )

    def test_deletes_task(self):
        request = self.factory.delete(f"/task/{self.task.pk}/delete/")
        response = task_delete(request, self.task.pk)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Task.objects.filter(pk=self.task.pk).exists())
