from datetime import time

from django.test import TestCase

from scheduler.algorithm import (
    Assignment,
    schedule_backtracking,
    schedule_genetic,
    schedule_greedy,
    score_schedule,
)
from scheduler.models import ClassGroup, Course, Lecturer, Room, TimeSlot


def _make_world():
    days = ['MON', 'TUE', 'WED', 'THU', 'FRI']
    times = [
        (time(8, 0), time(10, 0)),
        (time(10, 0), time(12, 0)),
        (time(13, 0), time(15, 0)),
        (time(15, 0), time(17, 0)),
    ]
    slots = []
    for d in days:
        for s, e in times:
            slots.append(TimeSlot.objects.create(day=d, start_time=s, end_time=e))
    room = Room.objects.create(name='R1', capacity=40)
    lec = Lecturer.objects.create(name='L1')
    grp = ClassGroup.objects.create(name='G1', size=30)
    return slots, room, lec, grp


def _make_courses(grp, lec, codes_with_counts):
    courses = []
    for code, n in codes_with_counts:
        c = Course.objects.create(
            code=code, title=code, lecturer=lec, class_group=grp, sessions_per_week=n
        )
        courses.append(c)
    return courses


class ScoreScheduleTests(TestCase):
    def test_empty(self):
        self.assertEqual(score_schedule([]), {'compactness': 0, 'spread': 0, 'total': 0})

    def test_compactness_counts_gaps(self):
        slots, room, lec, grp = _make_world()
        course = Course.objects.create(
            code='C1', title='T', lecturer=lec, class_group=grp, sessions_per_week=2
        )
        # Mon 8-10 and Mon 1-3: one empty slot (10-12) between them.
        assignments = [
            Assignment(course.id, lec.id, grp.id, slots[0].id, room.id),
            Assignment(course.id, lec.id, grp.id, slots[2].id, room.id),
        ]
        self.assertEqual(score_schedule(assignments)['compactness'], 1)

    def test_spread_counts_same_day_duplicates(self):
        slots, room, lec, grp = _make_world()
        course = Course.objects.create(
            code='C1', title='T', lecturer=lec, class_group=grp, sessions_per_week=2
        )
        # Both sessions on Monday: 1 duplicate.
        assignments = [
            Assignment(course.id, lec.id, grp.id, slots[0].id, room.id),
            Assignment(course.id, lec.id, grp.id, slots[1].id, room.id),
        ]
        self.assertEqual(score_schedule(assignments)['spread'], 1)


class AlgorithmFeasibilityTests(TestCase):
    def setUp(self):
        slots, room, lec, grp = _make_world()
        _make_courses(grp, lec, [('A', 2), ('B', 2), ('C', 2)])

    def _assert_feasible(self, result):
        self.assertEqual(len(result.unscheduled), 0)
        used_lecturer = set()
        used_room = set()
        used_group = set()
        for a in result.assignments:
            self.assertNotIn((a.lecturer_id, a.timeslot_id), used_lecturer)
            self.assertNotIn((a.room_id, a.timeslot_id), used_room)
            self.assertNotIn((a.class_group_id, a.timeslot_id), used_group)
            used_lecturer.add((a.lecturer_id, a.timeslot_id))
            used_room.add((a.room_id, a.timeslot_id))
            used_group.add((a.class_group_id, a.timeslot_id))

    def test_greedy_feasible(self):
        result = schedule_greedy()
        self.assertEqual(result.algorithm, 'greedy')
        self._assert_feasible(result)

    def test_backtracking_feasible(self):
        result = schedule_backtracking()
        self.assertIn('backtracking', result.algorithm)
        self._assert_feasible(result)

    def test_genetic_feasible(self):
        result = schedule_genetic(seed=42, generations=50, population_size=30)
        self.assertEqual(result.algorithm, 'genetic')
        self._assert_feasible(result)


class GeneticImprovesSpreadTests(TestCase):
    def setUp(self):
        slots, room, lec, grp = _make_world()
        _make_courses(grp, lec, [('A', 2), ('B', 2), ('C', 2)])

    def test_genetic_score_no_worse_than_greedy(self):
        greedy_score = score_schedule(schedule_greedy().assignments)['total']
        genetic_score = score_schedule(
            schedule_genetic(seed=42, generations=100, population_size=50).assignments
        )['total']
        self.assertLessEqual(genetic_score, greedy_score)