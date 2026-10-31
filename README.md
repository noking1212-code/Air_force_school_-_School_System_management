# Airforce School

Airforce School is a custom-written Flask and MySQL demo website for a Class 12 school management project. It is fictional and is not an official Indian Air Force website. Separate accounts cover students, teachers, parents, visitors, and administrators.

The site includes a saved light/dark theme switch, responsive layouts for phone, tablet, laptop, and desktop screens, student ID cards, report-card PDFs, attendance summaries, a demo fee guide, class timetables, homework, and a library catalogue with loan tracking.

## Start locally

1. Back up the configured database in MySQL Workbench before applying changes.
2. Select the same database the app uses (`DB_NAME` in `.env`, usually `gradesphere`).
3. For a new database, run `schema.sql`. If you created the older tables earlier, back up and restore-verify the database, then run any unapplied migrations in order: `001_calendar_attendance.sql`, `002_school_demo.sql`, and `003_school_features.sql`.
4. If the school tables already exist, back up and verify a restore before applying `003_school_features.sql`. This adds profile fields and feature tables without deleting existing records. The app never runs schema changes automatically.
5. Keep database values in local `.env` settings. `DB_HOST` is the MySQL server address; `DB_PASSWORD` is the account password. For a Vercel deployment, set each `DB_*` value in that Vercel project’s environment settings to point to a network-accessible database; `127.0.0.1` only refers to the same computer running the app.
6. Install `requirements.txt` if needed. It includes ReportLab for downloadable report-card PDFs.
7. Load the demo campus: `python seed_demo.py`. Add class, section, guardian, and demo fee details through the administrator pages; no personal profile or fee amounts are invented by the seed script.
8. Run `python app.py` and open `http://127.0.0.1:5000`.

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
- **Student:** own ID card, results and report PDFs, attendance summary, class timetable and homework, library loans, fees, calendar, and school notices.
- **Teacher:** student attendance, individual or class batch marks, report PDFs, homework posts, assigned timetable, fees, calendar, and school notices.
- **Parent:** linked students’ ID cards, results and report PDFs, attendance summaries, timetables, homework, and library loans; fee guide, calendar, and school notices.
- **Administrator:** people and student profiles, parent links, both attendance registers, individual or batch marks, report PDFs, fee guide, timetable, library catalogue and loans, homework, notices, and contact inbox.

Exam dates can include an optional PDF up to 10 MB.
