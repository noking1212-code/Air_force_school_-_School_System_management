"""Airforce School: a role-based Flask school management website."""
import calendar as month_calendar
import os
import uuid
from datetime import date
from functools import wraps

import mysql.connector
from dotenv import load_dotenv
from flask import Flask, abort, flash, redirect, render_template, request, send_from_directory, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("GRADESPHERE_SECRET") or os.urandom(32)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024 + 64 * 1024
app.config["EXAM_UPLOAD_FOLDER"] = os.getenv(
    "EXAM_UPLOAD_FOLDER", os.path.join(app.instance_path, "exam_uploads")
)

ROLES = {"student", "teacher", "parent", "visitor", "administrator"}
SCHOOL_ROLES = {"student", "teacher", "parent", "administrator"}


def get_db():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "gradesphere"),
    )


@app.context_processor
def inject_today():
    return {"today": date.today()}


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Sign in to open your dashboard.", "info")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


def role_required(*roles):
    def decorate(view):
        @wraps(view)
        @login_required
        def wrapped(*args, **kwargs):
            if session.get("role") not in roles:
                flash("This area is not available for your account.", "error")
                return redirect(url_for("dashboard"))
            return view(*args, **kwargs)
        return wrapped
    return decorate


def fetch_notices(include_school):
    connection = get_db()
    cursor = connection.cursor(dictionary=True)
    if include_school:
        cursor.execute(
            "SELECT n.id, n.title, n.body, n.visibility, n.created_at, u.full_name FROM notices n "
            "JOIN users u ON u.id = n.created_by ORDER BY n.created_at DESC"
        )
    else:
        cursor.execute(
            "SELECT n.id, n.title, n.body, n.visibility, n.created_at, u.full_name FROM notices n "
            "JOIN users u ON u.id = n.created_by WHERE n.visibility = 'public' ORDER BY n.created_at DESC"
        )
    rows = cursor.fetchall()
    cursor.close()
    connection.close()
    return rows


@app.route("/")
def home():
    notices = fetch_notices(False)[:3]
    return render_template("home.html", notices=notices)


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/notices")
def public_notices():
    include_school = session.get("role") in SCHOOL_ROLES
    return render_template(
        "notices.html",
        notices=fetch_notices(include_school),
        include_school=include_school,
        nav="notices",
    )


@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        message = request.form.get("message", "").strip()
        if not name or not email or not message or len(message) > 4000 or len(name) > 120:
            flash("Enter your name, email, and a message of up to 4,000 characters.", "error")
        else:
            connection = get_db()
            cursor = connection.cursor()
            cursor.execute(
                "INSERT INTO contact_messages (full_name, email, message) VALUES (%s, %s, %s)",
                (name, email, message),
            )
            connection.commit()
            cursor.close()
            connection.close()
            flash("Your message was sent to the school office.", "success")
            return redirect(url_for("contact"))
    return render_template("contact.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        connection = get_db()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, full_name, email, password_hash, role FROM users WHERE email = %s AND active = TRUE",
            (email,),
        )
        user = cursor.fetchone()
        cursor.close()
        connection.close()
        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["name"] = user["full_name"]
            session["role"] = user["role"]
            session["email"] = user["email"]
            return redirect(url_for("dashboard"))
        flash("That email and password did not match an active account.", "error")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You are signed out.", "success")
    return redirect(url_for("home"))


