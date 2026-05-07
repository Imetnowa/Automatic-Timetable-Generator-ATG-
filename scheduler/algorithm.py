"""
Timetable scheduling engine.

Strategy: most-constrained-first ordering + greedy assignment +
backtracking. Constraints enforced:

- Lecturer not double-booked
- Room not double-booked
- Class group not double-booked
- Lecturer is available in the chosen time slot (if availability set)
- Room capacity >= class group size
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

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
    unscheduled: List[Tuple[int, int]] = field(default_factory=list)  # (course_id, session_index)

    @property
    def success(self) -> bool:
        return not self.unscheduled


def _candidate_slots_for_lecturer(lecturer, all_slot_ids: List[int]) -> Set[int]:
    avail = list(lecturer.available_slots.values_list('id', flat=True))
    if not avail:
        return set(all_slot_ids)
    return set(avail)


def _candidate_rooms_for_group(group_size: int, rooms) -> List[int]:
    return [r.id for r in rooms if r.capacity >= group_size]


def generate_timetable() -> GenerationResult:
    courses = list(Course.objects.select_related('lecturer', 'class_group').all())
    timeslots = list(TimeSlot.objects.all())
    rooms = list(Room.objects.all())

    if not courses or not timeslots or not rooms:
        return GenerationResult(unscheduled=[(c.id, 0) for c in courses])

    all_slot_ids = [t.id for t in timeslots]

    # Build per-course candidate (timeslot, room) lists
    sessions: List[dict] = []  # one entry per session instance
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

    # Most constrained first
    sessions.sort(key=lambda s: len(s['candidates']))

    used_lecturer: Set[Tuple[int, int]] = set()  # (lecturer_id, slot_id)
    used_room: Set[Tuple[int, int]] = set()      # (room_id, slot_id)
    used_group: Set[Tuple[int, int]] = set()     # (group_id, slot_id)
    used_course_slot: Set[Tuple[int, int]] = set()  # avoid same course twice in same slot

    result = GenerationResult()

    def backtrack(i: int) -> bool:
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
            # assign
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
            # undo
            used_lecturer.discard((c.lecturer_id, slot_id))
            used_room.discard((room_id, slot_id))
            used_group.discard((c.class_group_id, slot_id))
            used_course_slot.discard((c.id, slot_id))
            result.assignments.pop()
        return False

    if not backtrack(0):
        # Fall back: greedy best-effort, mark remainder as unscheduled
        result.assignments.clear()
        used_lecturer.clear(); used_room.clear(); used_group.clear(); used_course_slot.clear()
        for s in sessions:
            c = s['course']
            placed = False
            for slot_id, room_id in s['candidates']:
                if (c.lecturer_id, slot_id) in used_lecturer: continue
                if (room_id, slot_id) in used_room: continue
                if (c.class_group_id, slot_id) in used_group: continue
                if (c.id, slot_id) in used_course_slot: continue
                used_lecturer.add((c.lecturer_id, slot_id))
                used_room.add((room_id, slot_id))
                used_group.add((c.class_group_id, slot_id))
                used_course_slot.add((c.id, slot_id))
                result.assignments.append(Assignment(
                    course_id=c.id, lecturer_id=c.lecturer_id,
                    class_group_id=c.class_group_id,
                    timeslot_id=slot_id, room_id=room_id,
                ))
                placed = True
                break
            if not placed:
                result.unscheduled.append((c.id, s['session_index']))

    return result


def persist_result(result: GenerationResult) -> int:
    """Replace previous schedule with new one. Returns count saved."""
    ScheduledSession.objects.all().delete()
    objs = [
        ScheduledSession(course_id=a.course_id, timeslot_id=a.timeslot_id, room_id=a.room_id)
        for a in result.assignments
    ]
    ScheduledSession.objects.bulk_create(objs)
    return len(objs)
