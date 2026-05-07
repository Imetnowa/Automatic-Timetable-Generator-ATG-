import csv
from io import BytesIO

from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from .algorithm import generate_timetable, persist_result
from .forms import (ClassGroupForm, CourseForm, LecturerForm, RoomForm,
                    TimeSlotForm)
from .models import (DAYS_OF_WEEK, ClassGroup, Course, Lecturer, Room,
                     ScheduledSession, TimeSlot)


def dashboard(request):
    ctx = {
        'counts': {
            'courses': Course.objects.count(),
            'lecturers': Lecturer.objects.count(),
            'rooms': Room.objects.count(),
            'groups': ClassGroup.objects.count(),
            'timeslots': TimeSlot.objects.count(),
            'scheduled': ScheduledSession.objects.count(),
        }
    }
    return render(request, 'scheduler/dashboard.html', ctx)


def manage_data(request):
    ctx = {
        'timeslots': TimeSlot.objects.all(),
        'rooms': Room.objects.all(),
        'lecturers': Lecturer.objects.all(),
        'groups': ClassGroup.objects.all(),
        'courses': Course.objects.select_related('lecturer', 'class_group').all(),
        'timeslot_form': TimeSlotForm(),
        'room_form': RoomForm(),
        'lecturer_form': LecturerForm(),
        'group_form': ClassGroupForm(),
        'course_form': CourseForm(),
    }
    return render(request, 'scheduler/manage.html', ctx)


def _create(request, form_cls, redirect_to='manage_data'):
    if request.method == 'POST':
        form = form_cls(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Saved.")
        else:
            messages.error(request, f"Validation error: {form.errors.as_text()}")
    return redirect(redirect_to)


def _delete(request, model, pk, redirect_to='manage_data'):
    obj = get_object_or_404(model, pk=pk)
    obj.delete()
    messages.success(request, "Deleted.")
    return redirect(redirect_to)


def timeslot_create(request): return _create(request, TimeSlotForm)
def timeslot_delete(request, pk): return _delete(request, TimeSlot, pk)
def room_create(request): return _create(request, RoomForm)
def room_delete(request, pk): return _delete(request, Room, pk)
def lecturer_create(request): return _create(request, LecturerForm)
def lecturer_delete(request, pk): return _delete(request, Lecturer, pk)
def group_create(request): return _create(request, ClassGroupForm)
def group_delete(request, pk): return _delete(request, ClassGroup, pk)
def course_create(request): return _create(request, CourseForm)
def course_delete(request, pk): return _delete(request, Course, pk)


def generate(request):
    result = generate_timetable()
    saved = persist_result(result)
    if result.success:
        messages.success(request, f"Generated {saved} sessions with no conflicts.")
    else:
        messages.warning(
            request,
            f"Generated {saved} sessions. {len(result.unscheduled)} could not be scheduled "
            "due to constraints — try adding more time slots or rooms."
        )
    return redirect('timetable')


def _grid_data():
    """Build {group_name: {day: {slot_label: 'COURSE — Room'}}}"""
    sessions = ScheduledSession.objects.select_related(
        'course', 'course__lecturer', 'course__class_group', 'timeslot', 'room'
    ).all()
    timeslots = list(TimeSlot.objects.all())
    slot_labels = sorted({(t.start_time, t.end_time) for t in timeslots})
    slot_labels = [f"{s:%H:%M}-{e:%H:%M}" for s, e in slot_labels]
    days = [d for d, _ in DAYS_OF_WEEK]

    groups = {}
    for s in sessions:
        gname = s.course.class_group.name
        groups.setdefault(gname, {d: {sl: '' for sl in slot_labels} for d in days})
        slot_label = f"{s.timeslot.start_time:%H:%M}-{s.timeslot.end_time:%H:%M}"
        cell = f"{s.course.code} — {s.room.name}<br><small>{s.course.lecturer.name}</small>"
        groups[gname][s.timeslot.day][slot_label] = cell
    return {'groups': groups, 'slot_labels': slot_labels, 'days': DAYS_OF_WEEK}


def timetable_view(request):
    ctx = _grid_data()
    return render(request, 'scheduler/timetable.html', ctx)


def export_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="timetable.csv"'
    writer = csv.writer(response)
    writer.writerow(['Class Group', 'Day', 'Start', 'End', 'Course Code', 'Course Title',
                     'Lecturer', 'Room'])
    for s in ScheduledSession.objects.select_related(
        'course', 'course__lecturer', 'course__class_group', 'timeslot', 'room'
    ):
        writer.writerow([
            s.course.class_group.name,
            s.timeslot.get_day_display(),
            s.timeslot.start_time.strftime('%H:%M'),
            s.timeslot.end_time.strftime('%H:%M'),
            s.course.code, s.course.title,
            s.course.lecturer.name, s.room.name,
        ])
    return response


def export_pdf(request):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import (Paragraph, SimpleDocTemplate, Spacer, Table,
                                    TableStyle)

    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4), title="Timetable")
    styles = getSampleStyleSheet()
    story = [Paragraph("Automatic Timetable Generator — Schedule", styles['Title']), Spacer(1, 12)]

    data = _grid_data()
    for group_name, by_day in data['groups'].items():
        story.append(Paragraph(f"<b>Class Group: {group_name}</b>", styles['Heading2']))
        header = ['Time'] + [label for _, label in data['days']]
        rows = [header]
        for slot in data['slot_labels']:
            row = [slot]
            for day_code, _ in data['days']:
                cell = by_day.get(day_code, {}).get(slot, '') or ''
                cell = cell.replace('<br>', '\n').replace('<small>', '').replace('</small>', '')
                row.append(cell)
            rows.append(row)
        t = Table(rows, repeatRows=1)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E2761')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('GRID', (0, 0), (-1, -1), 0.4, colors.grey),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(t)
        story.append(Spacer(1, 16))

    if not data['groups']:
        story.append(Paragraph("No timetable generated yet.", styles['Normal']))

    doc.build(story)
    pdf = buf.getvalue(); buf.close()
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="timetable.pdf"'
    return response
