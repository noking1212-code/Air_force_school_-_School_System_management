
CREATE DATABASE IF NOT EXISTS student_result_system;
USE student_result_system;

CREATE TABLE IF NOT EXISTS students (
    student_id INT AUTO_INCREMENT PRIMARY KEY,
    roll_no VARCHAR(20) NOT NULL,
    name VARCHAR(100) NOT NULL,
    class_name VARCHAR(20) NOT NULL DEFAULT '12',
    section VARCHAR(5) NOT NULL DEFAULT 'A',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (class_name, section, roll_no)
);

CREATE TABLE IF NOT EXISTS subjects (
    subject_id INT AUTO_INCREMENT PRIMARY KEY,
    subject_name VARCHAR(60) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS exams (
    exam_id INT AUTO_INCREMENT PRIMARY KEY,
    exam_name VARCHAR(60) NOT NULL,
    academic_year VARCHAR(9) NOT NULL,
    exam_date DATE,
    UNIQUE (exam_name, academic_year)
);

CREATE TABLE IF NOT EXISTS exam_subjects (
    exam_subject_id INT AUTO_INCREMENT PRIMARY KEY,
    exam_id INT NOT NULL,
    subject_id INT NOT NULL,
    max_marks INT NOT NULL DEFAULT 100,
    passing_marks INT NOT NULL DEFAULT 33,

    FOREIGN KEY (exam_id) REFERENCES exams(exam_id),
    FOREIGN KEY (subject_id) REFERENCES subjects(subject_id),
    UNIQUE (exam_id, subject_id),

    CHECK (max_marks > 0),
    CHECK (passing_marks >= 0 AND passing_marks <= max_marks)
);

CREATE TABLE IF NOT EXISTS marks (
    mark_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    exam_subject_id INT NOT NULL,
    marks_obtained DECIMAL(6,2) NOT NULL,

    FOREIGN KEY (student_id) REFERENCES students(student_id),
    FOREIGN KEY (exam_subject_id)
        REFERENCES exam_subjects(exam_subject_id),

    UNIQUE (student_id, exam_subject_id),
    CHECK (marks_obtained >= 0)
);

select * from students;