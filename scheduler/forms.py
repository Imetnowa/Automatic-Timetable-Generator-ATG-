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
        fields = ['name', 'size', 'mess_window']
        widgets = {
            'mess_window': forms.TextInput(attrs={
                'placeholder': 'e.g. 12:00-13:00'
            }),
        }


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = [
            'code', 'title', 'lecturer', 'class_group',
            'sessions_per_week', 'credit_hours', 'contact_hours', 'blocked_days',
        ]
        widgets = {
            'blocked_days': forms.TextInput(attrs={
                'placeholder': 'e.g. MON,FRI'
            }),
        }