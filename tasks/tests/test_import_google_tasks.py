"""Tests for the import_google_tasks management command."""

import tempfile
from datetime import date, timedelta

from django.test import TestCase

from tasks.management.commands.import_google_tasks import (
    build_import_data,
    categorise_task,
    export_to_json,
    import_tasks_to_db,
    load_from_json,
    parse_mcp_task_output,
)
from tasks.models import Task, TaskList


class CategoriseTaskTest(TestCase):
    """Test keyword-based task categorisation."""

    def test_medical_keywords(self):
        self.assertEqual(categorise_task("Do Nurosym"), "Medical")
        self.assertEqual(categorise_task("Postural device"), "Medical")
        self.assertEqual(categorise_task("Phone hospital re upadacitinib"), "Medical")
        self.assertEqual(categorise_task("Evening drugs"), "Medical")

    def test_academic_reading_keywords(self):
        self.assertEqual(
            categorise_task("Read Lara and Tom book proposal"),
            "Academic (Reading)",
        )
        self.assertEqual(categorise_task("Read C H-B review"), "Academic (Reading)")
        self.assertEqual(categorise_task("Stanford peer review"), "Academic (Reading)")

    def test_academic_writing_keywords(self):
        self.assertEqual(
            categorise_task("Write AI and Gothic piece"),
            "Academic (Writing)",
        )
        self.assertEqual(
            categorise_task("Do abstract for OpenFest keynote"),
            "Academic (Writing)",
        )

    def test_admin_legal_keywords(self):
        self.assertEqual(
            categorise_task("Look at and redline OLH contract"),
            "Admin/Legal",
        )
        self.assertEqual(
            categorise_task("Lasting power of attorney"),
            "Admin/Legal",
        )

    def test_communication_keywords(self):
        self.assertEqual(categorise_task("Email Sam Moore"), "Communication")
        self.assertEqual(categorise_task("Ping David Winters"), "Communication")
        self.assertEqual(
            categorise_task("Birthday message for Andrew"),
            "Communication",
        )

    def test_personal_keywords(self):
        self.assertEqual(categorise_task("Shop"), "Personal")
        self.assertEqual(categorise_task("Pay Thalia"), "Personal")

    def test_technology_keywords(self):
        self.assertEqual(categorise_task("Try Manal's code"), "Technology")
        self.assertEqual(categorise_task("Check AWS billing"), "Technology")

    def test_uncategorised_falls_back_to_personal(self):
        self.assertEqual(categorise_task("Some random thing"), "Personal")

    def test_case_insensitive_matching(self):
        self.assertEqual(categorise_task("READ something"), "Academic (Reading)")
        self.assertEqual(categorise_task("PHONE HOSPITAL"), "Medical")


class ParseMcpTaskOutputTest(TestCase):
    """Test parsing the raw text output from the MCP server."""

    def test_parses_single_task(self):
        raw = (
            "Found 1 tasks:\n"
            "Do Nurosym\n"
            " (Due: 2026-04-04T00:00:00.000Z) - Notes: undefined "
            "- ID: abc123 - Status: needsAction "
            "- URI: https://www.googleapis.com/tasks/v1/lists/list1/tasks/abc123 "
            "- Hidden: undefined - Parent: undefined - Deleted?: undefined "
            "- Completed Date: undefined - Position: 00000000000000000000 "
            "- Updated Date: 2026-04-03T23:07:33.788Z "
            '- ETag: "HHC-rdtryeU" - Links:  - Kind: tasks#task}'
        )
        tasks = parse_mcp_task_output(raw)
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0]["title"], "Do Nurosym")
        self.assertEqual(tasks[0]["due"], "2026-04-04")
        self.assertEqual(tasks[0]["status"], "needsAction")
        self.assertEqual(tasks[0]["id"], "abc123")

    def test_parses_multiple_tasks(self):
        raw = (
            "Found 2 tasks:\n"
            "Task One\n"
            " (Due: 2026-04-04T00:00:00.000Z) - Notes: undefined "
            "- ID: id1 - Status: needsAction "
            "- URI: https://example.com/tasks/id1 "
            "- Hidden: undefined - Parent: undefined - Deleted?: undefined "
            "- Completed Date: undefined - Position: 00000000000000000000 "
            "- Updated Date: 2026-04-03T23:07:33.788Z "
            '- ETag: "tag1" - Links:  - Kind: tasks#task}\n'
            "Task Two\n"
            " (Due: 2026-04-05T00:00:00.000Z) - Notes: some notes "
            "- ID: id2 - Status: completed "
            "- URI: https://example.com/tasks/id2 "
            "- Hidden: undefined - Parent: undefined - Deleted?: undefined "
            "- Completed Date: 2026-04-05T10:00:00.000Z "
            "- Position: 00000000000000000001 "
            "- Updated Date: 2026-04-04T10:00:00.000Z "
            '- ETag: "tag2" - Links:  - Kind: tasks#task}'
        )
        tasks = parse_mcp_task_output(raw)
        self.assertEqual(len(tasks), 2)
        self.assertEqual(tasks[0]["title"], "Task One")
        self.assertEqual(tasks[1]["title"], "Task Two")
        self.assertEqual(tasks[1]["status"], "completed")
        self.assertEqual(tasks[1]["notes"], "some notes")

    def test_handles_task_with_no_due_date(self):
        raw = (
            "Found 1 tasks:\n"
            "No Due Task\n"
            " (Due: Not set) - Notes: undefined "
            "- ID: id3 - Status: needsAction "
            "- URI: https://example.com/tasks/id3 "
            "- Hidden: undefined - Parent: undefined - Deleted?: undefined "
            "- Completed Date: undefined - Position: 00000000000000000000 "
            "- Updated Date: 2026-04-03T23:07:33.788Z "
            '- ETag: "tag3" - Links:  - Kind: tasks#task}'
        )
        tasks = parse_mcp_task_output(raw)
        self.assertEqual(len(tasks), 1)
        self.assertIsNone(tasks[0]["due"])

    def test_handles_notes_with_url(self):
        raw = (
            "Found 1 tasks:\n"
            "Task With Link\n"
            " (Due: 2026-04-12T00:00:00.000Z) "
            "- Notes: https://docs.google.com/document/d/123/edit "
            "- ID: id4 - Status: needsAction "
            "- URI: https://example.com/tasks/id4 "
            "- Hidden: undefined - Parent: undefined - Deleted?: undefined "
            "- Completed Date: undefined - Position: 00000000000000000000 "
            "- Updated Date: 2026-04-03T08:20:28.942Z "
            '- ETag: "tag4" - Links:  - Kind: tasks#task}'
        )
        tasks = parse_mcp_task_output(raw)
        self.assertEqual(
            tasks[0]["notes"],
            "https://docs.google.com/document/d/123/edit",
        )