@app.route("/dashboard")
@login_required
def dashboard():
    role = session["role"]
    connection = get_db()
    cursor = connection.cursor(dictionary=True)
    if role == "administrator":
        cursor.execute("SELECT role, COUNT(*) AS total FROM users WHERE active = TRUE GROUP BY role")
        counts = {row["role"]: row["total"] for row in cursor.fetchall()}
        cursor.execute("SELECT id, full_name, email, role, created_at FROM users ORDER BY created_at DESC LIMIT 8")
        recent = cursor.fetchall()
        cursor.execute("SELECT COUNT(*) AS total FROM contact_messages")
        inbox = cursor.fetchone()["total"]
        data = {"counts": counts, "recent": recent, "inbox": inbox}
    elif role == "student":
        cursor.execute(
            "SELECT subject_name, score, max_score, term FROM results WHERE student_id = %s ORDER BY id DESC LIMIT 6",
            (session["user_id"],),
        )
        data = {"results": cursor.fetchall()}
    elif role == "teacher":
        cursor.execute(
            "SELECT id, full_name, email FROM users WHERE role = 'student' AND active = TRUE ORDER BY full_name LIMIT 8"
        )
        data = {"students": cursor.fetchall()}
    elif role == "parent":
        cursor.execute(
            "SELECT u.full_name, r.subject_name, r.score, r.max_score, r.term FROM parent_students ps "
            "JOIN users u ON u.id = ps.student_id LEFT JOIN results r ON r.student_id = u.id "
            "WHERE ps.parent_id = %s ORDER BY r.id DESC LIMIT 8",
            (session["user_id"],),
        )
        data = {"children_results": cursor.fetchall()}
    else:
        data = {}
    cursor.close()
    connection.close()
    data["notices"] = fetch_notices(role in SCHOOL_ROLES)[:5]
    return render_template("dashboard.html", data=data, nav="overview", today=date.today())


@app.route("/people", methods=["GET", "POST"])
@role_required("administrator")
def people():
    connection = get_db()
    cursor = connection.cursor(dictionary=True)
    if request.method == "POST":
        action = request.form.get("action", "create")
        if action == "create":
            name = request.form.get("full_name", "").strip()
            email = request.form.get("email", "").strip().lower()
            role = request.form.get("role", "")
            password = request.form.get("password", "")
            if not name or not email or role not in ROLES or len(password) < 8:
                flash("Enter a name, email, valid role, and a password of at least 8 characters.", "error")
            else:
                try:
                    cursor.execute(
                        "INSERT INTO users (full_name, email, password_hash, role) VALUES (%s, %s, %s, %s)",
                        (name, email, generate_password_hash(password), role),
                    )
                    connection.commit()
                    flash("Account created.", "success")
                except mysql.connector.IntegrityError:
                    connection.rollback()
                    flash("That email is already registered.", "error")
        elif action == "link":
            try:
                parent_id = int(request.form.get("parent_id", "0"))
                student_id = int(request.form.get("student_id", "0"))
            except (TypeError, ValueError):
                parent_id = student_id = 0
            cursor.execute("SELECT id FROM users WHERE id = %s AND role = 'parent' AND active = TRUE", (parent_id,))
            parent = cursor.fetchone()
            cursor.execute("SELECT id FROM users WHERE id = %s AND role = 'student' AND active = TRUE", (student_id,))
            student = cursor.fetchone()
            if not parent or not student:
                flash("Choose an active parent and an active student.", "error")
            else:
                try:
                    cursor.execute(
                        "INSERT INTO parent_students (parent_id, student_id) VALUES (%s, %s)",
                        (parent_id, student_id),
                    )
                    connection.commit()
                    flash("Parent linked to student.", "success")
                except mysql.connector.IntegrityError:
                    connection.rollback()
                    flash("That parent and student are already linked.", "error")
        elif action == "unlink":
            try:
                parent_id = int(request.form.get("parent_id", "0"))
                student_id = int(request.form.get("student_id", "0"))
            except (TypeError, ValueError):
                parent_id = student_id = 0
            cursor.execute(
                "DELETE FROM parent_students WHERE parent_id = %s AND student_id = %s",
                (parent_id, student_id),
            )
            connection.commit()
            flash("Parent link removed." if cursor.rowcount else "That link was not found.", "info")
        elif action == "toggle":
            try:
                user_id = int(request.form.get("user_id", "0"))
            except (TypeError, ValueError):
                user_id = 0
            if user_id == session["user_id"]:
                flash("You cannot deactivate your own account.", "error")
            else:
                cursor.execute("SELECT id, active FROM users WHERE id = %s", (user_id,))
                person = cursor.fetchone()
                if not person:
                    flash("Account not found.", "error")
                else:
                    cursor.execute("UPDATE users SET active = %s WHERE id = %s", (not person["active"], user_id))
                    connection.commit()
                    flash("Account deactivated." if person["active"] else "Account reactivated.", "success")
    cursor.execute("SELECT id, full_name, email, role, active FROM users ORDER BY role, full_name")
    rows = cursor.fetchall()
    cursor.execute(
        "SELECT p.id AS parent_id, p.full_name AS parent_name, s.id AS student_id, s.full_name AS student_name "
        "FROM parent_students ps JOIN users p ON p.id = ps.parent_id JOIN users s ON s.id = ps.student_id "
        "ORDER BY p.full_name, s.full_name"
    )
    links = cursor.fetchall()
    cursor.close()
    connection.close()
    parents = [row for row in rows if row["role"] == "parent" and row["active"]]
    students = [row for row in rows if row["role"] == "student" and row["active"]]
    return render_template("people.html", people=rows, links=links, parents=parents, students=students, nav="people")


