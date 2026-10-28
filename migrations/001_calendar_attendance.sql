-- Airforce School calendar and daily attendance additions.
-- Back up the configured database before running this migration.
-- Select the same database configured in the app's local environment first.

CREATE TABLE IF NOT EXISTS calendar_events (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(120) NOT NULL,
    event_type ENUM('holiday', 'event', 'exam') NOT NULL,
    event_date DATE NOT NULL,
    description TEXT,
    attachment_file VARCHAR(80),
    attachment_name VARCHAR(255),
    created_by INT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_calendar_event_date (event_date),
    FOREIGN KEY (created_by) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS student_attendance (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    attendance_date DATE NOT NULL,
    status ENUM('present', 'absent') NOT NULL,
    recorded_by INT NOT NULL,
    updated_by INT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_student_attendance_day (student_id, attendance_date),
    INDEX idx_student_attendance_date (attendance_date),
    FOREIGN KEY (student_id) REFERENCES users(id),
    FOREIGN KEY (recorded_by) REFERENCES users(id),
    FOREIGN KEY (updated_by) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS teacher_attendance (
    id INT AUTO_INCREMENT PRIMARY KEY,
    teacher_id INT NOT NULL,
    attendance_date DATE NOT NULL,
    status ENUM('present', 'absent') NOT NULL,
    recorded_by INT NOT NULL,
    updated_by INT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_teacher_attendance_day (teacher_id, attendance_date),
    INDEX idx_teacher_attendance_date (attendance_date),
    FOREIGN KEY (teacher_id) REFERENCES users(id),
    FOREIGN KEY (recorded_by) REFERENCES users(id),
    FOREIGN KEY (updated_by) REFERENCES users(id)
);
