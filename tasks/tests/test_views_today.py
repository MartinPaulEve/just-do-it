from datetime import date, timedelta

from django.test import RequestFactory, TestCase

from tasks.models import Task, TaskList
from tasks.views.today import today_view


class TodayViewTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.work = TaskList.objects.create(
            name="Work", colour="#4f46e5", position=0, column=0
        )
        self.home = TaskList.objects.create(
            name="Home", colour="#059669", position=0, column=1
        )

    def test_returns_200(self):
        request = self.factory.get("/today/")
        response = today_view(request)
        self.assertEqual(response.status_code, 200)

    def test_shows_tasks_due_today(self):
        Task.objects.create(
            title="Due today",
            task_list=self.work,
            position=0,
            deadline=date.today(),
        )
        request = self.factory.get("/today/")
        response = today_view(request)
        self.assertIn(b"Due today", response.content)

    def test_shows_overdue_tasks(self):
        Task.objects.create(
            title="Overdue",
            task_list=self.work,
            position=0,
            deadline=date.today() - timedelta(days=3),
        )
        request = self.factory.get("/today/")
        response = today_view(request)
        self.assertIn(b"Overdue", response.content)

    def test_hides_future_tasks(self):
        Task.objects.create(
            title="Future",
            task_list=self.work,
            position=0,
            deadline=date.today() + timedelta(days=5),
        )
        request = self.factory.get("/today/")
        response = today_view(request)
        self.assertNotIn(b"Future", response.content)

    def test_hides_completed_tasks(self):
        Task.objects.create(
            title="Done",
            task_list=self.work,
            position=0,
            deadline=date.today(),
            completed=True,
        )
        request = self.factory.get("/today/")
        response = today_view(request)
        self.assertNotIn(b"Done", response.content)

    def test_groups_by_task_list(self):
        Task.objects.create(
            title="Work task",
            task_list=self.work,
            position=0,
            deadline=date.today(),
        )
        Task.objects.create(
            title="Home task",
            task_list=self.home,
            position=0,
            deadline=date.today(),
        )
        request = self.factory.get("/today/")
        response = today_view(request)
        content = response.content.decode()
        self.assertIn("Work", content)
        self.assertIn("Home", content)
