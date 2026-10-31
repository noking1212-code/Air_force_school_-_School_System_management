-- GradeSphere student profiles, fee guide, timetable, homework, and library.
-- Back up the configured database and confirm a test restore before running.
-- This migration is additive; run it once against the database selected in .env.

ALTER TABLE users
    ADD COLUMN IF NOT EXISTS class_name VARCHAR(32) NULL,
    ADD COLUMN IF NOT EXISTS section VARCHAR(20) NULL,
    ADD COLUMN IF NOT EXISTS house VARCHAR(40) NULL,
    ADD COLUMN IF NOT EXISTS photo_file VARCHAR(80) NULL,
    ADD COLUMN IF NOT EXISTS guardian_name VARCHAR(120) NULL,
    ADD COLUMN IF NOT EXISTS guardian_phone VARCHAR(32) NULL;

CREATE TABLE IF NOT EXISTS fee_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(120) NOT NULL,
    description TEXT,
    amount DECIMAL(10,2) NOT NULL,
    frequency ENUM('one-time','monthly','per-term','yearly') NOT NULL DEFAULT 'yearly',
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_by INT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_fee_items_active (active),
    FOREIGN KEY (created_by) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS timetable_slots (
    id INT AUTO_INCREMENT PRIMARY KEY,
    class_name VARCHAR(32) NOT NULL,
    section VARCHAR(20) NOT NULL DEFAULT '',
    weekday TINYINT UNSIGNED NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    subject_name VARCHAR(100) NOT NULL,
    teacher_id INT,
    room VARCHAR(80),
    created_by INT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_timetable_class_day (class_name, section, weekday),
    FOREIGN KEY (teacher_id) REFERENCES users(id),
    FOREIGN KEY (created_by) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS homework_assignments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    class_name VARCHAR(32) NOT NULL,
    section VARCHAR(20) NOT NULL DEFAULT '',
    subject_name VARCHAR(100) NOT NULL,
    title VARCHAR(160) NOT NULL,
    description TEXT,
    due_date DATE,
    created_by INT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_homework_class_due (class_name, section, due_date),
    FOREIGN KEY (created_by) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS library_books (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(180) NOT NULL,
    author VARCHAR(120),
    isbn VARCHAR(32),
    copies_total INT UNSIGNED NOT NULL DEFAULT 1,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_library_books_active (active),
    INDEX idx_library_books_title (title)
);

CREATE TABLE IF NOT EXISTS library_loans (
    id INT AUTO_INCREMENT PRIMARY KEY,
    book_id INT NOT NULL,
    student_id INT NOT NULL,
    issued_by INT NOT NULL,
    loan_date DATE NOT NULL,
    due_date DATE NOT NULL,
    returned_at DATE,
    returned_by INT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_library_loans_student (student_id, due_date),
    INDEX idx_library_loans_book_open (book_id, returned_at),
    FOREIGN KEY (book_id) REFERENCES library_books(id),
    FOREIGN KEY (student_id) REFERENCES users(id),
    FOREIGN KEY (issued_by) REFERENCES users(id),
    FOREIGN KEY (returned_by) REFERENCES users(id)
);
