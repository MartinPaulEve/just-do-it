"""Management command to import tasks from Google Tasks via MCP server."""

import json
import re
import subprocess
from datetime import date, timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from tasks.models import Task, TaskList

# Category configuration: keyword patterns mapped to TaskList names
CATEGORY_CONFIG = {
    "Medical": {
        "colour": "#ef4444",
        "icon": "🏥",
        "keywords": [
            "nurosym",
            "postural",
            "hospital",
            "upadacitinib",
            "drugs",
            "hearing",
            "mush",
            "prescriptions",
            "doctor",
            "medical",
            "phone hospital",
        ],
    },
    "Academic (Reading)": {
        "colour": "#3b82f6",
        "icon": "📖",
        "keywords": [
            "read ",
            "review",
        ],
    },
    "Academic (Writing)": {
        "colour": "#8b5cf6",
        "icon": "✍️",
        "keywords": [
            "write ",
            "piece",
            "abstract",
            "preface",
            "slides",
        ],
    },
    "Admin/Legal": {
        "colour": "#f59e0b",
        "icon": "📋",
        "keywords": [
            "contract",
            "redline",
            "attorney",
            "insurance",
            "tax",
            "hmrc",
            "gpg",
        ],
    },
    "Communication": {
        "colour": "#10b981",
        "icon": "💬",
        "keywords": [
            "email",
            "ping",
            "write to",
            "birthday",
            "contact",
            "message",
        ],
    },
    "Personal": {
        "colour": "#ec4899",
        "icon": "🏠",
        "keywords": [
            "shop",
            "present",
            "lottery",
            "tuna",
            "course",
            "pay ",
            "money",
        ],
    },
    "Technology": {
        "colour": "#06b6d4",
        "icon": "💻",
        "keywords": [
            "code",
            "aws",
            "website",
            "login",
            "billing",
        ],
    },
}

# Google Task ID marker prefix used in task descriptions for idempotency
GTASK_ID_PREFIX = "[gtask:"


def categorise_task(title):
    """Determine the category for a task based on its title keywords.

    Checks categories in a priority order. Multi-word keywords (like
    "write to") are checked before single-word ones within each category
    to avoid false positives (e.g. "Write to Sam" is Communication, not
    Academic Writing).
    """
    title_lower = title.lower()

    # Check Communication first — "write to" must beat "write "
    for category_name in [
        "Medical",
        "Communication",
        "Academic (Writing)",
        "Academic (Reading)",
        "Admin/Legal",
        "Technology",
        "Personal",
    ]:
        config = CATEGORY_CONFIG[category_name]
        # Sort keywords longest-first so multi-word patterns match first
        keywords = sorted(config["keywords"], key=len, reverse=True)
        for keyword in keywords:
            if keyword in title_lower:
                return category_name

    return "Personal"


def parse_mcp_task_output(raw_text):
    """Parse the raw text output from the gtasks MCP server's list tool.

    The MCP server returns tasks in a format like:
        Found N tasks:
        Task Title
         (Due: 2026-04-04T00:00:00.000Z) - Notes: ... - ID: ... - Status: ...
         - URI: ... - Hidden: ... }
    """
    tasks = []

    # Strip the "Found N tasks:\n" header
    text = raw_text
    header_match = re.match(r"Found \d+ tasks:\n", text)
    if header_match:
        text = text[header_match.end() :]

    # Split into task blocks — each block ends with "}"
    blocks = re.split(r"\}\n?", text)

    for block in blocks:
        block = block.strip()
        if not block:
            continue

        lines = block.split("\n")
        if len(lines) < 2:
            continue

        title = lines[0].strip()
        detail = "\n".join(lines[1:])

        # Extract fields using regex
        due_match = re.search(r"Due: (\S+?)(?:\)| -)", detail)
        due = None
        if due_match:
            due_raw = due_match.group(1)
            # Parse ISO date, extract just the date part
            date_match = re.match(r"(\d{4}-\d{2}-\d{2})", due_raw)
            if date_match:
                due = date_match.group(1)

        status_match = re.search(r"Status: (\S+)", detail)
        status = status_match.group(1) if status_match else "needsAction"

        id_match = re.search(r"ID: (\S+)", detail)
        task_id = id_match.group(1) if id_match else ""

        notes_match = re.search(r"Notes: (.*?) - ID:", detail)
        notes = ""
        if notes_match:
            notes_raw = notes_match.group(1).strip()
            if notes_raw != "undefined":
                notes = notes_raw

        if title:
            tasks.append(
                {
                    "title": title,
                    "due": due,
                    "status": status,
                    "id": task_id,
                    "uri": "",
                    "notes": notes,
                }
            )

    return tasks


def fetch_tasks_from_mcp(bun_path, server_path):
    """Call the gtasks MCP server and return the raw task list text."""
    # Build JSON-RPC messages
    init_msg = json.dumps(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "import-script", "version": "1.0.0"},
            },
        }
    )
    notify_msg = json.dumps(
        {
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
            "params": {},
        }
    )
    list_msg = json.dumps(
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {"name": "list", "arguments": {}},
        }
    )

    stdin_data = f"{init_msg}\n{notify_msg}\n{list_msg}\n"

    result = subprocess.run(
        [bun_path, "run", server_path],
        input=stdin_data,
        capture_output=True,
        text=True,
        timeout=30,
    )

    # Parse the last line as the tool response
    lines = result.stdout.strip().split("\n")
    for line in reversed(lines):
        try:
            response = json.loads(line)
            if "result" in response and "content" in response["result"]:
                return response["result"]["content"][0]["text"]
        except (json.JSONDecodeError, KeyError, IndexError):
            continue

    raise RuntimeError(f"Failed to get tasks from MCP server. stderr: {result.stderr}")


