from django.core.management.base import BaseCommand

from tasks.recurrence import ensure_series_generated


class Command(BaseCommand):
    help = "Generate recurring task instances for the next N days (default 90)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=90,
            help="Number of days ahead to generate instances (default: 90).",
        )

    def handle(self, *args, **options):
        horizon_days = options["days"]
        ensure_series_generated(horizon_days=horizon_days)
        self.stdout.write(
            self.style.SUCCESS(
                f"Recurring task instances generated for the next {horizon_days} days."
            )
        )
