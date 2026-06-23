# Automatic Timetable Generator (ATG)

A Django web application that automatically generates conflict-free academic
timetables, based on the project proposal by Awontemi Wepeh Akwolaga, Prince
Geraldo, and Ezekiel Divine Momo (Regional Maritime University, Python
Programming, supervised by Mr. Francis Anlimah).

## Features

- Manage **Courses**, **Lecturers**, **Rooms**, **Time Slots**, and **Class
  Groups** through a clean web UI and the Django admin.
- **Automatic timetable generation** using a three-algorithm scheduling
  pipeline: Greedy, Backtracking, and Genetic.
- **Conflict-free allocation** — no lecturer, room, or class group is ever
  double-booked.
- **Constraint handling** — lecturer availability per time slot, room capacity
  vs. class group size, blocked days per course, and mess/break windows per
  class group.
- **Visualization** — view the generated timetable as a structured weekly grid
  per class group.
- **Export** — download the timetable as **CSV** or **PDF**.
- **Regenerate** at any time when constraints change.

## Tech Stack

- Python 3.10+
- Django 4.2+
- SQLite (default, zero-config, managed via Django ORM migrations)
- ReportLab (PDF export)
- Tailwind CSS (responsive web UI, loaded via CDN)

## Quick Start

```bash
# 1. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Apply migrations
python manage.py migrate

# 4. (Optional) Load demo data — realistic dataset with constraints
python manage.py seed_demo

# (Optional) Load stress dataset — tight lecturer windows for visible algorithm differences
python manage.py seed_stress

# 5. (Optional) Create an admin user
python manage.py createsuperuser

# 6. Run the server
python manage.py runserver
```

Open http://127.0.0.1:8000/ in your browser.

## Usage

1. **Add data** — go to *Manage Data* and create rooms, time slots, lecturers,
   class groups, and courses. Each course links a lecturer and a class group,
   and declares `contact_hours` (the scheduler derives the number of weekly
   sessions as `ceil(contact_hours / 2)`). Optionally set `blocked_days` per
   course and a `mess_window` per class group to exclude specific time windows.
2. **Generate** — click *Generate Timetable*. The scheduler runs backtracking
   against all constraints and reports any unscheduled sessions.
3. **View** — the generated timetable is shown as a Day × Time grid per class
   group.
4. **Export** — download the current timetable as CSV or PDF.
5. **Regenerate** — click *Regenerate* after changing any constraints or data.

You can also generate from the command line:

```bash
python manage.py generate_timetable
```

## Scheduling Algorithm

`scheduler/algorithm.py` implements a three-stage constraint-satisfaction
scheduler:

### 1. Greedy (fast initial allocation / fallback)

- Sort course sessions by *most constrained first* (fewest feasible
  slot × room candidate pairs).
- Assign each session to the first feasible `(timeslot, room)` pair.
- Used as a fallback if backtracking cannot find a complete solution.

### 2. Backtracking (default)

- Same candidate ordering as greedy.
- On each assignment, recursively attempts to place all remaining sessions.
- Rolls back and tries the next candidate if a later session becomes
  infeasible.
- Falls back to greedy if no complete solution is found.

### 3. Genetic Algorithm (optional optimiser)

- Encodes a full schedule as a chromosome (one `(slot, room)` gene per
  session).
- Fitness function penalises hard-constraint violations (×1000 each) and
  soft-constraint violations (compactness gaps and same-day course repeats).
- Evolves the population via tournament selection, single-point crossover,
  and random mutation.
- Elitism preserves the best individuals across generations.
- Returns the lowest-fitness feasible chromosome found.

### Constraints checked at every step

- Lecturer not double-booked in the same time slot
- Room not double-booked in the same time slot
- Class group not double-booked in the same time slot
- Same course not placed twice in the same time slot
- Lecturer is available in that time slot (if availability is set)
- Room capacity ≥ class group size
- Time slot day not in the course's `blocked_days`
- Time slot does not overlap the class group's `mess_window`

## Running Tests

```bash
python manage.py test scheduler
```

Tests live in `scheduler/tests.py`. The suite covers algorithm feasibility
(all three algorithms produce conflict-free schedules), constraint enforcement
(blocked days, mess windows, contact-hours-driven session counts), schedule
scoring (compactness and spread metrics), and helper functions
(`parse_blocked_days`, `overlaps_mess`).

## Project Layout

```
AUTOMATIC-TIMETABLE-GENERATOR-ATG-/
├── manage.py
├── requirements.txt
├── README.md
├── timetable_project/          # Django project (settings, urls, wsgi, asgi)
└── scheduler/                  # Main app
    ├── models.py               # Domain entities (Course, Lecturer, Room, etc.)
    ├── algorithm.py            # Greedy + Backtracking + Genetic scheduler
    ├── views.py                # Web views (CRUD, generate, export CSV/PDF)
    ├── forms.py                # ModelForms for all entities
    ├── urls.py                 # URL routing
    ├── admin.py                # Django admin registrations
    ├── tests.py                # Unit tests (feasibility, constraints, scoring)
    ├── templatetags/
    │   └── dict_extras.py      # Custom template filter (get_item)
    ├── templates/scheduler/    # HTML templates (base, dashboard, manage, timetable)
    ├── migrations/             # Django database migrations
    └── management/commands/
        ├── seed_demo.py        # Loads a realistic demo dataset
        ├── seed_stress.py      # Loads a tight-constraint stress dataset
        └── generate_timetable.py  # CLI timetable generation
```

## License

MIT — feel free to adapt for academic or production use.