@app.route("/results", methods=["GET", "POST"])
@role_required("administrator", "teacher")
def results():
    connection = get_db()
    cursor = connection.cursor(dictionary=True)
    if request.method == "POST":
        try:
            student_id = int(request.form.get("student_id", "0"))
            score = float(request.form.get("score", "-1"))
            maximum = float(request.form.get("max_score", "0"))
            subject = request.form.get("subject_name", "").strip()
            term = request.form.get("term", "").strip()
            if not subject or not term or maximum <= 0 or score < 0 or score > maximum:
                raise ValueError
            cursor.execute(
                "INSERT INTO results (student_id, subject_name, score, max_score, term, entered_by) "
                "SELECT id, %s, %s, %s, %s, %s FROM users WHERE id = %s AND role = 'student'",
                (subject, score, maximum, term, session["user_id"], student_id),
            )
            if cursor.rowcount:
                connection.commit()
                flash("Result saved.", "success")
            else:
                flash("Choose a valid student account.", "error")
        except (ValueError, TypeError):
            flash("Check the result details and score range.", "error")
    cursor.execute("SELECT id, full_name FROM users WHERE role = 'student' AND active = TRUE ORDER BY full_name")
    students = cursor.fetchall()
    cursor.execute(
        "SELECT r.subject_name, r.score, r.max_score, r.term, u.full_name FROM results r "
        "JOIN users u ON u.id = r.student_id ORDER BY r.id DESC LIMIT 30"
    )
    rows = cursor.fetchall()
    cursor.close()
    connection.close()
    return render_template("results.html", students=students, results=rows, nav="results")


@app.route("/results/mine")
@role_required("student", "parent")
def my_results():
    connection = get_db()
    cursor = connection.cursor(dictionary=True)
    if session["role"] == "student":
        cursor.execute(
            "SELECT r.subject_name, r.score, r.max_score, r.term, u.full_name FROM results r "
            "JOIN users u ON u.id = r.student_id WHERE r.student_id = %s ORDER BY r.id DESC",
            (session["user_id"],),
        )
    else:
        cursor.execute(
            "SELECT r.subject_name, r.score, r.max_score, r.term, u.full_name FROM parent_students ps "
            "JOIN users u ON u.id = ps.student_id JOIN results r ON r.student_id = u.id "
            "WHERE ps.parent_id = %s ORDER BY r.id DESC",
            (session["user_id"],),
        )
    rows = cursor.fetchall()
    cursor.close()
    connection.close()
    return render_template("results_mine.html", results=rows, is_parent=session["role"] == "parent", nav="my_results")


