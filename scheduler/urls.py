from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('manage/', views.manage_data, name='manage_data'),

    path('timeslots/add/', views.timeslot_create, name='timeslot_create'),
    path('timeslots/<int:pk>/delete/', views.timeslot_delete, name='timeslot_delete'),

    path('rooms/add/', views.room_create, name='room_create'),
    path('rooms/<int:pk>/delete/', views.room_delete, name='room_delete'),

    path('lecturers/add/', views.lecturer_create, name='lecturer_create'),
    path('lecturers/<int:pk>/delete/', views.lecturer_delete, name='lecturer_delete'),

    path('groups/add/', views.group_create, name='group_create'),
    path('groups/<int:pk>/delete/', views.group_delete, name='group_delete'),

    path('courses/add/', views.course_create, name='course_create'),
    path('courses/<int:pk>/delete/', views.course_delete, name='course_delete'),

    path('generate/', views.generate, name='generate'),
    path('timetable/', views.timetable_view, name='timetable'),
    path('export/csv/', views.export_csv, name='export_csv'),
    path('export/pdf/', views.export_pdf, name='export_pdf'),
]
