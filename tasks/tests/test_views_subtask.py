from django.test import RequestFactory, TestCase

from tasks.models import Task, TaskList
from tasks.views.subtask import subtask_create, subtask_form, subtask_toggle


class SubtaskFormTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.work = TaskList.objects.create(
            name="Work", colour="#4f46e5", position=0, column=0
        )
        self.parent = Task.objects.create(
            title="Parent", task_list=self.work, position=0
        )

    def test_returns_form_html(self):
        request = self.factory.get(f"/subtask/form/{self.parent.pk}/")
        response = subtask_form(request, self.parent.pk)
        self.assertEqual(response.status_code, 200)


class SubtaskCreateTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.work = TaskList.objects.create(
            name="Work", colour="#4f46e5", position=0, column=0
        )
        self.parent = Task.objects.create(
            title="Parent", task_list=self.work, position=0
        )

    def test_creates_subtask_linked_to_parent(self):
        request = self.factory.post(
            f"/subtask/create/{self.parent.pk}/",
            data={"title": "Child task"},
        )
        subtask_create(request, self.parent.pk)
        child = Task.objects.get(title="Child task")
        self.assertEqual(child.parent_task, self.parent)
        self.assertEqual(child.task_list, self.work)


class SubtaskToggleTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.work = TaskList.objects.create(
            name="Work", colour="#4f46e5", position=0, column=0
        )
        self.parent = Task.objects.create(
            title="Parent", task_list=self.work, position=0
        )
        self.subtask = Task.objects.create(
            title="Sub",
            task_list=self.work,
            position=0,
            parent_task=self.parent,
        )

    def test_toggles_subtask_complete(self):
        request = self.factory.post(f"/subtask/{self.subtask.pk}/toggle/")
        subtask_toggle(request, self.subtask.pk)
        self.subtask.refresh_from_db()
        self.assertTrue(self.subtask.completed)
