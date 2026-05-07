from django.db import models

DAYS_OF_WEEK = [
    ('MON', 'Monday'),
    ('TUE', 'Tuesday'),
    ('WED', 'Wednesday'),
    ('THU', 'Thursday'),
    ('FRI', 'Friday'),
]


class TimeSlot(models.Model):
    day = models.CharField(max_length=3, choices=DAYS_OF_WEEK)
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        unique_together = ('day', 'start_time', 'end_time')
        ordering = ['day', 'start_time']

    def __str__(self):
        return f"{self.get_day_display()} {self.start_time:%H:%M}-{self.end_time:%H:%M}"


class Room(models.Model):
    name = models.CharField(max_length=64, unique=True)
    capacity = models.PositiveIntegerField(default=30)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} (cap {self.capacity})"


class Lecturer(models.Model):
    name = models.CharField(max_length=128)
    email = models.EmailField(blank=True)
    available_slots = models.ManyToManyField(
        TimeSlot,
        blank=True,
        help_text="Time slots when this lecturer is available. Leave empty = always available.",
    )

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class ClassGroup(models.Model):
    name = models.CharField(max_length=64, unique=True,
                            help_text="e.g. 'BIT Year 2', 'BCE Year 1'")
    size = models.PositiveIntegerField(default=30)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.size})"


class Course(models.Model):
    code = models.CharField(max_length=16, unique=True)
    title = models.CharField(max_length=128)
    lecturer = models.ForeignKey(Lecturer, on_delete=models.CASCADE,
                                 related_name='courses')
    class_group = models.ForeignKey(ClassGroup, on_delete=models.CASCADE,
                                    related_name='courses')
    sessions_per_week = models.PositiveIntegerField(
        default=2,
        help_text="Number of weekly sessions to schedule for this course.",
    )

    class Meta:
        ordering = ['code']

    def __str__(self):
        return f"{self.code} — {self.title}"


class ScheduledSession(models.Model):
    """Result of a generation run."""
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    timeslot = models.ForeignKey(TimeSlot, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)

    class Meta:
        ordering = ['timeslot__day', 'timeslot__start_time']

    def __str__(self):
        return f"{self.course.code} @ {self.timeslot} in {self.room.name}"
