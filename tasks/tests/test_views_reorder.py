import json

from django.test import RequestFactory, TestCase

from tasks.models import Task, TaskList
from tasks.views.reorder import reorder_panels, reorder_tasks


class ReorderPanelsTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.work = TaskList.objects.create(
            name="Work", colour="#4f46e5", position=0, column=0
        )
        self.home = TaskList.objects.create(
            name="Home", colour="#059669", position=0, column=1
        )

    def test_updates_column_and_position(self):
        payload = json.dumps(
            {
                "layout": [
                    {"list_id": self.home.pk, "column": 0, "position": 0},
                    {"list_id": self.work.pk, "column": 1, "position": 0},
                ]
            }
        )
        request = self.factory.post(
            "/reorder/panels/",
            data=payload,
            content_type="application/json",
        )
        response = reorder_panels(request)
        self.assertEqual(response.status_code, 204)
        self.work.refresh_from_db()
        self.home.refresh_from_db()
        self.assertEqual(self.work.column, 1)
        self.assertEqual(self.home.column, 0)


class ReorderTasksTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.work = TaskList.objects.create(
            name="Work", colour="#4f46e5", position=0, column=0
        )
        self.t1 = Task.objects.create(title="First", task_list=self.work, position=0)
        self.t2 = Task.objects.create(title="Second", task_list=self.work, position=1)
        self.t3 = Task.objects.create(title="Third", task_list=self.work, position=2)

    def test_reorders_tasks(self):
        payload = json.dumps(
            {
                "list_id": self.work.pk,
                "task_ids": [self.t3.pk, self.t1.pk, self.t2.pk],
            }
        )
        request = self.factory.post(
            "/reorder/tasks/",
            data=payload,
            content_type="application/json",
        )
        response = reorder_tasks(request)
        self.assertEqual(response.status_code, 204)
        self.t1.refresh_from_db()
        self.t2.refresh_from_db()
        self.t3.refresh_from_db()
        self.assertEqual(self.t3.position, 0)
        self.assertEqual(self.t1.position, 1)
        self.assertEqual(self.t2.position, 2)
