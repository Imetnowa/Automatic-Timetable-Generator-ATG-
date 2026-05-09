from datetime import time
from django.core.management.base import BaseCommand
from scheduler.models import (ClassGroup, Course, Lecturer, Room, TimeSlot,
                              ScheduledSession)


class Command(BaseCommand):
    help = "Stress dataset: tight lecturer windows and dense scheduling for visible algorithm differences."

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
        slots_by_day = {
            d: [TimeSlot.objects.create(day=d, start_time=s, end_time=e)
                for s, e in slot_times]
            for d in days
        }

        Room.objects.create(name='Room A101', capacity=40)
        Room.objects.create(name='Room B202', capacity=60)

        francis = Lecturer.objects.create(name='Mr. Francis Anlimah')
        ada = Lecturer.objects.create(name='Dr. Ada Mensah')
        kojo = Lecturer.objects.create(name='Mr. Kojo Boateng')
        joana = Lecturer.objects.create(name='Ms. Joana Owusu')

        francis.available_slots.set(slots_by_day['MON'] + slots_by_day['TUE'])
        ada.available_slots.set(slots_by_day['WED'] + slots_by_day['THU'][:2])
        kojo.available_slots.set(slots_by_day['FRI'] + slots_by_day['MON'][:2])
        afternoons = []
        for d in days:
            afternoons.extend(slots_by_day[d][2:])
        joana.available_slots.set(afternoons)

        bit2 = ClassGroup.objects.create(name='BIT Year 2', size=35)
        bce1 = ClassGroup.objects.create(name='BCE Year 1', size=28)
        bbm1 = ClassGroup.objects.create(name='BBM Year 1', size=50)

        Course.objects.create(code='BIT201', title='Python Programming',
                              lecturer=francis, class_group=bit2, sessions_per_week=3)
        Course.objects.create(code='BIT202', title='Databases',
                              lecturer=ada, class_group=bit2, sessions_per_week=2)
        Course.objects.create(code='BIT203', title='Web Development',
                              lecturer=kojo, class_group=bit2, sessions_per_week=2)
        Course.objects.create(code='BCE101', title='Intro to Computing',
                              lecturer=ada, class_group=bce1, sessions_per_week=2)
        Course.objects.create(code='BCE102', title='Mathematics',
                              lecturer=kojo, class_group=bce1, sessions_per_week=2)
        Course.objects.create(code='BBM101', title='Accounting',
                              lecturer=francis, class_group=bbm1, sessions_per_week=2)
        Course.objects.create(code='BBM102', title='Statistics',
                              lecturer=joana, class_group=bbm1, sessions_per_week=2)
        Course.objects.create(code='BBM103', title='Management',
                              lecturer=ada, class_group=bbm1, sessions_per_week=1)

        self.stdout.write(self.style.SUCCESS(
            "Stress data loaded: 16 sessions, 4 lecturers (tight windows), 3 groups, 2 rooms."
        ))
