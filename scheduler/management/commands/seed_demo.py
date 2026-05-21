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
        nii = Lecturer.objects.create(name='Capt. Nii Armah', email='nii@rmu.edu')

        # Francis available Mon-Wed only; the rest are unconstrained.
        francis.available_slots.set(slots[:12])

        bit2 = ClassGroup.objects.create(name='BIT Year 2', size=35)
        bce1 = ClassGroup.objects.create(name='BCE Year 1', size=28)
        # Cadet group: mess 11:00-12:00, so the 10:00-12:00 slot is unavailable to them.
        marine1 = ClassGroup.objects.create(name='Marine Eng Year 1', size=25,
                                            mess_window='11:00-12:00')

        # Number of sessions = ceil(contact_hours / 2).
        Course.objects.create(code='BIT201', title='Python Programming',
                              lecturer=francis, class_group=bit2,
                              credit_hours=3, contact_hours=5)   # 3 sessions
        Course.objects.create(code='BIT202', title='Databases',
                              lecturer=ada, class_group=bit2,
                              credit_hours=3, contact_hours=4,    # 2 sessions
                              blocked_days='WED')                 # never on Wednesday
        Course.objects.create(code='BIT203', title='Web Development',
                              lecturer=kojo, class_group=bit2,
                              credit_hours=3, contact_hours=4)    # 2 sessions
        Course.objects.create(code='BCE101', title='Intro to Computing',
                              lecturer=ada, class_group=bce1,
                              credit_hours=3, contact_hours=3)    # 2 sessions
        Course.objects.create(code='BCE102', title='Mathematics',
                              lecturer=kojo, class_group=bce1,
                              credit_hours=3, contact_hours=3)    # 2 sessions
        Course.objects.create(code='MAR101', title='Marine Engineering Fundamentals',
                              lecturer=nii, class_group=marine1,
                              credit_hours=3, contact_hours=4)    # 2 sessions
        Course.objects.create(code='MAR102', title='Navigation',
                              lecturer=nii, class_group=marine1,
                              credit_hours=3, contact_hours=4)    # 2 sessions

        self.stdout.write(self.style.SUCCESS(
            "Demo data loaded. BIT201 has 5 contact hours (3 sessions), "
            "BIT202 is blocked on Wednesday, and Marine Eng Year 1 has an "
            "11:00-12:00 mess window. Run the server and click Generate."))