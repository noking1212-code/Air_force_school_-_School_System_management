"""Load demo Airforce School accounts and sample records. Safe to run more than once."""
from datetime import date, timedelta
import os

import mysql.connector
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

load_dotenv()

DEMO_PASSWORD = "Airforce@123"
DEMO_EMAILS = {
    "administrator": "principal@airforceschool.demo",
    "teacher": "teacher@airforceschool.demo",
    "student": "student@airforceschool.demo",
    "parent": "parent@airforceschool.demo",
    "visitor": "visitor@airforceschool.demo",
}
DEMO_NAMES = {
    "administrator": "Wing Cdr. Meera Kapoor",
    "teacher": "Anita Sharma",
    "student": "Arjun Singh",
    "parent": "Rajesh Singh",
    "visitor": "Guest Visitor",
}


def connect():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "gradesphere"),
    )


def user_id(cursor, email):
    cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
    row = cursor.fetchone()
    return row["id"] if row else None


def ensure_user(cursor, role):
    email = DEMO_EMAILS[role]
    existing = user_id(cursor, email)
    if existing:
        return existing
    cursor.execute(
        "INSERT INTO users (full_name, email, password_hash, role, active) VALUES (%s, %s, %s, %s, TRUE)",
        (DEMO_NAMES[role], email, generate_password_hash(DEMO_PASSWORD), role),
    )
    return cursor.lastrowid


def main():
    connection = connect()
    cursor = connection.cursor(dictionary=True)
    ids = {role: ensure_user(cursor, role) for role in DEMO_EMAILS}
    connection.commit()

    cursor.execute(
        "INSERT IGNORE INTO parent_students (parent_id, student_id) VALUES (%s, %s)",
        (ids["parent"], ids["student"]),
    )

    cursor.execute("SELECT COUNT(*) AS total FROM notices")
    if cursor.fetchone()["total"] == 0:
        cursor.execute(
            "INSERT INTO notices (title, body, visibility, created_by) VALUES (%s, %s, %s, %s)",
            (
                "Welcome to Airforce School",
                "This demo campus is open for visitors. Sign in with a school account to see results, attendance, and the calendar.",
                "public",
                ids["administrator"],
            ),
        )
        cursor.execute(
            "INSERT INTO notices (title, body, visibility, created_by) VALUES (%s, %s, %s, %s)",
            (
                "Annual sports day",
                "House matches begin next Friday. Students should bring house colours. Parents are welcome in the afternoon.",
                "public",
                ids["administrator"],
            ),
        )
        cursor.execute(
            "INSERT INTO notices (title, body, visibility, created_by) VALUES (%s, %s, %s, %s)",
            (
                "Term 1 result meeting",
                "Teachers will discuss Term 1 scores with linked parents this Thursday after assembly. Students should bring their report printout.",
                "school",
                ids["administrator"],
            ),
        )

    cursor.execute("SELECT COUNT(*) AS total FROM results WHERE student_id = %s", (ids["student"],))
    if cursor.fetchone()["total"] == 0:
        samples = [
            ("Mathematics", 88, 100, "Term 1"),
            ("English", 91, 100, "Term 1"),
            ("Science", 84, 100, "Term 1"),
        ]
        for subject, score, maximum, term in samples:
            cursor.execute(
                "INSERT INTO results (student_id, subject_name, score, max_score, term, entered_by) "
                "VALUES (%s, %s, %s, %s, %s, %s)",
                (ids["student"], subject, score, maximum, term, ids["teacher"]),
            )

    cursor.execute("SELECT COUNT(*) AS total FROM calendar_events")
    if cursor.fetchone()["total"] == 0:
        today = date.today()
        cursor.execute(
            "INSERT INTO calendar_events (title, event_type, event_date, description, created_by) VALUES (%s, %s, %s, %s, %s)",
            ("Gandhi Jayanti", "holiday", date(today.year, 10, 2), "National holiday. Campus closed.", ids["administrator"]),
        )
        cursor.execute(
            "INSERT INTO calendar_events (title, event_type, event_date, description, created_by) VALUES (%s, %s, %s, %s, %s)",
            ("House assembly", "event", today, "Falcon House presents the morning programme.", ids["administrator"]),
        )
        cursor.execute(
            "INSERT INTO calendar_events (title, event_type, event_date, description, created_by) VALUES (%s, %s, %s, %s, %s)",
            ("Term 1 Science exam", "exam", today + timedelta(days=10), "Class XII Science, 9:00 AM, Hall A.", ids["administrator"]),
        )

    cursor.execute(
        "SELECT COUNT(*) AS total FROM student_attendance WHERE student_id = %s",
        (ids["student"],),
    )
    if cursor.fetchone()["total"] == 0:
        today = date.today()
        for offset, status in ((1, "present"), (2, "present"), (3, "absent")):
            day = today - timedelta(days=offset)
            cursor.execute(
                "INSERT INTO student_attendance (student_id, attendance_date, status, recorded_by, updated_by) "
                "VALUES (%s, %s, %s, %s, %s)",
                (ids["student"], day, status, ids["teacher"], ids["teacher"]),
            )
        cursor.execute(
            "INSERT INTO teacher_attendance (teacher_id, attendance_date, status, recorded_by, updated_by) "
            "VALUES (%s, %s, %s, %s, %s)",
            (ids["teacher"], today - timedelta(days=1), "present", ids["administrator"], ids["administrator"]),
        )

    cursor.execute("SELECT COUNT(*) AS total FROM contact_messages")
    if cursor.fetchone()["total"] == 0:
        cursor.execute(
            "INSERT INTO contact_messages (full_name, email, message) VALUES (%s, %s, %s)",
            (
                "Neha Verma",
                "neha.verma@example.com",
                "I would like a visitor pass for the science exhibition next week. Thank you.",
            ),
        )

    connection.commit()
    cursor.close()
    connection.close()
    print("Demo data is ready. Sign in with these accounts (password Airforce@123):")
    for role, email in DEMO_EMAILS.items():
        print(f"  {role:15} {email}")


if __name__ == "__main__":
    main()