@app.route("/notices/manage", methods=["GET", "POST"])
@role_required("administrator")
def manage_notices():
    connection = get_db()
    cursor = connection.cursor(dictionary=True)
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        body = request.form.get("body", "").strip()
        visibility = request.form.get("visibility", "")
        if not title or len(title) > 160 or not body or len(body) > 4000 or visibility not in ("public", "school"):
            flash("Enter a title, a message, and whether the notice is public or for school accounts.", "error")
        else:
            cursor.execute(
                "INSERT INTO notices (title, body, visibility, created_by) VALUES (%s, %s, %s, %s)",
                (title, body, visibility, session["user_id"]),
            )
            connection.commit()
            flash("Notice published.", "success")
            cursor.close()
            connection.close()
            return redirect(url_for("manage_notices"))
    cursor.execute(
        "SELECT n.id, n.title, n.body, n.visibility, n.created_at, u.full_name FROM notices n "
        "JOIN users u ON u.id = n.created_by ORDER BY n.created_at DESC"
    )
    rows = cursor.fetchall()
    cursor.close()
    connection.close()
    return render_template("notices_manage.html", notices=rows, nav="notices_manage")


@app.route("/notices/delete/<int:notice_id>", methods=["POST"])
@role_required("administrator")
def delete_notice(notice_id):
    connection = get_db()
    cursor = connection.cursor()
    cursor.execute("DELETE FROM notices WHERE id = %s", (notice_id,))
    removed = cursor.rowcount
    connection.commit()
    cursor.close()
    connection.close()
    flash("Notice removed." if removed else "Notice not found.", "info")
    return redirect(url_for("manage_notices"))


@app.route("/inbox")
@role_required("administrator")
def contact_inbox():
    connection = get_db()
    cursor = connection.cursor(dictionary=True)
    cursor.execute(
        "SELECT id, full_name, email, message, created_at FROM contact_messages ORDER BY created_at DESC"
    )
    messages = cursor.fetchall()
    cursor.close()
    connection.close()
    return render_template("inbox.html", messages=messages, nav="inbox")


def save_pdf(upload):
    """Save a small PDF using a server-generated name; return stored and display names."""
    if not upload or not upload.filename:
        return None
    display_name = secure_filename(upload.filename)[:255]
    if not display_name or not display_name.lower().endswith(".pdf"):
        raise ValueError("Attach a PDF file for an exam date.")
    upload.stream.seek(0, os.SEEK_END)
    file_size = upload.stream.tell()
    upload.stream.seek(0)
    if file_size > 10 * 1024 * 1024:
        raise ValueError("Exam PDF files must be 10 MB or smaller.")
    header = upload.stream.read(5)
    upload.stream.seek(0)
    if header != b"%PDF-":
        raise ValueError("The attached file is not a valid PDF.")
    os.makedirs(app.config["EXAM_UPLOAD_FOLDER"], exist_ok=True)
    stored_name = uuid.uuid4().hex + ".pdf"
    upload.save(os.path.join(app.config["EXAM_UPLOAD_FOLDER"], stored_name))
    return stored_name, display_name


def calendar_event_values(form):
    title = form.get("title", "").strip()
    event_type = form.get("event_type", "")
    description = form.get("description", "").strip()
    try:
        event_day = date.fromisoformat(form.get("event_date", ""))
    except ValueError:
        raise ValueError("Choose a valid calendar date.")
    if not title or len(title) > 120:
        raise ValueError("Enter a title of up to 120 characters.")
    if event_type not in ("holiday", "event", "exam"):
        raise ValueError("Choose a holiday, school event, or exam date.")
    if len(description) > 4000:
        raise ValueError("The description must be 4,000 characters or fewer.")
    if not form.get("event_date"):
        raise ValueError("Choose a calendar date.")
    return title, event_type, event_day, description