class BuildImportDataTest(TestCase):
    """Test filtering and structuring tasks for import."""

    def _make_task(self, title, due, status="needsAction", task_id="x"):
        return {
            "title": title,
            "due": due,
            "status": status,
            "id": task_id,
            "uri": f"https://example.com/tasks/{task_id}",
            "notes": "",
        }

    def test_includes_active_tasks(self):
        future = (date.today() + timedelta(days=5)).isoformat()
        tasks = [self._make_task("Active Task", future, task_id="a1")]
        data = build_import_data(tasks, months_back=6)
        titles = [t["title"] for t in data["tasks"]]
        self.assertIn("Active Task", titles)

    def test_includes_recently_completed_tasks(self):
        recent = (date.today() - timedelta(days=30)).isoformat()
        tasks = [
            self._make_task("Recent Done", recent, status="completed", task_id="r1"),
        ]
        data = build_import_data(tasks, months_back=6)
        titles = [t["title"] for t in data["tasks"]]
        self.assertIn("Recent Done", titles)

    def test_excludes_old_completed_tasks(self):
        old = "2021-06-01"
        tasks = [
            self._make_task("Old Done", old, status="completed", task_id="o1"),
        ]
        data = build_import_data(tasks, months_back=6)
        titles = [t["title"] for t in data["tasks"]]
        self.assertNotIn("Old Done", titles)

    def test_assigns_categories(self):
        future = (date.today() + timedelta(days=5)).isoformat()
        tasks = [self._make_task("Read something", future, task_id="c1")]
        data = build_import_data(tasks, months_back=6)
        self.assertEqual(data["tasks"][0]["category"], "Academic (Reading)")

    def test_includes_category_config(self):
        data = build_import_data([], months_back=6)
        self.assertIn("categories", data)
        self.assertIn("Medical", data["categories"])

    def test_preserves_google_task_id(self):
        future = (date.today() + timedelta(days=5)).isoformat()
        tasks = [self._make_task("Task", future, task_id="gid123")]
        data = build_import_data(tasks, months_back=6)
        self.assertEqual(data["tasks"][0]["google_task_id"], "gid123")


