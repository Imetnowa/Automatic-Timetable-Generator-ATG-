import math
import random
from datetime import time
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from .models import Course, Room, ScheduledSession, TimeSlot


def parse_blocked_days(blocked_days):
    if not blocked_days:
        return set()
    return {d.strip().upper() for d in blocked_days.split(",") if d.strip()}


def parse_time_window(window):
    start_str, end_str = window.split("-")
    sh, sm = start_str.strip().split(":")
    eh, em = end_str.strip().split(":")
    return time(int(sh), int(sm)), time(int(eh), int(em))


def overlaps_mess(slot_start, slot_end, mess_window):
    if not mess_window:
        return False
    mess_start, mess_end = parse_time_window(mess_window)
    return slot_start < mess_end and mess_start < slot_end


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


def _sessions_for_course(course):
    return max(1, math.ceil(course.contact_hours / 2))


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
    slot_day = {t.id: t.day for t in timeslots}
    slot_times = {t.id: (t.start_time, t.end_time) for t in timeslots}

    sessions = []
    for c in courses:
        blocked = parse_blocked_days(c.blocked_days)
        mess = c.class_group.mess_window
        slot_ids = _candidate_slots_for_lecturer(c.lecturer, all_slot_ids)
        slot_ids = {
            sid for sid in slot_ids
            if slot_day[sid] not in blocked
            and not overlaps_mess(slot_times[sid][0], slot_times[sid][1], mess)
        }
        room_ids = _candidate_rooms_for_group(c.class_group.size, rooms)
        candidates = [(s, r) for s in slot_ids for r in room_ids]
        num_sessions = _sessions_for_course(c)
        for i in range(num_sessions):
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


def schedule_genetic(
    population_size: int = 50,
    generations: int = 100,
    mutation_rate: float = 0.1,
    tournament_size: int = 3,
    elite_count: int = 2,
    seed: int = None,
) -> GenerationResult:
    if seed is not None:
        random.seed(seed)

    sessions, _all_slot_ids, empty = _build_sessions()
    if empty:
        return GenerationResult(algorithm='genetic')

    no_candidate = [s for s in sessions if not s['candidates']]
    schedulable = [s for s in sessions if s['candidates']]

    if not schedulable:
        result = GenerationResult(algorithm='genetic')
        for s in no_candidate:
            result.unscheduled.append((s['course'].id, s['session_index']))
        return result

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

    population = [
        [random.choice(s['candidates']) for s in schedulable]
        for _ in range(population_size)
    ]

    best_chromo = None
    best_fitness = float('inf')

    for _gen in range(generations):
        scored = sorted(
            ((c, _ga_fitness(c, schedulable, slot_info, day_slot_index)) for c in population),
            key=lambda x: x[1],
        )

        if scored[0][1] < best_fitness:
            best_fitness = scored[0][1]
            best_chromo = scored[0][0]

        next_pop = [c for c, _ in scored[:elite_count]]
        while len(next_pop) < population_size:
            p1 = _ga_tournament(scored, tournament_size)
            p2 = _ga_tournament(scored, tournament_size)
            child = [g1 if random.random() < 0.5 else g2 for g1, g2 in zip(p1, p2)]
            child = [
                random.choice(s['candidates']) if random.random() < mutation_rate else g
                for g, s in zip(child, schedulable)
            ]
            next_pop.append(child)
        population = next_pop

    return _ga_chromo_to_result(best_chromo, schedulable, no_candidate)


def _ga_fitness(chromo, sessions, slot_info, day_slot_index):
    used_lecturer = set()
    used_room = set()
    used_group = set()
    used_course_slot = set()
    violations = 0

    group_day_indices = {}
    course_day_count = {}

    for s, (slot_id, room_id) in zip(sessions, chromo):
        c = s['course']
        l_key = (c.lecturer_id, slot_id)
        r_key = (room_id, slot_id)
        g_key = (c.class_group_id, slot_id)
        cs_key = (c.id, slot_id)
        if l_key in used_lecturer:
            violations += 1
        else:
            used_lecturer.add(l_key)
        if r_key in used_room:
            violations += 1
        else:
            used_room.add(r_key)
        if g_key in used_group:
            violations += 1
        else:
            used_group.add(g_key)
        if cs_key in used_course_slot:
            violations += 1
        else:
            used_course_slot.add(cs_key)

        day = slot_info[slot_id][0]
        idx = day_slot_index[day][slot_id]
        group_day_indices.setdefault((c.class_group_id, day), []).append(idx)
        ck = (c.id, day)
        course_day_count[ck] = course_day_count.get(ck, 0) + 1

    compactness = 0
    for indices in group_day_indices.values():
        if len(indices) > 1:
            compactness += (max(indices) - min(indices) + 1) - len(indices)
    spread = sum(max(0, n - 1) for n in course_day_count.values())

    return violations * 1000 + compactness + spread


def _ga_tournament(scored, k):
    competitors = random.sample(scored, min(k, len(scored)))
    competitors.sort(key=lambda x: x[1])
    return competitors[0][0]


def _ga_chromo_to_result(chromo, sessions, no_candidate):
    result = GenerationResult(algorithm='genetic')
    used_lecturer = set()
    used_room = set()
    used_group = set()
    used_course_slot = set()

    for s, (slot_id, room_id) in zip(sessions, chromo):
        c = s['course']
        l_key = (c.lecturer_id, slot_id)
        r_key = (room_id, slot_id)
        g_key = (c.class_group_id, slot_id)
        cs_key = (c.id, slot_id)
        if (l_key in used_lecturer or r_key in used_room
                or g_key in used_group or cs_key in used_course_slot):
            result.unscheduled.append((c.id, s['session_index']))
            continue
        used_lecturer.add(l_key)
        used_room.add(r_key)
        used_group.add(g_key)
        used_course_slot.add(cs_key)
        result.assignments.append(Assignment(
            course_id=c.id,
            lecturer_id=c.lecturer_id,
            class_group_id=c.class_group_id,
            timeslot_id=slot_id,
            room_id=room_id,
        ))

    for s in no_candidate:
        result.unscheduled.append((s['course'].id, s['session_index']))

    return result


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