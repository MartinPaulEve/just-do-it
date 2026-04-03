import json
from datetime import date, timedelta

from django.test import RequestFactory, TestCase

from tasks.models import Task, TaskList
from tasks.views.calendar import calendar_events, calendar_view


class CalendarViewTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_returns_200(self):
        request = self.factory.get("/calendar/")
        response = calendar_view(request)
        self.assertEqual(response.status_code, 200)


class CalendarEventsTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.work = TaskList.objects.create(
            name="Work", colour="#4f46e5", position=0, column=0
        )

    def test_returns_json(self):
        Task.objects.create(
            title="Meeting",
            task_list=self.work,
            position=0,
            deadline=date.today() + timedelta(days=3),
        )
        request = self.factory.get(
            "/calendar/events/",
            {"start": str(date.today()), "end": str(date.today() + timedelta(days=30))},
        )
        response = calendar_events(request)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["title"], "Meeting")

    def test_excludes_tasks_without_deadline(self):
        Task.objects.create(title="No deadline", task_list=self.work, position=0)
        request = self.factory.get(
            "/calendar/events/",
            {"start": str(date.today()), "end": str(date.today() + timedelta(days=30))},
        )
        response = calendar_events(request)
        data = json.loads(response.content)
        self.assertEqual(len(data), 0)

    def test_includes_task_colour(self):
        Task.objects.create(
            title="Coloured",
            task_list=self.work,
            position=0,
            deadline=date.today(),
        )
        request = self.factory.get(
            "/calendar/events/",
            {
                "start": str(date.today() - timedelta(days=1)),
                "end": str(date.today() + timedelta(days=1)),
            },
        )
        response = calendar_events(request)
        data = json.loads(response.content)
        self.assertEqual(data[0]["backgroundColor"], "#4f46e5")