@app.route("/calendar", methods=["GET", "POST"])
@role_required("administrator", "teacher", "student", "parent")
def school_calendar():
    if request.method == "POST":
        if session.get("role") != "administrator":
            abort(403)
        stored_file = None
        try:
            title, event_type, event_day, description = calendar_event_values(request.form)
            upload = request.files.get("attachment")
            if upload and upload.filename and event_type != "exam":
                raise ValueError("PDF attachments are only available for exam dates.")
            if upload and upload.filename:
                stored_file = save_pdf(upload)
            connection = get_db()
            cursor = connection.cursor()
            cursor.execute(
                "INSERT INTO calendar_events (title, event_type, event_date, description, attachment_file, attachment_name, created_by) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (
                    title, event_type, event_day, description,
                    stored_file[0] if stored_file else None,
                    stored_file[1] if stored_file else None,
                    session["user_id"],
                ),
            )
            connection.commit()
            cursor.close()
            connection.close()
            flash("Calendar entry added.", "success")
            return redirect(url_for("school_calendar", year=event_day.year, month=event_day.month))
        except ValueError as error:
            if stored_file:
                try:
                    os.remove(os.path.join(app.config["EXAM_UPLOAD_FOLDER"], stored_file[0]))
                except OSError:
                    pass
            flash(str(error), "error")
        except mysql.connector.Error:
            if stored_file:
                try:
                    os.remove(os.path.join(app.config["EXAM_UPLOAD_FOLDER"], stored_file[0]))
                except OSError:
                    pass
            raise

    today_value = date.today()
    try:
        year = int(request.args.get("year", today_value.year))
        month = int(request.args.get("month", today_value.month))
        if month < 1 or month > 12 or year < 1900 or year > 2100:
            raise ValueError
    except (TypeError, ValueError):
        year, month = today_value.year, today_value.month
    first_day = date(year, month, 1)
    last_day = date(year, month, month_calendar.monthrange(year, month)[1])
    connection = get_db()
    cursor = connection.cursor(dictionary=True)
    cursor.execute(
        "SELECT id, title, event_type, event_date, description, attachment_name FROM calendar_events "
        "WHERE event_date BETWEEN %s AND %s ORDER BY event_date, title",
        (first_day, last_day),
    )
    events = cursor.fetchall()
    cursor.close()
    connection.close()
    events_by_day = {}
    for item in events:
        events_by_day.setdefault(item["event_date"], []).append(item)
    weeks = []
    for week in month_calendar.Calendar(firstweekday=0).monthdatescalendar(year, month):
        weeks.append([
            {"date": day, "in_month": day.month == month, "events": events_by_day.get(day, [])}
            for day in week
        ])
    prev_year, prev_month = (year - 1, 12) if month == 1 else (year, month - 1)
    next_year, next_month = (year + 1, 1) if month == 12 else (year, month + 1)
    return render_template(
        "calendar.html", weeks=weeks, year=year, month=month,
        month_name=month_calendar.month_name[month],
        prev_year=prev_year, prev_month=prev_month,
        next_year=next_year, next_month=next_month,
        is_admin=session.get("role") == "administrator",
        nav="calendar",
    )


@app.route("/calendar/edit/<int:event_id>", methods=["GET", "POST"])
@role_required("administrator")
def edit_calendar_event(event_id):
    connection = get_db()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM calendar_events WHERE id = %s", (event_id,))
    event = cursor.fetchone()
    if not event:
        cursor.close()
        connection.close()
        abort(404)
    if request.method == "POST":
        new_file = None
        try:
            title, event_type, event_day, description = calendar_event_values(request.form)
            upload = request.files.get("attachment")
            if upload and upload.filename and event_type != "exam":
                raise ValueError("PDF attachments are only available for exam dates.")
            if upload and upload.filename:
                new_file = save_pdf(upload)
            stored_file = new_file or (event["attachment_file"], event["attachment_name"])
            if event_type != "exam":
                stored_file = (None, None)
            cursor.execute(
                "UPDATE calendar_events SET title = %s, event_type = %s, event_date = %s, description = %s, "
                "attachment_file = %s, attachment_name = %s WHERE id = %s",
                (title, event_type, event_day, description, stored_file[0], stored_file[1], event_id),
            )
            connection.commit()
            cursor.close()
            connection.close()
            if event.get("attachment_file") and event.get("attachment_file") != stored_file[0]:
                try:
                    os.remove(os.path.join(app.config["EXAM_UPLOAD_FOLDER"], event["attachment_file"]))
                except OSError:
                    pass
            flash("Calendar entry updated.", "success")
            return redirect(url_for("school_calendar", year=event_day.year, month=event_day.month))
        except ValueError as error:
            if new_file:
                try:
                    os.remove(os.path.join(app.config["EXAM_UPLOAD_FOLDER"], new_file[0]))
                except OSError:
                    pass
            flash(str(error), "error")
    cursor.close()
    connection.close()
    return render_template("calendar_form.html", event=event, nav="calendar")


