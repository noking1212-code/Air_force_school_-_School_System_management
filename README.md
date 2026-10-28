# Airforce School

Airforce School is a custom-written Flask and MySQL demo website for a Class 12 school management project. It is fictional and is not an official Indian Air Force website. Separate accounts cover students, teachers, parents, visitors, and administrators.

The site includes a saved light/dark theme switch and responsive layouts for phone, tablet, laptop, and desktop screens.

## Start locally

1. Back up the configured database in MySQL Workbench before applying changes.
2. Select the same database the app uses (`DB_NAME` in `.env`, usually `gradesphere`).
3. For a new database, run `schema.sql` (it now includes notices, contact messages, calendar, and attendance). If you created the older tables earlier, run `migrations/001_calendar_attendance.sql` then `migrations/002_school_demo.sql` instead of re-running the full schema.
4. If the earlier school tables already exist, back up first, then run any migrations you have not applied yet, including `002_school_demo.sql`. The app never runs schema changes automatically. Styles and scripts are local files only (no Bootstrap or font CDNs).
5. Keep your existing local `.env` settings (`DB_*` and `GRADESPHERE_SECRET`). Install `requirements.txt` if needed.
6. Load the demo campus: `python seed_demo.py`.
7. Run `python app.py` and open `http://127.0.0.1:5000`.

## Demo logins

All demo accounts use the password `Airforce@123`.

| Role | Email |
| --- | --- |
| Administrator / principal | `principal@airforceschool.demo` |
| Teacher | `teacher@airforceschool.demo` |
| Student | `student@airforceschool.demo` |
| Parent (linked to the demo student) | `parent@airforceschool.demo` |
| Visitor | `visitor@airforceschool.demo` |

The seed script is safe to run more than once. It creates missing demo users and fills empty notices, results, calendar, attendance, and contact samples.

To add another administrator without the seed password, run `python create_admin.py`.

## What each role can do

- **Visitor (no login or visitor account):** home, about, public notices, contact form. No marks or attendance.
- **Student:** own results, own attendance, calendar, school notices.
- **Teacher:** student attendance, enter results, calendar, school notices.
- **Parent:** results and attendance only for linked students, calendar, school notices.
- **Administrator:** people (create, deactivate, parent links), both attendance registers, results, calendar, publish notices, contact inbox.

Exam dates can include an optional PDF up to 10 MB.
