from django.test import RequestFactory, TestCase

from tasks.models import Task, TaskLink, TaskList
from tasks.views.links import link_create, link_delete, link_form


class LinkFormTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.work = TaskList.objects.create(
            name="Work", colour="#4f46e5", position=0, column=0
        )
        self.task = Task.objects.create(title="Test", task_list=self.work, position=0)

    def test_returns_form(self):
        request = self.factory.get(f"/link/form/{self.task.pk}/")
        response = link_form(request, self.task.pk)
        self.assertEqual(response.status_code, 200)


class LinkCreateTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.work = TaskList.objects.create(
            name="Work", colour="#4f46e5", position=0, column=0
        )
        self.task = Task.objects.create(title="Test", task_list=self.work, position=0)

    def test_creates_link(self):
        request = self.factory.post(
            f"/link/create/{self.task.pk}/",
            data={"url": "https://example.com", "label": "Example"},
        )
        link_create(request, self.task.pk)
        self.assertEqual(self.task.links.count(), 1)
        link = self.task.links.first()
        self.assertEqual(link.url, "https://example.com")
        self.assertEqual(link.label, "Example")


class LinkDeleteTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.work = TaskList.objects.create(
            name="Work", colour="#4f46e5", position=0, column=0
        )
        self.task = Task.objects.create(title="Test", task_list=self.work, position=0)
        self.link = TaskLink.objects.create(
            task=self.task,
            url="https://example.com",
            label="Example",
            position=0,
        )

    def test_deletes_link(self):
        request = self.factory.delete(f"/link/{self.link.pk}/delete/")
        link_delete(request, self.link.pk)
        self.assertEqual(self.task.links.count(), 0)