@app.route("/calendar/delete/<int:event_id>", methods=["POST"])
@role_required("administrator")
def delete_calendar_event(event_id):
    connection = get_db()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT attachment_file FROM calendar_events WHERE id = %s", (event_id,))
    event = cursor.fetchone()
    if event:
        cursor.execute("DELETE FROM calendar_events WHERE id = %s", (event_id,))
        connection.commit()
    cursor.close()
    connection.close()
    if event and event["attachment_file"]:
        try:
            os.remove(os.path.join(app.config["EXAM_UPLOAD_FOLDER"], event["attachment_file"]))
        except OSError:
            pass
    flash("Calendar entry removed." if event else "Calendar entry not found.", "info")
    return redirect(url_for("school_calendar"))


@app.route("/calendar/files/<int:event_id>")
@role_required("administrator", "teacher", "student", "parent")
def exam_attachment(event_id):
    connection = get_db()
    cursor = connection.cursor(dictionary=True)
    cursor.execute(
        "SELECT attachment_file, attachment_name FROM calendar_events WHERE id = %s AND event_type = 'exam'",
        (event_id,),
    )
    event = cursor.fetchone()
    cursor.close()
    connection.close()
    if not event or not event["attachment_file"]:
        abort(404)
    return send_from_directory(
        app.config["EXAM_UPLOAD_FOLDER"], event["attachment_file"],
        as_attachment=True, download_name=event["attachment_name"],
    )


def attendance_date_from_request():
    value = request.values.get("date", "")
    try:
        return date.fromisoformat(value) if value else date.today()
    except ValueError:
        return date.today()


def save_daily_attendance(cursor, table, person_role, record_date, recorded_by, prefix):
    person_column = "student_id" if person_role == "student" else "teacher_id"
    cursor.execute("SELECT id FROM users WHERE role = %s AND active = TRUE", (person_role,))
    valid_ids = {row["id"] for row in cursor.fetchall()}
    statuses = {}
    for key, value in request.form.items():
        if key.startswith(prefix):
            try:
                person_id = int(key[len(prefix):])
            except ValueError:
                raise ValueError("Invalid account in attendance form.")
            if person_id not in valid_ids:
                raise ValueError("Choose a current account in the attendance form.")
            if value == "":
                continue
            if value not in ("present", "absent"):
                raise ValueError("Choose Present or Absent for a current account.")
            statuses[person_id] = value
    if not statuses:
        raise ValueError("Mark at least one person Present or Absent.")
    for person_id, status in statuses.items():
        cursor.execute(
            f"INSERT INTO {table} ({person_column}, attendance_date, status, recorded_by, updated_by) "
            "VALUES (%s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE status = VALUES(status), "
            "updated_by = VALUES(updated_by), updated_at = CURRENT_TIMESTAMP",
            (person_id, record_date, status, recorded_by, recorded_by),
        )
    return len(statuses)