def build_import_data(raw_tasks, months_back=6):
    """Filter tasks and build structured import data with categories."""
    cutoff = date.today() - timedelta(days=months_back * 30)

    filtered_tasks = []
    for task in raw_tasks:
        is_completed = task.get("status") == "completed"

        if is_completed and task.get("due"):
            try:
                due_date = date.fromisoformat(task["due"])
                if due_date < cutoff:
                    continue
            except (ValueError, TypeError):
                continue

        category = categorise_task(task["title"])

        filtered_tasks.append(
            {
                "title": task["title"],
                "due": task.get("due"),
                "status": task.get("status", "needsAction"),
                "category": category,
                "google_task_id": task.get("id", ""),
                "notes": task.get("notes", ""),
            }
        )

    # Build category config for export (only include categories with colours/icons)
    categories = {}
    for name, config in CATEGORY_CONFIG.items():
        categories[name] = {
            "colour": config["colour"],
            "icon": config["icon"],
        }

    return {
        "categories": categories,
        "tasks": filtered_tasks,
    }


def export_to_json(import_data, output_path):
    """Export structured import data to a JSON file."""
    with open(output_path, "w") as f:
        json.dump(import_data, f, indent=2)


def load_from_json(json_path):
    """Load structured import data from a JSON file."""
    with open(json_path) as f:
        return json.load(f)


def import_tasks_to_db(import_data):
    """Create TaskList and Task objects from structured import data.

    Returns a dict with counts of created/skipped items.
    """
    lists_created = 0
    tasks_created = 0
    tasks_skipped = 0

    # Create or get TaskLists for each category
    task_lists = {}
    max_position = TaskList.objects.count()

    for name, config in import_data["categories"].items():
        task_list, created = TaskList.objects.get_or_create(
            name=name,
            defaults={
                "colour": config["colour"],
                "icon": config.get("icon", ""),
                "position": max_position,
                "column": 0,
            },
        )
        if created:
            lists_created += 1
            max_position += 1
        task_lists[name] = task_list

    # Create tasks
    for task_data in import_data["tasks"]:
        gtask_id = task_data.get("google_task_id", "")

        # Idempotency check: look for existing task with same Google Task ID
        if gtask_id:
            marker = f"{GTASK_ID_PREFIX}{gtask_id}]"
            if Task.objects.filter(description__contains=marker).exists():
                tasks_skipped += 1
                continue

        category = task_data.get("category", "Personal")
        task_list = task_lists.get(category)
        if not task_list:
            task_list = task_lists.get("Personal", list(task_lists.values())[0])

        # Build description with Google Task ID marker and notes
        description_parts = []
        if task_data.get("notes"):
            description_parts.append(task_data["notes"])
        if gtask_id:
            description_parts.append(f"{GTASK_ID_PREFIX}{gtask_id}]")
        description = "\n".join(description_parts)

        # Parse due date
        deadline = None
        if task_data.get("due"):
            try:
                deadline = date.fromisoformat(task_data["due"])
            except (ValueError, TypeError):
                pass

        is_completed = task_data.get("status") == "completed"

        Task.objects.create(
            title=task_data["title"],
            description=description,
            task_list=task_list,
            deadline=deadline,
            start_date=deadline,
            completed=is_completed,
            completed_at=timezone.now() if is_completed else None,
            position=Task.objects.filter(task_list=task_list).count(),
        )
        tasks_created += 1

    return {
        "lists_created": lists_created,
        "tasks_created": tasks_created,
        "tasks_skipped": tasks_skipped,
    }


class Command(BaseCommand):
    help = "Import tasks from Google Tasks via MCP server."

    def add_arguments(self, parser):
        parser.add_argument(
            "--from-json",
            type=str,
            help="Import from a JSON file instead of calling the MCP server.",
        )
        parser.add_argument(
            "--output",
            type=str,
            default="google_tasks_export.json",
            help="Path for the JSON export file (default: google_tasks_export.json).",
        )
        parser.add_argument(
            "--bun-path",
            type=str,
            default="/home/martin/.bun/bin/bun",
            help="Path to the bun binary.",
        )
        parser.add_argument(
            "--server-path",
            type=str,
            default="/home/martin/Documents/Programming/gtasks-mcp/dist/index.js",
            help="Path to the gtasks MCP server index.js.",
        )
        parser.add_argument(
            "--months-back",
            type=int,
            default=6,
            help="Include completed tasks from this many months back (default: 6).",
        )

    def handle(self, *args, **options):
        if options["from_json"]:
            self.stdout.write(f"Loading tasks from {options['from_json']}...")
            import_data = load_from_json(options["from_json"])
        else:
            self.stdout.write("Fetching tasks from Google Tasks MCP server...")
            raw_text = fetch_tasks_from_mcp(options["bun_path"], options["server_path"])
            raw_tasks = parse_mcp_task_output(raw_text)
            self.stdout.write(f"Parsed {len(raw_tasks)} tasks from Google Tasks.")

            import_data = build_import_data(
                raw_tasks, months_back=options["months_back"]
            )

            # Export to JSON
            output_path = options["output"]
            export_to_json(import_data, output_path)
            self.stdout.write(self.style.SUCCESS(f"Exported to {output_path}"))

        # Import into database
        result = import_tasks_to_db(import_data)
        self.stdout.write(
            self.style.SUCCESS(
                f"Import complete: {result['lists_created']} lists created, "
                f"{result['tasks_created']} tasks created, "
                f"{result['tasks_skipped']} tasks skipped."
            )
        )
