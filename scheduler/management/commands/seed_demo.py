from datetime import time
from django.core.management.base import BaseCommand
from scheduler.models import (ClassGroup, Course, Lecturer, Room, TimeSlot,
                              ScheduledSession)


class Command(BaseCommand):
    help = "Load demo data: rooms, time slots, lecturers, groups, courses."

    def handle(self, *args, **kwargs):
        ScheduledSession.objects.all().delete()
        Course.objects.all().delete()
        Lecturer.objects.all().delete()
        ClassGroup.objects.all().delete()
        Room.objects.all().delete()
        TimeSlot.objects.all().delete()

        days = ['MON', 'TUE', 'WED', 'THU', 'FRI']
        slot_times = [
            (time(8, 0), time(10, 0)),
            (time(10, 0), time(12, 0)),
            (time(13, 0), time(15, 0)),
            (time(15, 0), time(17, 0)),
        ]
        slots = []
        for d in days:
            for s, e in slot_times:
                slots.append(TimeSlot.objects.create(day=d, start_time=s, end_time=e))

        r1 = Room.objects.create(name='Room A101', capacity=40)
        r2 = Room.objects.create(name='Room B202', capacity=60)
        r3 = Room.objects.create(name='Lab C303', capacity=30)

        francis = Lecturer.objects.create(name='Mr. Francis Anlimah', email='francis@rmu.edu')
        ada = Lecturer.objects.create(name='Dr. Ada Mensah', email='ada@rmu.edu')
        kojo = Lecturer.objects.create(name='Mr. Kojo Boateng', email='kojo@rmu.edu')

        # availability subsets
        francis.available_slots.set(slots[:12])
        ada.available_slots.set(slots[4:])
        # kojo has no constraints

        bit2 = ClassGroup.objects.create(name='BIT Year 2', size=35)
        bce1 = ClassGroup.objects.create(name='BCE Year 1', size=28)

        Course.objects.create(code='BIT201', title='Python Programming',
                              lecturer=francis, class_group=bit2, sessions_per_week=2)
        Course.objects.create(code='BIT202', title='Databases',
                              lecturer=ada, class_group=bit2, sessions_per_week=2)
        Course.objects.create(code='BIT203', title='Web Development',
                              lecturer=kojo, class_group=bit2, sessions_per_week=3)
        Course.objects.create(code='BCE101', title='Intro to Computing',
                              lecturer=ada, class_group=bce1, sessions_per_week=2)
        Course.objects.create(code='BCE102', title='Mathematics',
                              lecturer=kojo, class_group=bce1, sessions_per_week=2)

        self.stdout.write(self.style.SUCCESS(
            "Demo data loaded. Run `python manage.py runserver` and click Generate."))
