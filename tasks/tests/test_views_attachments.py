from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory, TestCase

from tasks.models import Task, TaskAttachment, TaskList
from tasks.views.attachments import attachment_create, attachment_delete


class AttachmentCreateTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.work = TaskList.objects.create(
            name="Work", colour="#4f46e5", position=0, column=0
        )
        self.task = Task.objects.create(title="Test", task_list=self.work, position=0)

    def test_creates_attachment(self):
        test_file = SimpleUploadedFile(
            "test.txt", b"file content", content_type="text/plain"
        )
        request = self.factory.post(
            f"/attachment/create/{self.task.pk}/",
            data={"file": test_file},
        )
        attachment_create(request, self.task.pk)
        self.assertEqual(self.task.attachments.count(), 1)
        self.assertEqual(self.task.attachments.first().filename, "test.txt")


class AttachmentDeleteTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.work = TaskList.objects.create(
            name="Work", colour="#4f46e5", position=0, column=0
        )
        self.task = Task.objects.create(title="Test", task_list=self.work, position=0)
        self.attachment = TaskAttachment.objects.create(
            task=self.task,
            file="attachments/test.txt",
            filename="test.txt",
        )

    def test_deletes_attachment(self):
        request = self.factory.delete(f"/attachment/{self.attachment.pk}/delete/")
        attachment_delete(request, self.attachment.pk)
        self.assertEqual(self.task.attachments.count(), 0)
