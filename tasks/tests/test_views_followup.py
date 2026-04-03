from django.test import RequestFactory, TestCase

from tasks.models import Task, TaskList
from tasks.views.followup import followup_create, followup_form


class FollowupFormTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.work = TaskList.objects.create(
            name="Work", colour="#4f46e5", position=0, column=0
        )
        self.task = Task.objects.create(
            title="Original", task_list=self.work, position=0
        )

    def test_returns_form_with_prefilled_title(self):
        request = self.factory.get(f"/followup/form/{self.task.pk}/")
        response = followup_form(request, self.task.pk)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Follow-up: Original", response.content)


class FollowupCreateTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.work = TaskList.objects.create(
            name="Work", colour="#4f46e5", position=0, column=0
        )
        self.task = Task.objects.create(
            title="Original", task_list=self.work, position=0
        )

    def test_creates_followup_task(self):
        request = self.factory.post(
            f"/followup/create/{self.task.pk}/",
            data={
                "title": "Follow-up: Original",
                "start_date": "2026-04-15",
                "deadline": "2026-04-20",
            },
        )
        followup_create(request, self.task.pk)
        followup = Task.objects.get(title="Follow-up: Original")
        self.assertEqual(followup.follow_up_from, self.task)
        self.assertEqual(followup.task_list, self.work)

    def test_followup_can_have_custom_title(self):
        request = self.factory.post(
            f"/followup/create/{self.task.pk}/",
            data={
                "title": "Custom title",
                "start_date": "2026-04-15",
            },
        )
        followup_create(request, self.task.pk)
        self.assertTrue(Task.objects.filter(title="Custom title").exists())
