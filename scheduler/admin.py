from django.contrib import admin
from .models import Course, ClassGroup, Lecturer, Room, ScheduledSession, TimeSlot

admin.site.register(TimeSlot)
admin.site.register(Room)
admin.site.register(ClassGroup)
admin.site.register(ScheduledSession)


@admin.register(Lecturer)
class LecturerAdmin(admin.ModelAdmin):
    list_display = ('name', 'email')
    filter_horizontal = ('available_slots',)


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('code', 'title', 'lecturer', 'class_group', 'sessions_per_week')
    list_filter = ('lecturer', 'class_group')
