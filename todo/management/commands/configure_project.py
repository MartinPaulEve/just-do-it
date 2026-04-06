"""
Management command to configure the project name and metadata.

Renames the Django project package, updates all references in config files,
settings, Docker files, CI workflows, and .env examples.

Usage:
    python manage.py configure_project --name myproject
    python manage.py configure_project --name myproject --description "My app"
"""

import re
import shutil
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Configure the project name, description, and version across all files"

    def add_arguments(self, parser):
        parser.add_argument(
            "--name",
            required=True,
            help="New project name (Python identifier, e.g. 'myproject')",
        )
        parser.add_argument(
            "--description",
            default="",
            help="Project description for pyproject.toml",
        )
        parser.add_argument(
            "--version",
            default="0.0.1",
            help="Initial version (default: 0.0.1)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be changed without making changes",
        )

    def handle(self, *args, **options):
        name = options["name"]
        description = options["description"]
        version = options["version"]
        dry_run = options["dry_run"]

        if not name.isidentifier():
            raise CommandError(
                f"'{name}' is not a valid Python identifier. "
                "Use only letters, digits, and underscores."
            )

        base_dir = Path(__file__).resolve().parent.parent.parent.parent
        old_package = "todo"

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN — no changes will be made"))

        self.stdout.write(f"Configuring project as '{name}'...")

        replacements = self._build_replacements(
            base_dir, old_package, name, description, version
        )

        for filepath, subs in replacements.items():
            self._apply_replacements(filepath, subs, dry_run)

        # Rename the Django project package directory
        old_dir = base_dir / old_package
        new_dir = base_dir / name
        if old_dir.exists() and old_package != name:
            if dry_run:
                self.stdout.write(f"  Would rename {old_dir} -> {new_dir}")
            else:
                if new_dir.exists():
                    raise CommandError(
                        f"Directory '{new_dir}' already exists. "
                        "Remove it first or choose a different name."
                    )
                shutil.move(str(old_dir), str(new_dir))
                self.stdout.write(
                    self.style.SUCCESS(f"  Renamed {old_package}/ -> {name}/")
                )

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(f"Project configured as '{name}'!"))
        self.stdout.write("")
        self.stdout.write("Next steps:")
        self.stdout.write("  1. Update .env files with your credentials")
        self.stdout.write("  2. Run: docker compose up -d")
        self.stdout.write("  3. Create your first app: python manage.py startapp myapp")

    def _build_replacements(self, base_dir, old_package, name, description, version):
        """Build a dict of filepath -> [(old, new), ...] replacements."""
        replacements = {}
        desc = description or "Django project"

        # pyproject.toml
        pyproject = base_dir / "pyproject.toml"
        if pyproject.exists():
            cur_ver = self._read_current_version(pyproject)
            replacements[pyproject] = [
                ('name = "myproject"', f'name = "{name}"'),
                (
                    'description = "Django project template"',
                    f'description = "{desc}"',
                ),
                (
                    f'version = "{cur_ver}"',
                    f'version = "{version}"',
                ),
                (
                    f'known-first-party = ["{old_package}", "config"]',
                    f'known-first-party = ["{name}", "config"]',
                ),
            ]

        # __version__.py
        version_file = base_dir / "__version__.py"
        if version_file.exists():
            cur_ver = self._read_current_version(version_file)
            replacements[version_file] = [
                (
                    f'__version__ = "{cur_ver}"',
                    f'__version__ = "{version}"',
                ),
            ]

        # config/settings/base.py
        base_settings = base_dir / "config" / "settings" / "base.py"
        if base_settings.exists():
            replacements[base_settings] = self._settings_replacements(old_package, name)

        # config/settings/test.py
        test_settings = base_dir / "config" / "settings" / "test.py"
        if test_settings.exists():
            replacements[test_settings] = self._settings_replacements(old_package, name)

        # compose/Dockerfile
        dockerfile = base_dir / "compose" / "Dockerfile"
        if dockerfile.exists():
            replacements[dockerfile] = [
                (
                    f"{old_package}.asgi:application",
                    f"{name}.asgi:application",
                ),
            ]

        # compose/start.sh
        start_sh = base_dir / "compose" / "start.sh"
        if start_sh.exists():
            replacements[start_sh] = [
                (
                    f"{old_package}.asgi:application",
                    f"{name}.asgi:application",
                ),
            ]

        # .env.example
        env_example = base_dir / ".env.example"
        if env_example.exists():
            replacements[env_example] = [
                ("POSTGRES_DB=myproject", f"POSTGRES_DB={name}"),
                ("POSTGRES_USER=myproject", f"POSTGRES_USER={name}"),
            ]

        # .env.prod.example
        env_prod = base_dir / ".env.prod.example"
        if env_prod.exists():
            replacements[env_prod] = [
                ("POSTGRES_DB=myproject", f"POSTGRES_DB={name}"),
                ("POSTGRES_USER=myproject", f"POSTGRES_USER={name}"),
                (
                    "ALLOWED_HOSTS=myproject.example.com",
                    f"ALLOWED_HOSTS={name}.example.com",
                ),
                (
                    "CSRF_TRUSTED_ORIGINS=https://myproject.example.com",
                    f"CSRF_TRUSTED_ORIGINS=https://{name}.example.com",
                ),
            ]

        # .github/workflows/ci.yml
        ci_yml = base_dir / ".github" / "workflows" / "ci.yml"
        if ci_yml.exists():
            replacements[ci_yml] = [
                (
                    "POSTGRES_DB: myproject_test",
                    f"POSTGRES_DB: {name}_test",
                ),
                (
                    "POSTGRES_USER: myproject",
                    f"POSTGRES_USER: {name}",
                ),
                (
                    "POSTGRES_PASSWORD: myproject",
                    f"POSTGRES_PASSWORD: {name}",
                ),
            ]

        # docker-compose.prod.yml
        prod_compose = base_dir / "docker-compose.prod.yml"
        if prod_compose.exists():
            replacements[prod_compose] = [
                (
                    "pg_isready -U $${POSTGRES_USER:-myproject}",
                    f"pg_isready -U $${{POSTGRES_USER:-{name}}}",
                ),
            ]

        return replacements

    def _settings_replacements(self, old_package, name):
        """Build replacement pairs for a Django settings file."""
        subs = [
            (
                f'ROOT_URLCONF = "{old_package}.urls"',
                f'ROOT_URLCONF = "{name}.urls"',
            ),
            (
                f'WSGI_APPLICATION = "{old_package}.wsgi.application"',
                f'WSGI_APPLICATION = "{name}.wsgi.application"',
            ),
            (
                f'ASGI_APPLICATION = "{old_package}.asgi.application"',
                f'ASGI_APPLICATION = "{name}.asgi.application"',
            ),
        ]
        for key in ("POSTGRES_DB", "POSTGRES_USER", "POSTGRES_PASSWORD"):
            old = f'"{key}", "myproject"'
            new = f'"{key}", "{name}"'
            subs.append((old, new))
        return subs

    def _apply_replacements(self, filepath, subs, dry_run):
        """Apply a list of (old, new) string replacements to a file."""
        if not subs:
            return

        filepath = Path(filepath)
        if not filepath.exists():
            self.stdout.write(self.style.WARNING(f"  Skipping {filepath} (not found)"))
            return

        content = filepath.read_text()
        changed = False

        for old, new in subs:
            if old == new:
                continue
            if old in content:
                content = content.replace(old, new)
                changed = True
                if dry_run:
                    self.stdout.write(f"  {filepath}: '{old}' -> '{new}'")

        if changed and not dry_run:
            filepath.write_text(content)
            self.stdout.write(self.style.SUCCESS(f"  Updated {filepath}"))

    def _read_current_version(self, filepath):
        """Extract the current version string from a file."""
        content = Path(filepath).read_text()
        match = re.search(r'version\s*=\s*"([^"]+)"', content)
        if match:
            return match.group(1)
        match = re.search(r'__version__\s*=\s*"([^"]+)"', content)
        if match:
            return match.group(1)
        return "0.0.1"
