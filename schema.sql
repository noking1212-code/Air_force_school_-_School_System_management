<<<<<<< HEAD
-- GradeSphere corrected full demo database script.
-- Target: MySQL 8.0+. Run in a fresh SQL editor/session.
-- This file creates the schema first, then inserts demo data.
-- Attendance sample/history and daily assessment seed data are included once.
-- Existing data is not dropped or truncated.

-- GradeSphere complete local demo database for MySQL 8.0.
-- Run the full script in a fresh connection. Demo records are fictional.
CREATE DATABASE IF NOT EXISTS gradesphere
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;
=======
-- GradeSphere: backfill 100 school days of demo attendance.
-- Run this only after schema.sql has created the users and attendance tables.
-- Safe to re-run: the unique person/date keys plus INSERT IGNORE prevent duplicates.
-- No LOCK TABLES, temporary tables, START TRANSACTION, COMMIT, or ROLLBACK are used.

>>>>>>> a6a614d6a435c1206b0d33ab0f8c32f92c7c8b50
USE gradesphere;

-- Generate 100 weekdays from 2026-06-01 through 2026-10-19,
-- excluding the 2026-10-02 school holiday.
INSERT IGNORE INTO student_attendance
    (student_id, attendance_date, status, recorded_by, updated_by, created_at, updated_at)
SELECT
    s.id,
    d.attendance_date,
    IF(MOD(s.id + d.day_no, 17) = 0, 'absent', 'present'),
    recorder.id,
    recorder.id,
    TIMESTAMP(d.attendance_date, '08:30:00'),
    TIMESTAMP(d.attendance_date, '08:30:00')
FROM users s
CROSS JOIN (
    SELECT school_dates.attendance_date,
           ROW_NUMBER() OVER (ORDER BY school_dates.attendance_date) AS day_no
    FROM (
        SELECT DATE_ADD(DATE('2026-06-01'), INTERVAL seq.day_offset DAY) AS attendance_date
        FROM (
            SELECT ones.n + tens.n * 10 + hundreds.n * 100 AS day_offset
            FROM (SELECT 0 AS n UNION ALL SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4
                  UNION ALL SELECT 5 UNION ALL SELECT 6 UNION ALL SELECT 7 UNION ALL SELECT 8 UNION ALL SELECT 9) ones
            CROSS JOIN (SELECT 0 AS n UNION ALL SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4
                        UNION ALL SELECT 5 UNION ALL SELECT 6 UNION ALL SELECT 7 UNION ALL SELECT 8 UNION ALL SELECT 9) tens
            CROSS JOIN (SELECT 0 AS n UNION ALL SELECT 1) hundreds
        ) seq
        WHERE seq.day_offset <= DATEDIFF(DATE('2026-10-19'), DATE('2026-06-01'))
    ) school_dates
    WHERE WEEKDAY(school_dates.attendance_date) < 5
      AND school_dates.attendance_date <> DATE('2026-10-02')
) d
JOIN users recorder
  ON recorder.id = COALESCE(
      (SELECT MIN(id) FROM users WHERE role = 'teacher' AND active = TRUE),
      (SELECT MIN(id) FROM users WHERE role = 'administrator' AND active = TRUE),
      (SELECT MIN(id) FROM users)
  )
WHERE s.role = 'student'
  AND s.active = TRUE;

INSERT IGNORE INTO teacher_attendance
    (teacher_id, attendance_date, status, recorded_by, updated_by, created_at, updated_at)
SELECT
    t.id,
    d.attendance_date,
    IF(MOD(t.id + d.day_no, 23) = 0, 'absent', 'present'),
    recorder.id,
    recorder.id,
    TIMESTAMP(d.attendance_date, '08:00:00'),
    TIMESTAMP(d.attendance_date, '08:00:00')
FROM users t
CROSS JOIN (
    SELECT school_dates.attendance_date,
           ROW_NUMBER() OVER (ORDER BY school_dates.attendance_date) AS day_no
    FROM (
        SELECT DATE_ADD(DATE('2026-06-01'), INTERVAL seq.day_offset DAY) AS attendance_date
        FROM (
            SELECT ones.n + tens.n * 10 + hundreds.n * 100 AS day_offset
            FROM (SELECT 0 AS n UNION ALL SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4
                  UNION ALL SELECT 5 UNION ALL SELECT 6 UNION ALL SELECT 7 UNION ALL SELECT 8 UNION ALL SELECT 9) ones
            CROSS JOIN (SELECT 0 AS n UNION ALL SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4
                        UNION ALL SELECT 5 UNION ALL SELECT 6 UNION ALL SELECT 7 UNION ALL SELECT 8 UNION ALL SELECT 9) tens
            CROSS JOIN (SELECT 0 AS n UNION ALL SELECT 1) hundreds
        ) seq
        WHERE seq.day_offset <= DATEDIFF(DATE('2026-10-19'), DATE('2026-06-01'))
    ) school_dates
    WHERE WEEKDAY(school_dates.attendance_date) < 5
      AND school_dates.attendance_date <> DATE('2026-10-02')
) d
JOIN users recorder
  ON recorder.id = COALESCE(
      (SELECT MIN(id) FROM users WHERE role = 'administrator' AND active = TRUE),
      (SELECT MIN(id) FROM users)
  )
WHERE t.role = 'teacher'
  AND t.active = TRUE;

-- Verification: expected 100 distinct school days and 100 records per active account.
SELECT 'students' AS attendance_type,
       COUNT(DISTINCT a.attendance_date) AS distinct_days,
       COUNT(*) AS total_records,
       COUNT(DISTINCT a.student_id) AS people_with_records
FROM student_attendance a
JOIN users u ON u.id = a.student_id
WHERE a.attendance_date BETWEEN '2026-06-01' AND '2026-10-19'
UNION ALL
SELECT 'teachers',
       COUNT(DISTINCT a.attendance_date),
       COUNT(*),
       COUNT(DISTINCT a.teacher_id)
FROM teacher_attendance a
JOIN users u ON u.id = a.teacher_id
WHERE a.attendance_date BETWEEN '2026-06-01' AND '2026-10-19';
