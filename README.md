# Automatic Timetable Generator (ATG)

A Django web application that automatically generates conflict-free academic
timetables, based on the project proposal by Awontemi Wepeh Akwolaga, Prince
Geraldo, and Ezekiel Divine Momo (Regional Maritime University, Python
Programming, supervised by Mr. Francis Anlimah).

## Features

- Manage **Courses**, **Lecturers**, **Rooms**, **Time slots**, and **Class
  Groups** through a clean web UI and the Django admin.
- **Automatic timetable generation** using a greedy + backtracking scheduling
  algorithm.
- **Conflict-free allocation** — no lecturer, room, or class group is ever
  double-booked.
- **Constraint handling** — lecturer availability per time slot, room capacity
  vs. class group size, and required sessions per week per course.
- **Visualization** — view the generated timetable as a structured weekly grid.
- **Export** — download the timetable as **CSV** or **PDF**.
- **Regenerate** at any time when constraints change.

## Tech Stack

- Python 3.10+
- Django 4.2+
- SQLite (default, zero-config)
- ReportLab (PDF export)

## Quick Start

```bash
# 1. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Apply migrations and load demo data
python manage.py migrate
python manage.py seed_demo        # optional: loads sample courses/lecturers

# 4. (Optional) create an admin user
python manage.py createsuperuser

# 5. Run the server
python manage.py runserver
```

Open http://127.0.0.1:8000/ in your browser.

## Usage

1. **Add data** — go to *Manage Data* and create rooms, time slots, lecturers,
   class groups, and courses (each course links a lecturer + class group and
   declares how many sessions per week it needs).
2. **Generate** — click *Generate Timetable*. The scheduler tries every course
   session against the constraints and reports unscheduled sessions, if any.
3. **View** — the generated timetable is shown as a Day × Time grid for each
   class group, lecturer, and room.
4. **Export** — download the current timetable as CSV or PDF.

## Scheduling Algorithm

`scheduler/algorithm.py` implements a constraint-satisfaction scheduler:

1. Sort course sessions by *most constrained first* (fewest available time
   slots × room candidates).
2. Greedy assignment of each session to the first feasible (timeslot, room)
   pair.
3. Backtracking when an assignment makes a later session infeasible.
4. Constraints checked at every step:
   - Lecturer not double-booked
   - Room not double-booked
   - Class group not double-booked
   - Lecturer is available in that timeslot
   - Room capacity ≥ class group size

## Project Layout

```
atg/
├── manage.py
├── requirements.txt
├── timetable_project/        # Django project (settings, urls, wsgi)
└── scheduler/                # Main app
    ├── models.py             # Domain entities
    ├── algorithm.py          # Greedy + backtracking scheduler
    ├── views.py              # Web views (CRUD, generate, export)
    ├── forms.py
    ├── urls.py
    ├── admin.py
    ├── templates/scheduler/  # HTML templates
    └── management/commands/  # `seed_demo`, `generate_timetable`
```

## License

MIT — feel free to adapt for academic or production use.
