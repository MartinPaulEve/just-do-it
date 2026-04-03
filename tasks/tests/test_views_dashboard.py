# tasks/tests/test_views_dashboard.py
from datetime import date, timedelta

from django.test import RequestFactory, TestCase

from tasks.models import Task, TaskList
from tasks.views.dashboard import dashboard_view, task_list_panel_partial


class DashboardViewTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.work = TaskList.objects.create(
            name="Work", colour="#4f46e5", position=0, column=0
        )
        self.home = TaskList.objects.create(
            name="Home", colour="#059669", position=0, column=1
        )

    def test_dashboard_returns_200(self):
        request = self.factory.get("/")
        response = dashboard_view(request)
        self.assertEqual(response.status_code, 200)

    def test_dashboard_contains_task_lists(self):
        request = self.factory.get("/")
        response = dashboard_view(request)
        content = response.content.decode()
        self.assertIn("Work", content)
        self.assertIn("Home", content)

    def test_dashboard_groups_lists_by_column(self):
        request = self.factory.get("/")
        response = dashboard_view(request)
        self.assertEqual(response.status_code, 200)


class TaskListPanelPartialTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.work = TaskList.objects.create(
            name="Work", colour="#4f46e5", position=0, column=0
        )

    def test_panel_returns_200(self):
        request = self.factory.get(f"/panel/{self.work.pk}/")
        response = task_list_panel_partial(request, self.work.pk)
        self.assertEqual(response.status_code, 200)

    def test_panel_shows_active_tasks_only(self):
        Task.objects.create(title="Visible", task_list=self.work, position=0)
        Task.objects.create(
            title="Future",
            task_list=self.work,
            position=1,
            start_date=date.today() + timedelta(days=30),
        )
        Task.objects.create(
            title="Done",
            task_list=self.work,
            position=2,
            completed=True,
        )
        request = self.factory.get(f"/panel/{self.work.pk}/")
        response = task_list_panel_partial(request, self.work.pk)
        content = response.content.decode()
        self.assertIn("Visible", content)
        self.assertNotIn("Future", content)
        self.assertNotIn("Done", content)

    def test_panel_hides_subtasks_from_top_level(self):
        parent = Task.objects.create(title="Parent", task_list=self.work, position=0)
        Task.objects.create(
            title="Child",
            task_list=self.work,
            position=0,
            parent_task=parent,
        )
        request = self.factory.get(f"/panel/{self.work.pk}/")
        response = task_list_panel_partial(request, self.work.pk)
        content = response.content.decode()
        self.assertIn("Parent", content)
        self.assertNotIn("Child", content)