class JsonExportImportTest(TestCase):
    """Test JSON export and re-import round-trip."""

    def test_export_creates_valid_json(self):
        import_data = {
            "categories": {
                "Medical": {"colour": "#ef4444", "icon": "🏥"},
            },
            "tasks": [
                {
                    "title": "Test Task",
                    "due": "2026-04-10",
                    "status": "needsAction",
                    "category": "Medical",
                    "google_task_id": "gt123",
                    "notes": "",
                },
            ],
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            export_to_json(import_data, f.name)
            loaded = load_from_json(f.name)

        self.assertEqual(loaded["tasks"][0]["title"], "Test Task")
        self.assertEqual(loaded["categories"]["Medical"]["colour"], "#ef4444")

    def test_load_from_json_returns_same_structure(self):
        import_data = {
            "categories": {"Personal": {"colour": "#ec4899", "icon": "🏠"}},
            "tasks": [
                {
                    "title": "Shop",
                    "due": "2026-04-04",
                    "status": "needsAction",
                    "category": "Personal",
                    "google_task_id": "s1",
                    "notes": "",
                },
            ],
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            export_to_json(import_data, f.name)
            result = load_from_json(f.name)

        self.assertEqual(len(result["tasks"]), 1)
        self.assertEqual(result["tasks"][0]["google_task_id"], "s1")


class ImportToDbTest(TestCase):
    """Test creating TaskList and Task objects from import data."""

    def test_creates_task_lists_for_categories(self):
        import_data = {
            "categories": {
                "Medical": {"colour": "#ef4444", "icon": "🏥"},
                "Personal": {"colour": "#ec4899", "icon": "🏠"},
            },
            "tasks": [
                {
                    "title": "Do Nurosym",
                    "due": "2026-04-04",
                    "status": "needsAction",
                    "category": "Medical",
                    "google_task_id": "n1",
                    "notes": "",
                },
            ],
        }
        result = import_tasks_to_db(import_data)
        self.assertTrue(TaskList.objects.filter(name="Medical").exists())
        self.assertTrue(TaskList.objects.filter(name="Personal").exists())
        self.assertEqual(result["lists_created"], 2)

    def test_creates_tasks_with_correct_fields(self):
        import_data = {
            "categories": {
                "Medical": {"colour": "#ef4444", "icon": "🏥"},
            },
            "tasks": [
                {
                    "title": "Do Nurosym",
                    "due": "2026-04-04",
                    "status": "needsAction",
                    "category": "Medical",
                    "google_task_id": "n1",
                    "notes": "some notes",
                },
            ],
        }
        import_tasks_to_db(import_data)
        task = Task.objects.get(title="Do Nurosym")
        self.assertEqual(task.task_list.name, "Medical")
        self.assertEqual(task.deadline, date(2026, 4, 4))
        self.assertFalse(task.completed)
        self.assertIn("some notes", task.description)

    def test_marks_completed_tasks(self):
        import_data = {
            "categories": {
                "Personal": {"colour": "#ec4899", "icon": "🏠"},
            },
            "tasks": [
                {
                    "title": "Done Task",
                    "due": "2026-03-01",
                    "status": "completed",
                    "category": "Personal",
                    "google_task_id": "d1",
                    "notes": "",
                },
            ],
        }
        import_tasks_to_db(import_data)
        task = Task.objects.get(title="Done Task")
        self.assertTrue(task.completed)

    def test_idempotent_skips_existing_tasks(self):
        import_data = {
            "categories": {
                "Medical": {"colour": "#ef4444", "icon": "🏥"},
            },
            "tasks": [
                {
                    "title": "Do Nurosym",
                    "due": "2026-04-04",
                    "status": "needsAction",
                    "category": "Medical",
                    "google_task_id": "n1",
                    "notes": "",
                },
            ],
        }
        import_tasks_to_db(import_data)
        result = import_tasks_to_db(import_data)
        self.assertEqual(result["tasks_skipped"], 1)
        self.assertEqual(Task.objects.filter(title="Do Nurosym").count(), 1)

    def test_reuses_existing_task_lists(self):
        TaskList.objects.create(name="Medical", colour="#ef4444", position=0, column=0)
        import_data = {
            "categories": {
                "Medical": {"colour": "#ef4444", "icon": "🏥"},
            },
            "tasks": [],
        }
        result = import_tasks_to_db(import_data)
        self.assertEqual(result["lists_created"], 0)
        self.assertEqual(TaskList.objects.filter(name="Medical").count(), 1)

    def test_handles_task_with_no_due_date(self):
        import_data = {
            "categories": {
                "Personal": {"colour": "#ec4899", "icon": "🏠"},
            },
            "tasks": [
                {
                    "title": "No deadline",
                    "due": None,
                    "status": "needsAction",
                    "category": "Personal",
                    "google_task_id": "nd1",
                    "notes": "",
                },
            ],
        }
        import_tasks_to_db(import_data)
        task = Task.objects.get(title="No deadline")
        self.assertIsNone(task.deadline)

    def test_stores_google_task_id_in_description(self):
        import_data = {
            "categories": {
                "Personal": {"colour": "#ec4899", "icon": "🏠"},
            },
            "tasks": [
                {
                    "title": "Track Me",
                    "due": "2026-04-04",
                    "status": "needsAction",
                    "category": "Personal",
                    "google_task_id": "track123",
                    "notes": "",
                },
            ],
        }
        import_tasks_to_db(import_data)
        task = Task.objects.get(title="Track Me")
        self.assertIn("track123", task.description)