@app.route("/attendance/students", methods=["GET", "POST"])
@role_required("administrator", "teacher")
def student_attendance():
    record_date = attendance_date_from_request()
    connection = get_db()
    cursor = connection.cursor(dictionary=True)
    if request.method == "POST":
        try:
            marked = save_daily_attendance(
                cursor, "student_attendance", "student", record_date,
                session["user_id"], "student_",
            )
            connection.commit()
            flash(f"Student attendance saved for {record_date.isoformat()} ({marked} records).", "success")
        except ValueError as error:
            connection.rollback()
            flash(str(error), "error")
    cursor.execute("SELECT id, full_name, email FROM users WHERE role = 'student' AND active = TRUE ORDER BY full_name")
    students = cursor.fetchall()
    cursor.execute("SELECT student_id, status FROM student_attendance WHERE attendance_date = %s", (record_date,))
    statuses = {row["student_id"]: row["status"] for row in cursor.fetchall()}
    cursor.execute(
        "SELECT a.attendance_date, a.status, u.full_name FROM student_attendance a "
        "JOIN users u ON u.id = a.student_id WHERE a.attendance_date = %s ORDER BY u.full_name",
        (record_date,),
    )
    recent = cursor.fetchall()
    cursor.close()
    connection.close()
    return render_template(
        "attendance_mark.html", people=students, statuses=statuses,
        record_date=record_date, attendance_kind="student",
        title="Student attendance", recent=recent, nav="student_attendance",
    )


@app.route("/attendance/teachers", methods=["GET", "POST"])
@role_required("administrator")
def teacher_attendance():
    record_date = attendance_date_from_request()
    connection = get_db()
    cursor = connection.cursor(dictionary=True)
    if request.method == "POST":
        try:
            marked = save_daily_attendance(
                cursor, "teacher_attendance", "teacher", record_date,
                session["user_id"], "teacher_",
            )
            connection.commit()
            flash(f"Teacher attendance saved for {record_date.isoformat()} ({marked} records).", "success")
        except ValueError as error:
            connection.rollback()
            flash(str(error), "error")
    cursor.execute("SELECT id, full_name, email FROM users WHERE role = 'teacher' AND active = TRUE ORDER BY full_name")
    teachers = cursor.fetchall()
    cursor.execute("SELECT teacher_id, status FROM teacher_attendance WHERE attendance_date = %s", (record_date,))
    statuses = {row["teacher_id"]: row["status"] for row in cursor.fetchall()}
    cursor.execute(
        "SELECT a.attendance_date, a.status, u.full_name FROM teacher_attendance a "
        "JOIN users u ON u.id = a.teacher_id WHERE a.attendance_date = %s ORDER BY u.full_name",
        (record_date,),
    )
    recent = cursor.fetchall()
    cursor.close()
    connection.close()
    return render_template(
        "attendance_mark.html", people=teachers, statuses=statuses,
        record_date=record_date, attendance_kind="teacher",
        title="Teacher attendance", recent=recent, nav="teacher_attendance",
    )


@app.route("/attendance/my")
@role_required("student", "parent")
def my_attendance():
    connection = get_db()
    cursor = connection.cursor(dictionary=True)
    if session["role"] == "student":
        cursor.execute(
            "SELECT a.attendance_date, a.status, u.full_name FROM student_attendance a "
            "JOIN users u ON u.id = a.student_id WHERE a.student_id = %s ORDER BY a.attendance_date DESC LIMIT 90",
            (session["user_id"],),
        )
    else:
        cursor.execute(
            "SELECT a.attendance_date, a.status, u.full_name FROM parent_students ps "
            "JOIN student_attendance a ON a.student_id = ps.student_id JOIN users u ON u.id = a.student_id "
            "WHERE ps.parent_id = %s ORDER BY a.attendance_date DESC, u.full_name LIMIT 180",
            (session["user_id"],),
        )
    rows = cursor.fetchall()
    cursor.close()
    connection.close()
    return render_template(
        "attendance_my.html", attendance=rows,
        is_parent=session["role"] == "parent", nav="my_attendance",
    )


@app.errorhandler(413)
def upload_too_large(error):
    flash("Exam PDF files must be 10 MB or smaller.", "error")
    return redirect(url_for("school_calendar")), 303


if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG", "false").lower() == "true")
