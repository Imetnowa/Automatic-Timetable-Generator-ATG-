from django import forms
from .models import ClassGroup, Course, Lecturer, Room, TimeSlot


class TimeSlotForm(forms.ModelForm):
    class Meta:
        model = TimeSlot
        fields = ['day', 'start_time', 'end_time']
        widgets = {
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
        }


class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = ['name', 'capacity']


class LecturerForm(forms.ModelForm):
    class Meta:
        model = Lecturer
        fields = ['name', 'email', 'available_slots']
        widgets = {'available_slots': forms.CheckboxSelectMultiple}


class ClassGroupForm(forms.ModelForm):
    class Meta:
        model = ClassGroup
        fields = ['name', 'size']


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['code', 'title', 'lecturer', 'class_group', 'sessions_per_week']
