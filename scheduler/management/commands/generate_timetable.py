from django.core.management.base import BaseCommand
from scheduler.algorithm import generate_timetable, persist_result


class Command(BaseCommand):
    help = "Generate the timetable from current data."

    def handle(self, *args, **kwargs):
        result = generate_timetable()
        n = persist_result(result)
        if result.success:
            self.stdout.write(self.style.SUCCESS(f"Generated {n} sessions, no conflicts."))
        else:
            self.stdout.write(self.style.WARNING(
                f"Generated {n} sessions; {len(result.unscheduled)} unscheduled."))
