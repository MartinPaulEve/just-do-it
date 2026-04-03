from datetime import date, timedelta

from django.test import RequestFactory, TestCase

from tasks.models import Task, TaskList
from tasks.views.all_tasks import all_tasks_view


class AllTasksViewTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.work = TaskList.objects.create(
            name="Work", colour="#4f46e5", position=0, column=0
        )

    def test_returns_200(self):
        request = self.factory.get("/all/")
        response = all_tasks_view(request)
        self.assertEqual(response.status_code, 200)

    def test_shows_all_tasks_including_completed(self):
        Task.objects.create(title="Active", task_list=self.work, position=0)
        Task.objects.create(
            title="Done",
            task_list=self.work,
            position=1,
            completed=True,
        )
        request = self.factory.get("/all/")
        response = all_tasks_view(request)
        content = response.content.decode()
        self.assertIn("Active", content)
        self.assertIn("Done", content)

    def test_shows_future_tasks(self):
        Task.objects.create(
            title="Future",
            task_list=self.work,
            position=0,
            start_date=date.today() + timedelta(days=30),
        )
        request = self.factory.get("/all/")
        response = all_tasks_view(request)
        self.assertIn(b"Future", response.content)

    def test_filters_by_task_list(self):
        home = TaskList.objects.create(
            name="Home", colour="#059669", position=0, column=1
        )
        Task.objects.create(title="Work task", task_list=self.work, position=0)
        Task.objects.create(title="Home task", task_list=home, position=0)
        request = self.factory.get("/all/", {"list": self.work.pk})
        response = all_tasks_view(request)
        content = response.content.decode()
        self.assertIn("Work task", content)
        self.assertNotIn("Home task", content)

    def test_filters_by_status_active(self):
        Task.objects.create(title="Active", task_list=self.work, position=0)
        Task.objects.create(
            title="Done",
            task_list=self.work,
            position=1,
            completed=True,
        )
        request = self.factory.get("/all/", {"status": "active"})
        response = all_tasks_view(request)
        content = response.content.decode()
        self.assertIn("Active", content)
        self.assertNotIn("Done", content)
