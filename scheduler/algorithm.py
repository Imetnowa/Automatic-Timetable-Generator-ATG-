from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from .models import Course, Room, ScheduledSession, TimeSlot


@dataclass
class Assignment:
    course_id: int
    lecturer_id: int
    class_group_id: int
    timeslot_id: int
    room_id: int


@dataclass
class GenerationResult:
    assignments: List[Assignment] = field(default_factory=list)
    unscheduled: List[Tuple[int, int]] = field(default_factory=list)
    algorithm: str = ""

    @property
    def success(self) -> bool:
        return not self.unscheduled


def _candidate_slots_for_lecturer(lecturer, all_slot_ids):
    avail = list(lecturer.available_slots.values_list('id', flat=True))
    if not avail:
        return set(all_slot_ids)
    return set(avail)


def _candidate_rooms_for_group(group_size, rooms):
    return [r.id for r in rooms if r.capacity >= group_size]


def _build_sessions():
    courses = list(Course.objects.select_related('lecturer', 'class_group').all())
    timeslots = list(TimeSlot.objects.all())
    rooms = list(Room.objects.all())

    if not courses or not timeslots or not rooms:
        return [], [], True

    all_slot_ids = [t.id for t in timeslots]

    sessions = []
    for c in courses:
        slot_ids = _candidate_slots_for_lecturer(c.lecturer, all_slot_ids)
        room_ids = _candidate_rooms_for_group(c.class_group.size, rooms)
        candidates = [(s, r) for s in slot_ids for r in room_ids]
        for i in range(c.sessions_per_week):
            sessions.append({
                'course': c,
                'session_index': i,
                'candidates': list(candidates),
            })

    sessions.sort(key=lambda s: len(s['candidates']))
    return sessions, all_slot_ids, False


def schedule_greedy() -> GenerationResult:
    result = GenerationResult(algorithm='greedy')
    sessions, _all_slot_ids, empty = _build_sessions()
    if empty:
        return result

    used_lecturer = set()
    used_room = set()
    used_group = set()
    used_course_slot = set()

    for s in sessions:
        c = s['course']
        placed = False
        for slot_id, room_id in s['candidates']:
            if (c.lecturer_id, slot_id) in used_lecturer:
                continue
            if (room_id, slot_id) in used_room:
                continue
            if (c.class_group_id, slot_id) in used_group:
                continue
            if (c.id, slot_id) in used_course_slot:
                continue
            used_lecturer.add((c.lecturer_id, slot_id))
            used_room.add((room_id, slot_id))
            used_group.add((c.class_group_id, slot_id))
            used_course_slot.add((c.id, slot_id))
            result.assignments.append(Assignment(
                course_id=c.id,
                lecturer_id=c.lecturer_id,
                class_group_id=c.class_group_id,
                timeslot_id=slot_id,
                room_id=room_id,
            ))
            placed = True
            break
        if not placed:
            result.unscheduled.append((c.id, s['session_index']))
    return result


def schedule_backtracking() -> GenerationResult:
    result = GenerationResult(algorithm='backtracking')
    sessions, _all_slot_ids, empty = _build_sessions()
    if empty:
        return result

    used_lecturer = set()
    used_room = set()
    used_group = set()
    used_course_slot = set()

    def backtrack(i):
        if i == len(sessions):
            return True
        s = sessions[i]
        c = s['course']
        for slot_id, room_id in s['candidates']:
            if (c.lecturer_id, slot_id) in used_lecturer:
                continue
            if (room_id, slot_id) in used_room:
                continue
            if (c.class_group_id, slot_id) in used_group:
                continue
            if (c.id, slot_id) in used_course_slot:
                continue
            used_lecturer.add((c.lecturer_id, slot_id))
            used_room.add((room_id, slot_id))
            used_group.add((c.class_group_id, slot_id))
            used_course_slot.add((c.id, slot_id))
            result.assignments.append(Assignment(
                course_id=c.id,
                lecturer_id=c.lecturer_id,
                class_group_id=c.class_group_id,
                timeslot_id=slot_id,
                room_id=room_id,
            ))
            if backtrack(i + 1):
                return True
            used_lecturer.discard((c.lecturer_id, slot_id))
            used_room.discard((room_id, slot_id))
            used_group.discard((c.class_group_id, slot_id))
            used_course_slot.discard((c.id, slot_id))
            result.assignments.pop()
        return False

    if backtrack(0):
        return result

    fallback = schedule_greedy()
    fallback.algorithm = 'backtracking (greedy fallback)'
    return fallback


def score_schedule(assignments) -> Dict[str, int]:
    if not assignments:
        return {'compactness': 0, 'spread': 0, 'total': 0}

    slot_info = {t.id: (t.day, t.start_time) for t in TimeSlot.objects.all()}

    day_slot_order = {}
    for sid, (day, _start) in slot_info.items():
        day_slot_order.setdefault(day, []).append(sid)
    for day, sids in day_slot_order.items():
        sids.sort(key=lambda sid: slot_info[sid][1])
    day_slot_index = {
        day: {sid: i for i, sid in enumerate(sids)}
        for day, sids in day_slot_order.items()
    }

    group_day_used = {}
    for a in assignments:
        day, _start = slot_info[a.timeslot_id]
        idx = day_slot_index[day][a.timeslot_id]
        group_day_used.setdefault((a.class_group_id, day), []).append(idx)

    compactness = 0
    for indices in group_day_used.values():
        if len(indices) <= 1:
            continue
        compactness += (max(indices) - min(indices) + 1) - len(indices)

    course_day_count = {}
    for a in assignments:
        day, _start = slot_info[a.timeslot_id]
        key = (a.course_id, day)
        course_day_count[key] = course_day_count.get(key, 0) + 1
    spread = sum(max(0, n - 1) for n in course_day_count.values())

    return {
        'compactness': compactness,
        'spread': spread,
        'total': compactness + spread,
    }


def generate_timetable() -> GenerationResult:
    return schedule_backtracking()


def persist_result(result):
    ScheduledSession.objects.all().delete()
    objs = [
        ScheduledSession(course_id=a.course_id, timeslot_id=a.timeslot_id, room_id=a.room_id)
        for a in result.assignments
    ]
    ScheduledSession.objects.bulk_create(objs)
    return len(objs)