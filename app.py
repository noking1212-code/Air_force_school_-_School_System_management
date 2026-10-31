"""Airforce School: a role-based Flask school management website."""
import calendar as month_calendar
import html
import os
import uuid
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from functools import wraps
from io import BytesIO

import mysql.connector
from dotenv import load_dotenv
from flask import Flask, abort, flash, redirect, render_template, request, send_file, send_from_directory, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("GRADESPHERE_SECRET") or os.urandom(32)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024 + 64 * 1024
app.config["EXAM_UPLOAD_FOLDER"] = os.getenv(
    "EXAM_UPLOAD_FOLDER", os.path.join(app.instance_path, "exam_uploads")
)
app.config["STUDENT_PHOTO_FOLDER"] = os.getenv(
    "STUDENT_PHOTO_FOLDER", os.path.join(app.instance_path, "student_photos")
)

ROLES = {"student", "teacher", "parent", "visitor", "administrator"}
SCHOOL_ROLES = {"student", "teacher", "parent", "administrator"}
PHOTO_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


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


def fetch_notices(include_school, query="", audience=""):
    connection = get_db()
    cursor = connection.cursor(dictionary=True)
    conditions = []
    values = []
    if not include_school:
        conditions.append("n.visibility = 'public'")
    elif audience in ("public", "school"):
        conditions.append("n.visibility = %s")
        values.append(audience)
    query = query.strip()[:100]
    if query:
        conditions.append("(n.title LIKE %s OR n.body LIKE %s)")
        values.extend([f"%{query}%", f"%{query}%"])
    sql = (
        "SELECT n.id, n.title, n.body, n.visibility, n.created_at, u.full_name FROM notices n "
        "JOIN users u ON u.id = n.created_by"
    )
    if conditions:
        sql += " WHERE " + " AND ".join(conditions)
    cursor.execute(sql + " ORDER BY n.created_at DESC", values)
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
    query = request.args.get("q", "").strip()[:100]
    audience = request.args.get("audience", "") if include_school else ""
    return render_template(
        "notices.html",
        notices=fetch_notices(include_school, query, audience),
        include_school=include_school,
        query=query,
        audience=audience,
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
        latest_results = cursor.fetchall()
        cursor.execute(
            "SELECT COUNT(*) AS total, COALESCE(SUM(status = 'present'), 0) AS present, "
            "COALESCE(SUM(status = 'absent'), 0) AS absent FROM student_attendance WHERE student_id = %s",
            (session["user_id"],),
        )
        attendance = cursor.fetchone()
        total = int(attendance["total"] or 0)
        cursor.execute("SELECT class_name, section FROM users WHERE id = %s", (session["user_id"],))
        profile = cursor.fetchone()
        data = {
            "results": latest_results, "profile": profile,
            "attendance_total": total, "attendance_present": int(attendance["present"] or 0),
            "attendance_absent": int(attendance["absent"] or 0),
            "attendance_percentage": round(int(attendance["present"] or 0) / total * 100, 1) if total else 0,
        }
    elif role == "teacher":
        cursor.execute(
            "SELECT id, full_name, email FROM users WHERE role = 'student' AND active = TRUE ORDER BY full_name LIMIT 8"
        )
        data = {"students": cursor.fetchall()}
    elif role == "parent":
        cursor.execute(
            "SELECT u.id, u.full_name, u.class_name, u.section FROM parent_students ps "
            "JOIN users u ON u.id = ps.student_id WHERE ps.parent_id = %s ORDER BY u.full_name",
            (session["user_id"],),
        )
        children = cursor.fetchall()
        for child in children:
            cursor.execute(
                "SELECT COUNT(*) AS total, COALESCE(SUM(status = 'present'), 0) AS present, "
                "COALESCE(SUM(status = 'absent'), 0) AS absent FROM student_attendance WHERE student_id = %s",
                (child["id"],),
            )
            attendance = cursor.fetchone()
            total = int(attendance["total"] or 0)
            child["attendance_total"] = total
            child["attendance_present"] = int(attendance["present"] or 0)
            child["attendance_absent"] = int(attendance["absent"] or 0)
            child["attendance_percentage"] = round(child["attendance_present"] / total * 100, 1) if total else 0
            cursor.execute(
                "SELECT subject_name, score, max_score, term FROM results WHERE student_id = %s "
                "ORDER BY id DESC LIMIT 3",
                (child["id"],),
            )
            child["results"] = cursor.fetchall()
        data = {"children": children}
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
    query = request.args.get("q", "").strip()[:100]
    role_filter = request.args.get("role", "")
    status_filter = request.args.get("status", "")
    filtered_people = rows
    if query:
        query_lower = query.casefold()
        filtered_people = [
            row for row in filtered_people
            if query_lower in row["full_name"].casefold() or query_lower in row["email"].casefold()
        ]
    if role_filter in ROLES:
        filtered_people = [row for row in filtered_people if row["role"] == role_filter]
    if status_filter in ("active", "inactive"):
        active_value = status_filter == "active"
        filtered_people = [row for row in filtered_people if bool(row["active"]) == active_value]
    return render_template(
        "people.html", people=filtered_people, links=links, parents=parents, students=students,
        query=query, role_filter=role_filter, status_filter=status_filter, nav="people",
    )


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
    cursor.execute("SELECT id, full_name, class_name, section FROM users WHERE role = 'student' AND active = TRUE ORDER BY full_name")
    students = cursor.fetchall()
    query = request.args.get("q", "").strip()[:100]
    student_filter = request.args.get("student", "")
    subject_filter = request.args.get("subject", "").strip()[:100]
    term_filter = request.args.get("term", "").strip()[:80]
    sql = (
        "SELECT r.id, r.student_id, r.subject_name, r.score, r.max_score, r.term, r.created_at, u.full_name "
        "FROM results r JOIN users u ON u.id = r.student_id WHERE 1 = 1"
    )
    values = []
    if query:
        sql += " AND (u.full_name LIKE %s OR r.subject_name LIKE %s OR r.term LIKE %s)"
        values.extend([f"%{query}%", f"%{query}%", f"%{query}%"])
    try:
        student_id_filter = int(student_filter) if student_filter else 0
    except ValueError:
        student_id_filter = 0
    if student_id_filter:
        sql += " AND r.student_id = %s"
        values.append(student_id_filter)
    if subject_filter:
        sql += " AND r.subject_name LIKE %s"
        values.append(f"%{subject_filter}%")
    if term_filter:
        sql += " AND r.term LIKE %s"
        values.append(f"%{term_filter}%")
    cursor.execute(sql + " ORDER BY r.id DESC LIMIT 200", values)
    rows = cursor.fetchall()
    report_options = {}
    for row in rows:
        report_options.setdefault((row["student_id"], row["term"]), {
            "student_id": row["student_id"], "term": row["term"], "full_name": row["full_name"],
        })
    cursor.close()
    connection.close()
    return render_template(
        "results.html", students=students, results=rows, query=query,
        report_options=list(report_options.values()), student_filter=student_filter,
        subject_filter=subject_filter, term_filter=term_filter, nav="results",
    )


@app.route("/results/mine")
@role_required("student", "parent")
def my_results():
    connection = get_db()
    cursor = connection.cursor(dictionary=True)
    if session["role"] == "student":
        cursor.execute(
            "SELECT r.student_id, r.subject_name, r.score, r.max_score, r.term, u.full_name FROM results r "
            "JOIN users u ON u.id = r.student_id WHERE r.student_id = %s ORDER BY r.id DESC",
            (session["user_id"],),
        )
    else:
        cursor.execute(
            "SELECT u.id AS student_id, r.subject_name, r.score, r.max_score, r.term, u.full_name FROM parent_students ps "
            "JOIN users u ON u.id = ps.student_id JOIN results r ON r.student_id = u.id "
            "WHERE ps.parent_id = %s ORDER BY r.id DESC",
            (session["user_id"],),
        )
    rows = cursor.fetchall()
    report_options = {}
    for row in rows:
        report_options.setdefault((row["student_id"], row["term"]), {
            "student_id": row["student_id"], "term": row["term"], "full_name": row["full_name"],
        })
    cursor.close()
    connection.close()
    return render_template(
        "results_mine.html", results=rows, report_options=list(report_options.values()),
        is_parent=session["role"] == "parent", nav="my_results",
    )


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
    start_value = request.args.get("start_date", "").strip()
    end_value = request.args.get("end_date", "").strip()
    start_date = end_date = None
    try:
        start_date = date.fromisoformat(start_value) if start_value else None
        end_date = date.fromisoformat(end_value) if end_value else None
        if start_date and end_date and start_date > end_date:
            raise ValueError
    except ValueError:
        start_date = end_date = None
        flash("Choose a valid attendance date range.", "error")
    connection = get_db()
    cursor = connection.cursor(dictionary=True)
    conditions = []
    params = []
    if start_date:
        conditions.append("attendance_date >= %s")
        params.append(start_date)
    if end_date:
        conditions.append("attendance_date <= %s")
        params.append(end_date)
    date_sql = (" AND " + " AND ".join(conditions)) if conditions else ""
    if session["role"] == "student":
        cursor.execute(
            "SELECT COUNT(*) AS total, COALESCE(SUM(status = 'present'), 0) AS present, "
            "COALESCE(SUM(status = 'absent'), 0) AS absent FROM student_attendance "
            "WHERE student_id = %s" + date_sql,
            [session["user_id"]] + params,
        )
        summary = cursor.fetchone()
        cursor.execute(
            "SELECT a.attendance_date, a.status, u.full_name FROM student_attendance a "
            "JOIN users u ON u.id = a.student_id WHERE a.student_id = %s" + date_sql +
            " ORDER BY a.attendance_date DESC LIMIT 500",
            [session["user_id"]] + params,
        )
        rows = cursor.fetchall()
        total = int(summary["total"] or 0)
        summaries = [{
            "student_id": session["user_id"], "full_name": session["name"],
            "total": total, "present": int(summary["present"] or 0),
            "absent": int(summary["absent"] or 0),
            "percentage": round((int(summary["present"] or 0) / total) * 100, 1) if total else 0,
        }]
    else:
        cursor.execute(
            "SELECT u.id AS student_id, u.full_name, COUNT(a.id) AS total, "
            "COALESCE(SUM(a.status = 'present'), 0) AS present, "
            "COALESCE(SUM(a.status = 'absent'), 0) AS absent FROM parent_students ps "
            "JOIN users u ON u.id = ps.student_id LEFT JOIN student_attendance a "
            "ON a.student_id = u.id" + date_sql + " WHERE ps.parent_id = %s "
            "GROUP BY u.id, u.full_name ORDER BY u.full_name",
            params + [session["user_id"]],
        )
        summaries = cursor.fetchall()
        for item in summaries:
            total = int(item["total"] or 0)
            item["present"] = int(item["present"] or 0)
            item["absent"] = int(item["absent"] or 0)
            item["percentage"] = round(item["present"] / total * 100, 1) if total else 0
        cursor.execute(
            "SELECT a.attendance_date, a.status, u.full_name FROM parent_students ps "
            "JOIN users u ON u.id = ps.student_id JOIN student_attendance a ON a.student_id = u.id "
            "WHERE ps.parent_id = %s" + date_sql +
            " ORDER BY a.attendance_date DESC, u.full_name LIMIT 500",
            [session["user_id"]] + params,
        )
        rows = cursor.fetchall()
    cursor.close()
    connection.close()
    return render_template(
        "attendance_my.html", attendance=rows, summaries=summaries,
        start_date=start_value, end_date=end_value,
        is_parent=session["role"] == "parent", nav="my_attendance",
    )


def student_access_allowed(cursor, student_id, allow_teacher=False):
    role = session.get("role")
    if role == "administrator" or (allow_teacher and role == "teacher"):
        return True
    if role == "student":
        return int(student_id) == int(session["user_id"])
    if role == "parent":
        cursor.execute(
            "SELECT 1 FROM parent_students WHERE parent_id = %s AND student_id = %s",
            (session["user_id"], student_id),
        )
        return cursor.fetchone() is not None
    return False


@app.route("/students/profiles", methods=["GET", "POST"])
@role_required("administrator")
def student_profiles():
    connection = get_db()
    cursor = connection.cursor(dictionary=True)
    if request.method == "POST":
        try:
            student_id = int(request.form.get("student_id", "0"))
        except (TypeError, ValueError):
            student_id = 0
        cursor.execute("SELECT id, photo_file FROM users WHERE id = %s AND role = 'student'", (student_id,))
        student = cursor.fetchone()
        if not student:
            flash("Choose a student account to update.", "error")
        else:
            class_name = request.form.get("class_name", "").strip()
            section = request.form.get("section", "").strip()
            house = request.form.get("house", "").strip()
            guardian_name = request.form.get("guardian_name", "").strip()
            guardian_phone = request.form.get("guardian_phone", "").strip()
            upload = request.files.get("photo")
            new_photo = None
            remove_photo = request.form.get("remove_photo") == "yes"
            try:
                if (class_name and len(class_name) > 32) or (section and len(section) > 20):
                    raise ValueError("Class and section must fit within their fields.")
                if (house and len(house) > 40) or (guardian_name and len(guardian_name) > 120):
                    raise ValueError("Check the house or guardian name length.")
                if guardian_phone and len(guardian_phone) > 32:
                    raise ValueError("Guardian phone must be 32 characters or fewer.")
                if upload and upload.filename:
                    filename = secure_filename(upload.filename)
                    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
                    if extension not in PHOTO_EXTENSIONS:
                        raise ValueError("Use a JPG, PNG, or WebP photo.")
                    upload.stream.seek(0, os.SEEK_END)
                    size = upload.stream.tell()
                    upload.stream.seek(0)
                    signature = upload.stream.read(12)
                    upload.stream.seek(0)
                    valid_signature = (
                        (extension in ("jpg", "jpeg") and signature.startswith(b"\xff\xd8\xff"))
                        or (extension == "png" and signature.startswith(b"\x89PNG\r\n\x1a\n"))
                        or (extension == "webp" and signature[:4] == b"RIFF" and signature[8:12] == b"WEBP")
                    )
                    if size > 3 * 1024 * 1024:
                        raise ValueError("Student photos must be 3 MB or smaller.")
                    if not valid_signature:
                        raise ValueError("The selected file is not a valid image of that type.")
                    new_photo = f"{uuid.uuid4().hex}.{extension}"
                    os.makedirs(app.config["STUDENT_PHOTO_FOLDER"], exist_ok=True)
                    upload.save(os.path.join(app.config["STUDENT_PHOTO_FOLDER"], new_photo))
                photo_file = new_photo or (None if remove_photo else student["photo_file"])
                cursor.execute(
                    "UPDATE users SET class_name = %s, section = %s, house = %s, guardian_name = %s, "
                    "guardian_phone = %s, photo_file = %s WHERE id = %s AND role = 'student'",
                    (class_name or None, section or None, house or None, guardian_name or None,
                     guardian_phone or None, photo_file, student_id),
                )
                connection.commit()
                old_photo = student["photo_file"]
                if old_photo and old_photo != photo_file:
                    try:
                        os.remove(os.path.join(app.config["STUDENT_PHOTO_FOLDER"], old_photo))
                    except FileNotFoundError:
                        pass
                flash("Student profile saved.", "success")
                cursor.close()
                connection.close()
                return redirect(url_for("student_profiles", selected=student_id))
            except ValueError as error:
                connection.rollback()
                if new_photo:
                    try:
                        os.remove(os.path.join(app.config["STUDENT_PHOTO_FOLDER"], new_photo))
                    except FileNotFoundError:
                        pass
                flash(str(error), "error")
            except mysql.connector.Error:
                connection.rollback()
                if new_photo:
                    try:
                        os.remove(os.path.join(app.config["STUDENT_PHOTO_FOLDER"], new_photo))
                    except FileNotFoundError:
                        pass
                flash("The student profile could not be saved.", "error")
    cursor.execute(
        "SELECT id, full_name, email, class_name, section, house, guardian_name, guardian_phone, photo_file "
        "FROM users WHERE role = 'student' ORDER BY full_name"
    )
    students = cursor.fetchall()
    cursor.close()
    connection.close()
    selected = request.args.get("selected", type=int)
    selected_student = next((item for item in students if item["id"] == selected), None)
    return render_template(
        "student_profiles.html", students=students, selected=selected,
        selected_student=selected_student, nav="student_profiles",
    )


@app.route("/students/<int:student_id>/id-card")
@role_required("administrator", "student", "parent")
def student_id_card(student_id):
    connection = get_db()
    cursor = connection.cursor(dictionary=True)
    if not student_access_allowed(cursor, student_id):
        cursor.close()
        connection.close()
        abort(404)
    cursor.execute(
        "SELECT id, full_name, class_name, section, house, guardian_name, guardian_phone, photo_file "
        "FROM users WHERE id = %s AND role = 'student' AND active = TRUE",
        (student_id,),
    )
    student = cursor.fetchone()
    cursor.close()
    connection.close()
    if not student:
        abort(404)
    return render_template("student_card.html", student=student, nav="student_card")


@app.route("/students/<int:student_id>/photo")
@role_required("administrator", "student", "parent")
def student_photo(student_id):
    connection = get_db()
    cursor = connection.cursor(dictionary=True)
    if not student_access_allowed(cursor, student_id):
        cursor.close()
        connection.close()
        abort(404)
    cursor.execute("SELECT photo_file FROM users WHERE id = %s AND role = 'student'", (student_id,))
    student = cursor.fetchone()
    cursor.close()
    connection.close()
    if not student or not student["photo_file"]:
        abort(404)
    return send_from_directory(app.config["STUDENT_PHOTO_FOLDER"], student["photo_file"])


@app.route("/report-card/<int:student_id>")
@role_required("administrator", "teacher", "student", "parent")
def download_report_card(student_id):
    term = request.args.get("term", "").strip()[:80]
    if not term:
        abort(400, "Choose a term for the report card.")
    connection = get_db()
    cursor = connection.cursor(dictionary=True)
    if not student_access_allowed(cursor, student_id, allow_teacher=True):
        cursor.close()
        connection.close()
        abort(404)
    cursor.execute(
        "SELECT id, full_name, class_name, section FROM users WHERE id = %s AND role = 'student' AND active = TRUE",
        (student_id,),
    )
    student = cursor.fetchone()
    cursor.execute(
        "SELECT r.subject_name, r.score, r.max_score FROM results r "
        "JOIN (SELECT subject_name, MAX(id) AS latest_id FROM results "
        "WHERE student_id = %s AND term = %s GROUP BY subject_name) latest ON latest.latest_id = r.id "
        "ORDER BY r.subject_name",
        (student_id, term),
    )
    rows = cursor.fetchall()
    cursor.close()
    connection.close()
    if not student:
        abort(404)
    if not rows:
        flash("No marks are recorded for that student and term yet.", "info")
        return redirect(request.referrer or url_for("my_results"))

    total_score = sum((Decimal(str(row["score"])) for row in rows), Decimal("0"))
    total_max = sum((Decimal(str(row["max_score"])) for row in rows), Decimal("0"))
    percentage = (total_score / total_max * Decimal("100")) if total_max else Decimal("0")
    buffer = BytesIO()
    styles = getSampleStyleSheet()
    story = [
        Paragraph("Airforce School", styles["Title"]),
        Paragraph("Academic report card · demo school", styles["Normal"]),
        Spacer(1, 8 * mm),
        Paragraph(f"Student: {html.escape(student['full_name'])}", styles["Heading2"]),
        Paragraph(
            f"Student ID: AFS-{student['id']:05d} &nbsp;&nbsp; Class: "
            f"{html.escape(student['class_name'] or 'Not set')} {html.escape(student['section'] or '')} "
            f"&nbsp;&nbsp; Term: {html.escape(term)}",
            styles["Normal"],
        ),
        Spacer(1, 5 * mm),
    ]
    table_data = [["Subject", "Score", "Maximum", "Progress"]]
    for row in rows:
        score = Decimal(str(row["score"]))
        maximum = Decimal(str(row["max_score"]))
        row_percent = score / maximum * Decimal("100") if maximum else Decimal("0")
        table_data.append([
            Paragraph(html.escape(row["subject_name"]), styles["BodyText"]),
            f"{score:.2f}", f"{maximum:.2f}", f"{row_percent:.1f}%",
        ])
    table_data.append(["Total", f"{total_score:.2f}", f"{total_max:.2f}", f"{percentage:.1f}%"])
    table = Table(table_data, colWidths=[78 * mm, 28 * mm, 28 * mm, 34 * mm], repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#173a63")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#eaf1f8")),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.extend([table, Spacer(1, 8 * mm), Paragraph("This report is generated from marks recorded in the school portal.", styles["Italic"])])
    SimpleDocTemplate(buffer, pagesize=A4, title=f"Report card - {student['full_name']}").build(story)
    buffer.seek(0)
    return send_file(
        buffer, mimetype="application/pdf", as_attachment=True,
        download_name=f"Report-card-AFS-{student_id:05d}.pdf",
    )


@app.route("/results/batch", methods=["GET", "POST"])
@role_required("administrator", "teacher")
def batch_results():
    connection = get_db()
    cursor = connection.cursor(dictionary=True)
    cursor.execute(
        "SELECT DISTINCT class_name, COALESCE(section, '') AS section FROM users "
        "WHERE role = 'student' AND active = TRUE AND class_name IS NOT NULL ORDER BY class_name, section"
    )
    classes = cursor.fetchall()
    class_names = sorted({item["class_name"] for item in classes})
    class_name = request.values.get("class_name", "").strip()[:32]
    section = request.values.get("section", "").strip()[:20]
    subject = request.values.get("subject_name", "").strip()[:100]
    term = request.values.get("term", "").strip()[:80]
    max_score = request.values.get("max_score", "")
    if request.method == "POST":
        try:
            maximum = Decimal(max_score)
            if not class_name or not subject or not term or maximum <= 0 or maximum > Decimal("9999.99"):
                raise ValueError
            cursor.execute(
                "SELECT id FROM users WHERE role = 'student' AND active = TRUE AND class_name = %s "
                "AND COALESCE(section, '') = %s ORDER BY full_name",
                (class_name, section),
            )
            valid_ids = {row["id"] for row in cursor.fetchall()}
            scores = []
            for key, value in request.form.items():
                if key.startswith("score_") and value.strip():
                    student_id = int(key[6:])
                    score = Decimal(value)
                    if student_id not in valid_ids or score < 0 or score > maximum:
                        raise ValueError
                    scores.append((student_id, score))
            if not scores:
                raise ValueError
            for student_id, score in scores:
                cursor.execute(
                    "INSERT INTO results (student_id, subject_name, score, max_score, term, entered_by) "
                    "VALUES (%s, %s, %s, %s, %s, %s)",
                    (student_id, subject, score, maximum, term, session["user_id"]),
                )
            connection.commit()
            flash(f"Marks saved for {len(scores)} students.", "success")
            cursor.close()
            connection.close()
            return redirect(url_for("batch_results", class_name=class_name, section=section,
                                    subject_name=subject, term=term, max_score=max_score))
        except (ValueError, InvalidOperation, TypeError):
            connection.rollback()
            flash("Check the class, subject, term, maximum score, and each mark.", "error")
        except mysql.connector.Error:
            connection.rollback()
            flash("The marks could not be saved. No marks from this batch were kept.", "error")
    students = []
    if class_name:
        cursor.execute(
            "SELECT id, full_name FROM users WHERE role = 'student' AND active = TRUE AND class_name = %s "
            "AND COALESCE(section, '') = %s ORDER BY full_name",
            (class_name, section),
        )
        students = cursor.fetchall()
    cursor.close()
    connection.close()
    return render_template(
        "results_batch.html", classes=classes, class_names=class_names, students=students, class_name=class_name,
        section=section, subject_name=subject, term=term, max_score=max_score, nav="results",
    )


@app.route("/fees", methods=["GET", "POST"])
def fee_guide():
    is_admin = session.get("role") == "administrator"
    if request.method == "POST" and not is_admin:
        abort(403)
    connection = get_db()
    cursor = connection.cursor(dictionary=True)
    if request.method == "POST":
        action = request.form.get("action", "save")
        if action == "toggle":
            try:
                fee_id = int(request.form.get("fee_id", "0") or "0")
            except ValueError:
                fee_id = 0
            cursor.execute("UPDATE fee_items SET active = NOT active WHERE id = %s", (fee_id,))
            connection.commit()
            flash("Fee guide item updated." if cursor.rowcount else "Fee item not found.", "info")
        else:
            title = request.form.get("title", "").strip()
            description = request.form.get("description", "").strip()
            frequency = request.form.get("frequency", "")
            try:
                amount = Decimal(request.form.get("amount", ""))
                fee_id = int(request.form.get("fee_id", "0") or "0")
                if not title or len(title) > 120 or len(description) > 1000 or amount < 0 or amount > Decimal("99999999.99"):
                    raise ValueError
                if frequency not in ("one-time", "monthly", "per-term", "yearly"):
                    raise ValueError
                if fee_id:
                    cursor.execute(
                        "UPDATE fee_items SET title = %s, description = %s, amount = %s, frequency = %s WHERE id = %s",
                        (title, description or None, amount, frequency, fee_id),
                    )
                else:
                    cursor.execute(
                        "INSERT INTO fee_items (title, description, amount, frequency, created_by) "
                        "VALUES (%s, %s, %s, %s, %s)",
                        (title, description or None, amount, frequency, session["user_id"]),
                    )
                connection.commit()
                flash("Demo fee guide saved.", "success")
            except (ValueError, InvalidOperation, TypeError):
                connection.rollback()
                flash("Enter a name, valid amount, frequency, and description.", "error")
    if is_admin:
        cursor.execute("SELECT id, title, description, amount, frequency, active FROM fee_items ORDER BY active DESC, title")
    else:
        cursor.execute("SELECT id, title, description, amount, frequency FROM fee_items WHERE active = TRUE ORDER BY title")
    fees = cursor.fetchall()
    cursor.close()
    connection.close()
    return render_template("fees.html", fees=fees, is_admin=is_admin, nav="fees")


def visible_class_pairs(cursor):
    role = session.get("role")
    if role == "student":
        cursor.execute("SELECT class_name, COALESCE(section, '') AS section FROM users WHERE id = %s", (session["user_id"],))
        rows = cursor.fetchall()
    elif role == "parent":
        cursor.execute(
            "SELECT u.class_name, COALESCE(u.section, '') AS section FROM parent_students ps "
            "JOIN users u ON u.id = ps.student_id WHERE ps.parent_id = %s AND u.class_name IS NOT NULL",
            (session["user_id"],),
        )
        rows = cursor.fetchall()
    else:
        return []
    return sorted({(row["class_name"], row["section"]) for row in rows if row["class_name"]})


@app.route("/timetable", methods=["GET", "POST"])
@role_required("administrator", "teacher", "student", "parent")
def timetable():
    connection = get_db()
    cursor = connection.cursor(dictionary=True)
    if request.method == "POST":
        if session.get("role") != "administrator":
            cursor.close()
            connection.close()
            abort(403)
        action = request.form.get("action", "save")
        if action == "delete":
            try:
                slot_id = int(request.form.get("slot_id", "0"))
            except ValueError:
                slot_id = 0
            cursor.execute("DELETE FROM timetable_slots WHERE id = %s", (slot_id,))
            connection.commit()
            flash("Timetable entry removed." if cursor.rowcount else "Entry not found.", "info")
        else:
            class_name = request.form.get("class_name", "").strip()[:32]
            section = request.form.get("section", "").strip()[:20]
            subject = request.form.get("subject_name", "").strip()[:100]
            room = request.form.get("room", "").strip()[:80]
            try:
                weekday = int(request.form.get("weekday", "-1"))
                teacher_value = request.form.get("teacher_id", "")
                teacher_id = int(teacher_value) if teacher_value else None
                start_time = datetime.strptime(request.form.get("start_time", ""), "%H:%M").time()
                end_time = datetime.strptime(request.form.get("end_time", ""), "%H:%M").time()
                slot_id = int(request.form.get("slot_id", "0"))
                if not class_name or not subject or weekday not in range(7) or start_time >= end_time:
                    raise ValueError
                if teacher_id:
                    cursor.execute("SELECT 1 FROM users WHERE id = %s AND role = 'teacher' AND active = TRUE", (teacher_id,))
                    if not cursor.fetchone():
                        raise ValueError
                cursor.execute(
                    "SELECT 1 FROM users WHERE role = 'student' AND active = TRUE AND class_name = %s "
                    "AND COALESCE(section, '') = %s LIMIT 1",
                    (class_name, section),
                )
                if not cursor.fetchone():
                    raise ValueError("Choose a class and section that has active students.")
                cursor.execute(
                    "SELECT COUNT(*) AS total FROM timetable_slots WHERE class_name = %s AND section = %s "
                    "AND weekday = %s AND start_time < %s AND end_time > %s AND id <> %s",
                    (class_name, section, weekday, end_time, start_time, slot_id),
                )
                if cursor.fetchone()["total"]:
                    raise ValueError("That class already has an overlapping timetable period.")
                if slot_id:
                    cursor.execute(
                        "UPDATE timetable_slots SET class_name = %s, section = %s, weekday = %s, "
                        "start_time = %s, end_time = %s, subject_name = %s, teacher_id = %s, room = %s WHERE id = %s",
                        (class_name, section, weekday, start_time, end_time, subject, teacher_id, room or None, slot_id),
                    )
                else:
                    cursor.execute(
                        "INSERT INTO timetable_slots (class_name, section, weekday, start_time, end_time, subject_name, teacher_id, room, created_by) "
                        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                        (class_name, section, weekday, start_time, end_time, subject, teacher_id, room or None, session["user_id"]),
                    )
                connection.commit()
                flash("Timetable entry saved.", "success")
            except ValueError as error:
                connection.rollback()
                flash(str(error) or "Check the class, day, time, and subject.", "error")
    role = session.get("role")
    if role == "administrator":
        cursor.execute(
            "SELECT t.*, u.full_name AS teacher_name FROM timetable_slots t "
            "LEFT JOIN users u ON u.id = t.teacher_id ORDER BY t.weekday, t.start_time, t.class_name, t.section"
        )
    elif role == "teacher":
        cursor.execute(
            "SELECT t.*, u.full_name AS teacher_name FROM timetable_slots t "
            "LEFT JOIN users u ON u.id = t.teacher_id WHERE t.teacher_id = %s ORDER BY t.weekday, t.start_time",
            (session["user_id"],),
        )
    else:
        pairs = visible_class_pairs(cursor)
        conditions, values = [], []
        for class_name, section in pairs:
            conditions.append("(t.class_name = %s AND t.section = %s)")
            values.extend([class_name, section])
        if conditions:
            cursor.execute(
                "SELECT t.*, u.full_name AS teacher_name FROM timetable_slots t "
                "LEFT JOIN users u ON u.id = t.teacher_id WHERE " + " OR ".join(conditions) +
                " ORDER BY t.weekday, t.start_time",
                values,
            )
        else:
            cursor.execute(
                "SELECT t.*, u.full_name AS teacher_name FROM timetable_slots t "
                "LEFT JOIN users u ON u.id = t.teacher_id WHERE 1 = 0"
            )
    slots = cursor.fetchall()
    for slot in slots:
        slot["start_text"] = str(slot["start_time"]).split()[-1][:5].zfill(5)
        slot["end_text"] = str(slot["end_time"]).split()[-1][:5].zfill(5)
    cursor.execute(
        "SELECT DISTINCT class_name, COALESCE(section, '') AS section FROM users "
        "WHERE role = 'student' AND active = TRUE AND class_name IS NOT NULL ORDER BY class_name, section"
    )
    classes = cursor.fetchall()
    class_names = sorted({item["class_name"] for item in classes})
    cursor.execute("SELECT id, full_name FROM users WHERE role = 'teacher' AND active = TRUE ORDER BY full_name")
    teachers = cursor.fetchall()
    cursor.close()
    connection.close()
    return render_template(
        "timetable.html", slots=slots, classes=classes, class_names=class_names, teachers=teachers,
        weekdays=WEEKDAYS, is_admin=role == "administrator", nav="timetable",
    )


@app.route("/homework", methods=["GET", "POST"])
@role_required("administrator", "teacher", "student", "parent")
def homework():
    connection = get_db()
    cursor = connection.cursor(dictionary=True)
    role = session.get("role")
    if request.method == "POST":
        if role not in ("administrator", "teacher"):
            cursor.close()
            connection.close()
            abort(403)
        action = request.form.get("action", "create")
        if action == "delete":
            try:
                homework_id = int(request.form.get("homework_id", "0"))
            except ValueError:
                homework_id = 0
            if role == "administrator":
                cursor.execute("DELETE FROM homework_assignments WHERE id = %s", (homework_id,))
            else:
                cursor.execute(
                    "DELETE FROM homework_assignments WHERE id = %s AND created_by = %s",
                    (homework_id, session["user_id"]),
                )
            connection.commit()
            flash("Homework removed." if cursor.rowcount else "Homework not found.", "info")
        else:
            class_name = request.form.get("class_name", "").strip()[:32]
            section = request.form.get("section", "").strip()[:20]
            subject = request.form.get("subject_name", "").strip()[:100]
            title = request.form.get("title", "").strip()[:160]
            description = request.form.get("description", "").strip()
            due_value = request.form.get("due_date", "").strip()
            try:
                due_date = date.fromisoformat(due_value) if due_value else None
                if not class_name or not subject or not title or len(description) > 4000:
                    raise ValueError
                cursor.execute(
                    "SELECT 1 FROM users WHERE role = 'student' AND active = TRUE AND class_name = %s "
                    "AND COALESCE(section, '') = %s LIMIT 1",
                    (class_name, section),
                )
                if not cursor.fetchone():
                    raise ValueError
                cursor.execute(
                    "INSERT INTO homework_assignments (class_name, section, subject_name, title, description, due_date, created_by) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                    (class_name, section, subject, title, description or None, due_date, session["user_id"]),
                )
                connection.commit()
                flash("Homework posted for the selected class.", "success")
            except (ValueError, TypeError):
                connection.rollback()
                flash("Choose a current class and enter a subject, title, and valid due date.", "error")
    if role == "administrator":
        cursor.execute(
            "SELECT h.*, u.full_name AS teacher_name FROM homework_assignments h "
            "JOIN users u ON u.id = h.created_by ORDER BY h.due_date IS NULL, h.due_date, h.created_at DESC"
        )
    elif role == "teacher":
        cursor.execute(
            "SELECT h.*, u.full_name AS teacher_name FROM homework_assignments h "
            "JOIN users u ON u.id = h.created_by ORDER BY h.due_date IS NULL, h.due_date, h.created_at DESC"
        )
    else:
        pairs = visible_class_pairs(cursor)
        conditions, values = [], []
        for class_name, section in pairs:
            conditions.append("(h.class_name = %s AND h.section = %s)")
            values.extend([class_name, section])
        if conditions:
            cursor.execute(
                "SELECT h.*, u.full_name AS teacher_name FROM homework_assignments h "
                "JOIN users u ON u.id = h.created_by WHERE " + " OR ".join(conditions) +
                " ORDER BY h.due_date IS NULL, h.due_date, h.created_at DESC",
                values,
            )
        else:
            cursor.execute(
                "SELECT h.*, u.full_name AS teacher_name FROM homework_assignments h "
                "JOIN users u ON u.id = h.created_by WHERE 1 = 0"
            )
    assignments = cursor.fetchall()
    cursor.execute(
        "SELECT DISTINCT class_name, COALESCE(section, '') AS section FROM users "
        "WHERE role = 'student' AND active = TRUE AND class_name IS NOT NULL ORDER BY class_name, section"
    )
    classes = cursor.fetchall()
    class_names = sorted({item["class_name"] for item in classes})
    cursor.close()
    connection.close()
    return render_template(
        "homework.html", assignments=assignments, classes=classes, class_names=class_names,
        can_post=role in ("administrator", "teacher"), role=role, nav="homework",
    )


@app.route("/library", methods=["GET", "POST"])
@role_required("administrator", "teacher", "student", "parent")
def library():
    connection = get_db()
    cursor = connection.cursor(dictionary=True)
    is_admin = session.get("role") == "administrator"
    if request.method == "POST":
        if not is_admin:
            cursor.close()
            connection.close()
            abort(403)
        action = request.form.get("action", "book")
        try:
            if action == "book":
                title = request.form.get("title", "").strip()[:180]
                author = request.form.get("author", "").strip()[:120]
                isbn = request.form.get("isbn", "").strip()[:32]
                copies = int(request.form.get("copies_total", "1"))
                book_id = int(request.form.get("book_id", "0"))
                if not title or copies < 1 or copies > 10000:
                    raise ValueError("Enter a title and a valid copy count.")
                if book_id:
                    cursor.execute("SELECT id FROM library_books WHERE id = %s FOR UPDATE", (book_id,))
                    if not cursor.fetchone():
                        raise ValueError("Book not found.")
                    cursor.execute(
                        "SELECT COUNT(*) AS total FROM library_loans WHERE book_id = %s AND returned_at IS NULL",
                        (book_id,),
                    )
                    if copies < cursor.fetchone()["total"]:
                        raise ValueError("Return open loans before reducing the number of copies.")
                    cursor.execute(
                        "UPDATE library_books SET title = %s, author = %s, isbn = %s, copies_total = %s WHERE id = %s",
                        (title, author or None, isbn or None, copies, book_id),
                    )
                else:
                    cursor.execute(
                        "INSERT INTO library_books (title, author, isbn, copies_total) VALUES (%s, %s, %s, %s)",
                        (title, author or None, isbn or None, copies),
                    )
                connection.commit()
                flash("Library book saved.", "success")
            elif action == "toggle_book":
                book_id = int(request.form.get("book_id", "0"))
                cursor.execute("UPDATE library_books SET active = NOT active WHERE id = %s", (book_id,))
                connection.commit()
                flash("Book catalogue status updated." if cursor.rowcount else "Book not found.", "info")
            elif action == "issue":
                book_id = int(request.form.get("book_id", "0"))
                student_id = int(request.form.get("student_id", "0"))
                due_date = date.fromisoformat(request.form.get("due_date", ""))
                if due_date < date.today():
                    raise ValueError("The due date cannot be before the issue date.")
                cursor.execute("SELECT copies_total FROM library_books WHERE id = %s AND active = TRUE FOR UPDATE", (book_id,))
                book = cursor.fetchone()
                cursor.execute("SELECT 1 FROM users WHERE id = %s AND role = 'student' AND active = TRUE", (student_id,))
                if not book or not cursor.fetchone():
                    raise ValueError("Choose an active book and student.")
                cursor.execute(
                    "SELECT COUNT(*) AS total FROM library_loans WHERE book_id = %s AND returned_at IS NULL",
                    (book_id,),
                )
                if cursor.fetchone()["total"] >= book["copies_total"]:
                    raise ValueError("All copies of this book are currently on loan.")
                cursor.execute(
                    "INSERT INTO library_loans (book_id, student_id, issued_by, loan_date, due_date) "
                    "VALUES (%s, %s, %s, %s, %s)",
                    (book_id, student_id, session["user_id"], date.today(), due_date),
                )
                connection.commit()
                flash("Book loan recorded.", "success")
            elif action == "return":
                loan_id = int(request.form.get("loan_id", "0"))
                cursor.execute(
                    "UPDATE library_loans SET returned_at = %s, returned_by = %s "
                    "WHERE id = %s AND returned_at IS NULL",
                    (date.today(), session["user_id"], loan_id),
                )
                connection.commit()
                flash("Book return recorded." if cursor.rowcount else "That loan was already returned or not found.", "info")
        except (ValueError, TypeError, InvalidOperation) as error:
            connection.rollback()
            flash(str(error) or "Check the book, student, copy count, and due date.", "error")
        except mysql.connector.Error:
            connection.rollback()
            flash("The library change could not be saved.", "error")
    if is_admin:
        cursor.execute(
            "SELECT b.*, b.copies_total - (SELECT COUNT(*) FROM library_loans l "
            "WHERE l.book_id = b.id AND l.returned_at IS NULL) AS copies_available "
            "FROM library_books b ORDER BY b.active DESC, b.title"
        )
    else:
        cursor.execute(
            "SELECT b.*, b.copies_total - (SELECT COUNT(*) FROM library_loans l "
            "WHERE l.book_id = b.id AND l.returned_at IS NULL) AS copies_available "
            "FROM library_books b WHERE b.active = TRUE ORDER BY b.title"
        )
    books = cursor.fetchall()
    if is_admin:
        cursor.execute(
            "SELECT l.id, l.loan_date, l.due_date, l.returned_at, b.title, u.full_name, l.student_id "
            "FROM library_loans l JOIN library_books b ON b.id = l.book_id "
            "JOIN users u ON u.id = l.student_id ORDER BY l.returned_at IS NULL DESC, l.due_date, u.full_name"
        )
    elif session["role"] == "parent":
        cursor.execute(
            "SELECT l.id, l.loan_date, l.due_date, l.returned_at, b.title, u.full_name, l.student_id "
            "FROM parent_students ps JOIN library_loans l ON l.student_id = ps.student_id "
            "JOIN library_books b ON b.id = l.book_id JOIN users u ON u.id = l.student_id "
            "WHERE ps.parent_id = %s ORDER BY l.returned_at IS NULL DESC, l.due_date, u.full_name",
            (session["user_id"],),
        )
    else:
        cursor.execute(
            "SELECT l.id, l.loan_date, l.due_date, l.returned_at, b.title, u.full_name, l.student_id "
            "FROM library_loans l JOIN library_books b ON b.id = l.book_id "
            "JOIN users u ON u.id = l.student_id WHERE l.student_id = %s "
            "ORDER BY l.returned_at IS NULL DESC, l.due_date",
            (session["user_id"],),
        )
    loans = cursor.fetchall()
    cursor.execute("SELECT id, full_name FROM users WHERE role = 'student' AND active = TRUE ORDER BY full_name")
    students = cursor.fetchall()
    cursor.close()
    connection.close()
    return render_template("library.html", books=books, loans=loans, students=students, is_admin=is_admin, nav="library")


@app.errorhandler(413)
def upload_too_large(error):
    if request.path.startswith("/students/profiles"):
        flash("Student photos must be 3 MB or smaller.", "error")
        return redirect(request.referrer or url_for("student_profiles")), 303
    flash("Exam PDF files must be 10 MB or smaller.", "error")
    return redirect(url_for("school_calendar")), 303


if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG", "false").lower() == "true")
