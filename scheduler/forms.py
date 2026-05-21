from django import forms
from .models import ClassGroup, Course, Lecturer, Room, TimeSlot, DAYS_OF_WEEK


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
    blocked_days = forms.MultipleChoiceField(
        choices=DAYS_OF_WEEK,
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )

    class Meta:
        model = Course
        fields = [
            'code', 'title', 'lecturer', 'class_group',
            'sessions_per_week', 'credit_hours', 'contact_hours', 'blocked_days',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Pre-populate checkboxes when editing an existing instance
        if self.instance and self.instance.blocked_days:
            self.initial['blocked_days'] = [
                d.strip() for d in self.instance.blocked_days.split(',') if d.strip()
            ]

    def clean_blocked_days(self):
        # Convert the list ['MON', 'FRI'] back to 'MON,FRI' for storage
        days = self.cleaned_data.get('blocked_days', [])
        return ','.join(days)