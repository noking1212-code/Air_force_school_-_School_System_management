drop database if EXISTS gradesphere;
-- ================================================================

SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE DATABASE IF NOT EXISTS gradesphere
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

ALTER DATABASE gradesphere
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE gradesphere;

-- ------------------------------------------------
-- 1. TABLES
-- ------------------------------------------------

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(120) NOT NULL,
    email VARCHAR(190) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('student','teacher','parent','visitor','administrator') NOT NULL,
    class_name VARCHAR(32),
    section VARCHAR(20),
    house VARCHAR(40),
    photo_file VARCHAR(80),
    guardian_name VARCHAR(120),
    guardian_phone VARCHAR(32),
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS parent_students (
    parent_id INT NOT NULL,
    student_id INT NOT NULL,
    PRIMARY KEY (parent_id, student_id),
    CONSTRAINT fk_parent_students_parent FOREIGN KEY (parent_id) REFERENCES users(id),
    CONSTRAINT fk_parent_students_student FOREIGN KEY (student_id) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS results (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    subject_name VARCHAR(100) NOT NULL,
    score DECIMAL(6,2) NOT NULL,
    max_score DECIMAL(6,2) NOT NULL,
    term VARCHAR(80) NOT NULL,
    entered_by INT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_results_student_term (student_id, term),
    CONSTRAINT fk_results_student FOREIGN KEY (student_id) REFERENCES users(id),
    CONSTRAINT fk_results_entered_by FOREIGN KEY (entered_by) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS notices (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(160) NOT NULL,
    body TEXT NOT NULL,
    visibility ENUM('public', 'school') NOT NULL DEFAULT 'public',
    created_by INT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_notices_visibility (visibility),
    CONSTRAINT fk_notices_creator FOREIGN KEY (created_by) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS contact_messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(120) NOT NULL,
    email VARCHAR(190) NOT NULL,
    message TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

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
    CONSTRAINT fk_calendar_events_creator FOREIGN KEY (created_by) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

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
    CONSTRAINT fk_student_attendance_student FOREIGN KEY (student_id) REFERENCES users(id),
    CONSTRAINT fk_student_attendance_recorder FOREIGN KEY (recorded_by) REFERENCES users(id),
    CONSTRAINT fk_student_attendance_updater FOREIGN KEY (updated_by) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

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
    CONSTRAINT fk_teacher_attendance_teacher FOREIGN KEY (teacher_id) REFERENCES users(id),
    CONSTRAINT fk_teacher_attendance_recorder FOREIGN KEY (recorded_by) REFERENCES users(id),
    CONSTRAINT fk_teacher_attendance_updater FOREIGN KEY (updated_by) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

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
    CONSTRAINT fk_fee_items_creator FOREIGN KEY (created_by) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS fee_invoices (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    fee_item_id INT NOT NULL,
    invoice_number VARCHAR(40) NOT NULL UNIQUE,
    academic_year VARCHAR(9) NOT NULL,
    period_label VARCHAR(40) NOT NULL,
    issue_date DATE NOT NULL,
    due_date DATE NOT NULL,
    amount_due DECIMAL(10,2) NOT NULL,
    status ENUM('unpaid','partially_paid','paid','overdue','waived') NOT NULL DEFAULT 'unpaid',
    created_by INT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_fee_invoices_student_year (student_id, academic_year),
    INDEX idx_fee_invoices_due_status (due_date, status),
    CONSTRAINT fk_fee_invoices_student FOREIGN KEY (student_id) REFERENCES users(id),
    CONSTRAINT fk_fee_invoices_item FOREIGN KEY (fee_item_id) REFERENCES fee_items(id),
    CONSTRAINT fk_fee_invoices_creator FOREIGN KEY (created_by) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS fee_payment_transactions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    invoice_id INT NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    payment_date DATE NOT NULL,
    payment_method ENUM('cash','card','upi','bank_transfer','cheque') NOT NULL,
    transaction_reference VARCHAR(100) NOT NULL UNIQUE,
    status ENUM('success','pending','failed','refunded') NOT NULL DEFAULT 'success',
    received_by INT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_fee_transactions_invoice_date (invoice_id, payment_date),
    INDEX idx_fee_transactions_status (status),
    CONSTRAINT fk_fee_transactions_invoice FOREIGN KEY (invoice_id) REFERENCES fee_invoices(id),
    CONSTRAINT fk_fee_transactions_receiver FOREIGN KEY (received_by) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

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
    CONSTRAINT fk_timetable_teacher FOREIGN KEY (teacher_id) REFERENCES users(id),
    CONSTRAINT fk_timetable_creator FOREIGN KEY (created_by) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

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
    CONSTRAINT fk_homework_creator FOREIGN KEY (created_by) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS library_books (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(180) NOT NULL,
    author VARCHAR(120),
    isbn VARCHAR(32),
    copies_total INT UNSIGNED NOT NULL DEFAULT 1,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_library_books_active (active),
    INDEX idx_library_books_title (title),
    INDEX idx_library_books_isbn (isbn)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

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
    CONSTRAINT fk_library_loans_book FOREIGN KEY (book_id) REFERENCES library_books(id),
    CONSTRAINT fk_library_loans_student FOREIGN KEY (student_id) REFERENCES users(id),
    CONSTRAINT fk_library_loans_issuer FOREIGN KEY (issued_by) REFERENCES users(id),
    CONSTRAINT fk_library_loans_returner FOREIGN KEY (returned_by) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------
-- 2. NORMALISE EXISTING TABLE COLLATIONS
--    CREATE TABLE IF NOT EXISTS does not change older tables.
--    These ALTER statements fix old general_ci/unicode_ci mixtures.
-- ------------------------------------------------

ALTER TABLE users CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE parent_students CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE results CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE notices CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE contact_messages CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE calendar_events CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE student_attendance CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE teacher_attendance CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE fee_items CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE fee_invoices CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE fee_payment_transactions CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE timetable_slots CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE homework_assignments CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE library_books CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE library_loans CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- ------------------------------------------------
-- 3. DEMO ACCOUNTS
-- ------------------------------------------------

-- Core accounts retain their original IDs for the supplied demo setup.
INSERT IGNORE INTO users
    (id, full_name, email, password_hash, role, active, created_at,
     class_name, section, house, photo_file, guardian_name, guardian_phone)
VALUES
(1,'prabhsamrath singh','prabhsmarathsingh1212@gmail.com','scrypt:32768:8:1$HW1dDtTeZp0qaiLG$2095e79f7ab181fce3f58791912898fd2b080c7742d06c5c9c11df7be0bd778f05d75e24c6fae0f5a655082c79c4d7892579c1aa4ad736cf8999c1224281562f','administrator',TRUE,'2026-10-27 14:25:15',NULL,NULL,NULL,NULL,NULL,NULL),
(2,'akshat','akshatdemo1234@gmail.com','scrypt:32768:8:1$74WKLXJeS9ofEqDq$efcc89a69f2480bf605e203fcf9971488093faca7c7145b06c167c6b710bba388080a2c43d9c0f482f85202ab4dcdbe57c45d947084772fabfdc9f343bcc65ca','student',TRUE,'2026-10-27 14:45:50',NULL,NULL,NULL,NULL,NULL,NULL),
(3,'Wing Cdr. Meera Kapoor','principal@airforceschool.demo','scrypt:32768:8:1$oZ56i9HeC5SEmo3P$7787ee7a70be90bebe349bd813c927b881d5c2dc06abef64e46320a942af1481557b458add96f007e2765e789815eab6956dd4b86b5493feca092c43c8dabc09','administrator',TRUE,'2026-10-28 10:54:10',NULL,NULL,NULL,NULL,NULL,NULL),
(4,'Anita Sharma','teacher@airforceschool.demo','scrypt:32768:8:1$2hQgw267pKXLLBqX$076aad72868308ac4fc22f7077a18ccb084c8f17593025d79619ac100d71819497d12387da9ceb0a13b8eff27e6b12e8e44f6685f8abbc02005273b9cea3c7c3','teacher',TRUE,'2026-10-28 10:54:10',NULL,NULL,NULL,NULL,NULL,NULL),
(5,'Arjun Singh','student@airforceschool.demo','scrypt:32768:8:1$o3yDTcnNticCxFXo$01e587d29b9014c196e01939f83571f00066a40ed78df076e9d85bcd94d353b02af44864190d21a8dbc3a6b391ebbd787fa3fbb8963a5c1e337036871fd58c74','student',TRUE,'2026-10-28 10:54:11',NULL,NULL,NULL,NULL,NULL,NULL),
(6,'Rajesh Singh','parent@airforceschool.demo','scrypt:32768:8:1$qeOrEbJP9FNA8JpH$a12500bd4954236d01ef2b3c44b3537cc5a5fc935d41c25632533d3eb05a45b50ba74231f6ef97ac8c1c80cfba54333e2ab5f50c403292c35df2ee78d67aaffc','parent',TRUE,'2026-10-28 10:54:11',NULL,NULL,NULL,NULL,NULL,NULL),
(7,'Guest Visitor','visitor@airforceschool.demo','scrypt:32768:8:1$x8wYSxZ21nXVIZq2$380a48b72660d452be2a1a79af6d403c81563b6215a6ce17da0dd6a9a0ce207192c4c0d25b1715f61ef75231c0931f3fe797ede1a13f2f4079f72a29515b83ec','visitor',TRUE,'2026-10-28 10:54:11',NULL,NULL,NULL,NULL,NULL,NULL);

-- Student accounts. All use the same sample student password hash.
INSERT IGNORE INTO users (full_name,email,password_hash,role,class_name,section,house,active)
SELECT v.full_name, v.email,
       'scrypt:32768:8:1$o3yDTcnNticCxFXo$01e587d29b9014c196e01939f83571f00066a40ed78df076e9d85bcd94d353b02af44864190d21a8dbc3a6b391ebbd787fa3fbb8963a5c1e337036871fd58c74',
       'student',v.class_name,v.section,v.house,TRUE
FROM (
    SELECT 'Aarav Sharma' full_name,'aarav.student@airforceschool.demo' email,'XII' class_name,'Science' section,'Falcon' house
    UNION ALL SELECT 'Vivaan Gupta','vivaan.student@airforceschool.demo','XII','Science','Hawk'
    UNION ALL SELECT 'Aditya Verma','aditya.student@airforceschool.demo','XII','Science','Eagle'
    UNION ALL SELECT 'Vihaan Malhotra','vihaan.student@airforceschool.demo','XI','Science','Panther'
    UNION ALL SELECT 'Arjun Mehra','arjun2.student@airforceschool.demo','XI','Commerce','Falcon'
    UNION ALL SELECT 'Sai Kumar','sai.student@airforceschool.demo','X','A','Hawk'
    UNION ALL SELECT 'Reyansh Singh','reyansh.student@airforceschool.demo','X','B','Eagle'
    UNION ALL SELECT 'Ayaan Patel','ayaan.student@airforceschool.demo','IX','A','Panther'
    UNION ALL SELECT 'Krishna Joshi','krishna.student@airforceschool.demo','IX','B','Falcon'
    UNION ALL SELECT 'Ishaan Saxena','ishaan.student@airforceschool.demo','VIII','A','Hawk'
    UNION ALL SELECT 'Dhruv Aggarwal','dhruv.student@airforceschool.demo','VIII','B','Eagle'
    UNION ALL SELECT 'Kabir Tiwari','kabir.student@airforceschool.demo','VII','A','Panther'
    UNION ALL SELECT 'Rudra Chauhan','rudra.student@airforceschool.demo','VII','B','Falcon'
    UNION ALL SELECT 'Anshul Yadav','anshul.student@airforceschool.demo','VI','A','Hawk'
    UNION ALL SELECT 'Aarav Rao','aarav2.student@airforceschool.demo','VI','B','Eagle'
    UNION ALL SELECT 'Ananya Verma','ananya.student@airforceschool.demo','XII','Science','Falcon'
    UNION ALL SELECT 'Diya Kulkarni','diya.student@airforceschool.demo','XII','Science','Hawk'
    UNION ALL SELECT 'Saanvi Reddy','saanvi.student@airforceschool.demo','XI','Commerce','Eagle'
    UNION ALL SELECT 'Pari Mishra','pari.student@airforceschool.demo','XI','Science','Panther'
    UNION ALL SELECT 'Navya Bhatia','navya.student@airforceschool.demo','X','A','Falcon'
    UNION ALL SELECT 'Aadhya Iyer','aadhya.student@airforceschool.demo','X','B','Hawk'
    UNION ALL SELECT 'Riya Sen','riya.student@airforceschool.demo','IX','A','Eagle'
    UNION ALL SELECT 'Meera Das','meera.student@airforceschool.demo','IX','B','Panther'
    UNION ALL SELECT 'Kavya Nair','kavya.student@airforceschool.demo','VIII','A','Falcon'
    UNION ALL SELECT 'Ahana Banerjee','ahana.student@airforceschool.demo','VIII','B','Hawk'
    UNION ALL SELECT 'Prisha Roy','prisha.student@airforceschool.demo','VII','A','Eagle'
    UNION ALL SELECT 'Shanaya Kothari','shanaya.student@airforceschool.demo','VII','B','Panther'
    UNION ALL SELECT 'Avani Joshi','avani.student@airforceschool.demo','VI','A','Falcon'
    UNION ALL SELECT 'Myra Pillai','myra.student@airforceschool.demo','VI','B','Hawk'
    UNION ALL SELECT 'Zara Khan','zara.student@airforceschool.demo','XII','Commerce','Eagle'
) v;

-- Teacher accounts.
INSERT IGNORE INTO users (full_name,email,password_hash,role,active)
SELECT v.full_name,v.email,
       'scrypt:32768:8:1$2hQgw267pKXLLBqX$076aad72868308ac4fc22f7077a18ccb084c8f17593025d79619ac100d71819497d12387da9ceb0a13b8eff27e6b12e8e44f6685f8abbc02005273b9cea3c7c3',
       'teacher',TRUE
FROM (
    SELECT 'Ramesh Kumar' full_name,'ramesh.teacher@airforceschool.demo' email
    UNION ALL SELECT 'Sunita Verma','sunita.teacher@airforceschool.demo'
    UNION ALL SELECT 'Manoj Tiwari','manoj.teacher@airforceschool.demo'
    UNION ALL SELECT 'Pooja Saxena','pooja.teacher@airforceschool.demo'
    UNION ALL SELECT 'Alok Rastogi','alok.teacher@airforceschool.demo'
    UNION ALL SELECT 'Deepika Sen','deepika.teacher@airforceschool.demo'
    UNION ALL SELECT 'Vikas Mishra','vikas.teacher@airforceschool.demo'
    UNION ALL SELECT 'Neha Aggarwal','neha.teacher@airforceschool.demo'
    UNION ALL SELECT 'Sanjay Gupta','sanjay.teacher@airforceschool.demo'
    UNION ALL SELECT 'Kirti Jha','kirti.teacher@airforceschool.demo'
    UNION ALL SELECT 'Rajesh Nambiar','rajesh.teacher@airforceschool.demo'
    UNION ALL SELECT 'Smita Deshmukh','smita.teacher@airforceschool.demo'
    UNION ALL SELECT 'Amitabh Ghosh','amitabh.teacher@airforceschool.demo'
    UNION ALL SELECT 'Geeta Iyer','geeta.teacher@airforceschool.demo'
    UNION ALL SELECT 'Nitin Pillai','nitin.teacher@airforceschool.demo'
    UNION ALL SELECT 'Swati Chawla','swati.teacher@airforceschool.demo'
    UNION ALL SELECT 'Tarun Bajaj','tarun.teacher@airforceschool.demo'
    UNION ALL SELECT 'Meenakshi Sundaram','meenakshi.teacher@airforceschool.demo'
    UNION ALL SELECT 'Karan Johar','karan.teacher@airforceschool.demo'
    UNION ALL SELECT 'Shalini Pandey','shalini.teacher@airforceschool.demo'
) v;

-- Parent accounts.
INSERT IGNORE INTO users (full_name,email,password_hash,role,active)
SELECT v.full_name,v.email,
       'scrypt:32768:8:1$qeOrEbJP9FNA8JpH$a12500bd4954236d01ef2b3c44b3537cc5a5fc935d41c25632533d3eb05a45b50ba74231f6ef97ac8c1c80cfba54333e2ab5f50c403292c35df2ee78d67aaffc',
       'parent',TRUE
FROM (
    SELECT 'Manoj Sharma' full_name,'manoj.parent@airforceschool.demo' email
    UNION ALL SELECT 'Suresh Gupta','suresh.parent@airforceschool.demo'
    UNION ALL SELECT 'Naresh Verma','naresh.parent@airforceschool.demo'
    UNION ALL SELECT 'Pankaj Malhotra','pankaj.parent@airforceschool.demo'
    UNION ALL SELECT 'Sunil Mehra','sunil.parent@airforceschool.demo'
    UNION ALL SELECT 'Venkat Kumar','venkat.parent@airforceschool.demo'
    UNION ALL SELECT 'Vikram Singh','vikram.parent@airforceschool.demo'
    UNION ALL SELECT 'Rakesh Patel','rakesh.parent@airforceschool.demo'
    UNION ALL SELECT 'Mukesh Joshi','mukesh.parent@airforceschool.demo'
    UNION ALL SELECT 'Sanjay Saxena','sanjay.parent@airforceschool.demo'
    UNION ALL SELECT 'Ashok Aggarwal','ashok.parent@airforceschool.demo'
    UNION ALL SELECT 'Vijay Tiwari','vijay.parent@airforceschool.demo'
    UNION ALL SELECT 'Anand Chauhan','anand.parent@airforceschool.demo'
    UNION ALL SELECT 'Dinesh Yadav','dinesh.parent@airforceschool.demo'
    UNION ALL SELECT 'Satish Rao','satish.parent@airforceschool.demo'
    UNION ALL SELECT 'Alok Verma','alok.parent@airforceschool.demo'
    UNION ALL SELECT 'Subhash Kulkarni','subhash.parent@airforceschool.demo'
    UNION ALL SELECT 'Srinivas Reddy','srinivas.parent@airforceschool.demo'
    UNION ALL SELECT 'Brijesh Mishra','brijesh.parent@airforceschool.demo'
    UNION ALL SELECT 'Vineet Bhatia','vineet.parent@airforceschool.demo'
    UNION ALL SELECT 'Mohan Iyer','mohan.parent@airforceschool.demo'
    UNION ALL SELECT 'Pradeep Sen','pradeep.parent@airforceschool.demo'
    UNION ALL SELECT 'Joy Das','joy.parent@airforceschool.demo'
    UNION ALL SELECT 'Ranganathan Nair','ranganathan.parent@airforceschool.demo'
    UNION ALL SELECT 'Amit Banerjee','amit.parent@airforceschool.demo'
    UNION ALL SELECT 'Sourav Roy','sourav.parent@airforceschool.demo'
    UNION ALL SELECT 'Hemant Kothari','hemant.parent@airforceschool.demo'
    UNION ALL SELECT 'Prakash Joshi','prakash.parent@airforceschool.demo'
    UNION ALL SELECT 'Chandrashekhar Pillai','chandru.parent@airforceschool.demo'
    UNION ALL SELECT 'Imran Khan','imran.parent@airforceschool.demo'
) v;

-- Additional administrator accounts.
INSERT IGNORE INTO users (full_name,email,password_hash,role,active)
SELECT v.full_name,v.email,
       'scrypt:32768:8:1$oZ56i9HeC5SEmo3P$7787ee7a70be90bebe349bd813c927b881d5c2dc06abef64e46320a942af1481557b458add96f007e2765e789815eab6956dd4b86b5493feca092c43c8dabc09',
       'administrator',TRUE
FROM (
    SELECT 'Air Cmde. Rajeshwar Rao' full_name,'admin1@airforceschool.demo' email
    UNION ALL SELECT 'Gp Capt. Alok Nambiar','admin2@airforceschool.demo'
    UNION ALL SELECT 'Wg Cdr. Vikas Deshmukh','admin3@airforceschool.demo'
    UNION ALL SELECT 'Sqn Ldr. Neha Bajpai','admin4@airforceschool.demo'
    UNION ALL SELECT 'Flt Lt. Sudeep Sen','admin5@airforceschool.demo'
    UNION ALL SELECT 'Mr. Arvind Saxena','admin6@airforceschool.demo'
    UNION ALL SELECT 'Mrs. Sunita Chawla','admin7@airforceschool.demo'
    UNION ALL SELECT 'Dr. R. K. Shrivastava','admin8@airforceschool.demo'
    UNION ALL SELECT 'Mr. Rajiv Bhatnagar','admin9@airforceschool.demo'
    UNION ALL SELECT 'Mrs. Deepa Ghosh','admin10@airforceschool.demo'
) v;

UPDATE users
SET class_name='XI', section='Science', house='Hawk'
WHERE email='akshatdemo1234@gmail.com' AND role='student'
  AND (class_name IS NULL OR class_name='');

UPDATE users
SET class_name='XII', section='Science', house='Falcon'
WHERE email='student@airforceschool.demo' AND role='student'
  AND (class_name IS NULL OR class_name='');

UPDATE users
SET class_name=COALESCE(NULLIF(class_name,''),'X'),
    section=COALESCE(NULLIF(section,''),'A'),
    house=COALESCE(NULLIF(house,''),'Falcon')
WHERE role='student' AND active=TRUE;

-- Link the generated parent/student demo pairs by their sorted IDs.
INSERT IGNORE INTO parent_students (parent_id,student_id)
SELECT p.id,s.id
FROM (
    SELECT id,ROW_NUMBER() OVER (ORDER BY id) rn
    FROM users
    WHERE role='parent' AND email LIKE '%.parent@airforceschool.demo' AND active=TRUE
) p
JOIN (
    SELECT id,ROW_NUMBER() OVER (ORDER BY id) rn
    FROM users
    WHERE role='student' AND email LIKE '%.student@airforceschool.demo' AND active=TRUE
) s ON s.rn=p.rn;

-- Link the built-in parent demo to the built-in student demo.
INSERT IGNORE INTO parent_students (parent_id,student_id)
SELECT p.id,s.id
FROM users p
JOIN users s ON s.email='akshatdemo1234@gmail.com'
WHERE p.email='parent@airforceschool.demo'
  AND p.role='parent' AND s.role='student';

UPDATE users s
JOIN (
    SELECT student_id,MIN(parent_id) parent_id
    FROM parent_students
    GROUP BY student_id
) link ON link.student_id=s.id
JOIN users p ON p.id=link.parent_id
SET s.guardian_name=COALESCE(NULLIF(s.guardian_name,''),p.full_name),
    s.guardian_phone=COALESCE(NULLIF(s.guardian_phone,''),
        CONCAT('9',LPAD(MOD(p.id*7919,1000000000),9,'0')))
WHERE s.role='student';

-- ------------------------------------------------
-- 4. SCHOOL CALENDAR, NOTICES, CONTACT SAMPLE
-- ------------------------------------------------

INSERT IGNORE INTO calendar_events
    (id,title,event_type,event_date,description,attachment_file,attachment_name,created_by,created_at,updated_at)
VALUES
(1,'Gandhi Jayanti','holiday','2026-10-02','National holiday. Campus closed.',NULL,NULL,3,'2026-10-28 10:54:11','2026-10-28 10:54:11'),
(2,'House assembly','event','2026-10-28','Falcon House presents the morning programme.',NULL,NULL,3,'2026-10-28 10:54:11','2026-10-28 10:54:11'),
(3,'Term 1 Science exam','exam','2026-11-07','Class XII Science, 9:00 AM, Hall A.',NULL,NULL,3,'2026-10-28 10:54:11','2026-10-28 10:54:11');

INSERT IGNORE INTO contact_messages (id,full_name,email,message,created_at)
VALUES (1,'Neha Verma','neha.verma@example.com','I would like a visitor pass for the science exhibition next week. Thank you.','2026-10-28 10:54:11');

INSERT INTO notices (title,body,visibility,created_by,created_at)
SELECT n.title,n.body,n.visibility,admin.id,n.created_at
FROM (
    SELECT 'Welcome to Airforce School' title,'This demo campus is open for visitors. Sign in with a school account to see results, attendance, and the calendar.' body,'public' visibility,'2026-10-28 10:54:11' created_at
    UNION ALL SELECT 'Annual sports day','House matches begin next Friday. Students should bring house colours. Parents are welcome in the afternoon.','public','2026-10-28 10:54:11'
    UNION ALL SELECT 'Term 1 result meeting','Teachers will discuss Term 1 scores with linked parents this Thursday after assembly. Students should bring their report printout.','school','2026-10-28 10:54:11'
    UNION ALL SELECT 'Parent-Teacher Meeting - November','Parent-teacher meetings will be held on 14 November 2026. Parents should confirm their preferred time with the class teacher.','school','2026-10-29 09:00:00'
    UNION ALL SELECT 'Winter Uniform Schedule','Students should begin wearing the winter uniform from 2 November 2026. Please label sweaters and jackets clearly.','public','2026-10-28 09:15:00'
    UNION ALL SELECT 'Inter-House Debate Competition','The debate competition will take place in the school auditorium. House coordinators should submit participant names by 5 November.','school','2026-10-27 10:00:00'
    UNION ALL SELECT 'Library Book Return Reminder','Students with books due this week should return them to the library counter before Friday.','school','2026-10-26 08:45:00'
    UNION ALL SELECT 'Science Exhibition Registration','Classes VI to XII may register teams for the annual science exhibition. Project abstracts are due by 12 November.','public','2026-10-24 11:00:00'
    UNION ALL SELECT 'Road Safety Awareness Session','A road safety awareness session for Classes IX and X will be conducted during the activity period.','school','2026-10-23 09:30:00'
    UNION ALL SELECT 'Fee Payment Due Date','The second-term fee instalment is due on 10 November 2026. Please use the official school payment channels.','school','2026-10-22 12:00:00'
    UNION ALL SELECT 'Sports Trials - Athletics','Athletics trials will be held on the school ground. Students should report in sports uniform with their house teacher.','public','2026-10-21 08:30:00'
    UNION ALL SELECT 'Computer Lab Maintenance','The senior computer laboratory will be unavailable during the first two periods on 3 November due to scheduled maintenance.','school','2026-10-20 14:00:00'
    UNION ALL SELECT 'National Education Day Programme','The school will observe National Education Day on 11 November with student presentations and a short assembly.','public','2026-10-19 10:30:00'
    UNION ALL SELECT 'Class XII Practical Preparation','Class XII students should check the practical examination schedule and complete their laboratory records before the review.','school','2026-10-18 13:00:00'
    UNION ALL SELECT 'Lost and Found Desk','A lost-and-found desk is available outside the administrative office. Unclaimed items will be logged at the end of each month.','public','2026-10-17 09:00:00'
) n
JOIN users admin ON admin.email='principal@airforceschool.demo'
WHERE NOT EXISTS (SELECT 1 FROM notices old_n WHERE old_n.title=n.title);

-- ------------------------------------------------
-- 5. RESULTS AND ATTENDANCE
-- ------------------------------------------------

INSERT IGNORE INTO results (id,student_id,subject_name,score,max_score,term,entered_by,created_at)
VALUES
(1,5,'Mathematics',88.00,100.00,'Term 1',4,'2026-10-28 10:54:11'),
(2,5,'English',91.00,100.00,'Term 1',4,'2026-10-28 10:54:11'),
(3,5,'Science',84.00,100.00,'Term 1',4,'2026-10-28 10:54:11');

INSERT IGNORE INTO student_attendance
    (id,student_id,attendance_date,status,recorded_by,updated_by,created_at,updated_at)
VALUES
(1,2,'2026-10-27','present',1,1,'2026-10-27 18:25:07','2026-10-27 18:25:07'),
(2,5,'2026-10-27','present',4,4,'2026-10-28 10:54:11','2026-10-28 10:54:11'),
(3,5,'2026-10-26','present',4,4,'2026-10-28 10:54:11','2026-10-28 10:54:11'),
(4,5,'2026-10-25','absent',4,4,'2026-10-28 10:54:11','2026-10-28 10:54:11');

INSERT IGNORE INTO teacher_attendance
    (id,teacher_id,attendance_date,status,recorded_by,updated_by,created_at,updated_at)
VALUES (1,4,'2026-10-27','present',3,3,'2026-10-28 10:54:11','2026-10-28 10:54:11');

-- Attendance history: weekdays from 1 June through 19 October 2026.
-- The recursive range is below TiDB/MySQL's usual CTE recursion limit.
INSERT IGNORE INTO student_attendance
    (student_id,attendance_date,status,recorded_by,updated_by,created_at,updated_at)
WITH RECURSIVE calendar_dates AS (
    SELECT DATE('2026-06-01') attendance_date
    UNION ALL
    SELECT attendance_date + INTERVAL 1 DAY
    FROM calendar_dates
    WHERE attendance_date < DATE('2026-10-19')
), school_days AS (
    SELECT attendance_date,
           ROW_NUMBER() OVER (ORDER BY attendance_date) day_no
    FROM calendar_dates
    WHERE WEEKDAY(attendance_date) < 5
      AND attendance_date <> DATE('2026-10-02')
)
SELECT s.id,d.attendance_date,
       IF(MOD(s.id+d.day_no,17)=0,'absent','present'),
       teacher.id,teacher.id,
       TIMESTAMP(d.attendance_date,'08:30:00'),
       TIMESTAMP(d.attendance_date,'08:30:00')
FROM users s
CROSS JOIN school_days d
JOIN users teacher ON teacher.email='teacher@airforceschool.demo'
WHERE s.role='student' AND s.active=TRUE;

INSERT IGNORE INTO teacher_attendance
    (teacher_id,attendance_date,status,recorded_by,updated_by,created_at,updated_at)
WITH RECURSIVE calendar_dates AS (
    SELECT DATE('2026-06-01') attendance_date
    UNION ALL
    SELECT attendance_date + INTERVAL 1 DAY
    FROM calendar_dates
    WHERE attendance_date < DATE('2026-10-19')
), school_days AS (
    SELECT attendance_date,
           ROW_NUMBER() OVER (ORDER BY attendance_date) day_no
    FROM calendar_dates
    WHERE WEEKDAY(attendance_date) < 5
      AND attendance_date <> DATE('2026-10-02')
)
SELECT t.id,d.attendance_date,
       IF(MOD(t.id+d.day_no,23)=0,'absent','present'),
       admin.id,admin.id,
       TIMESTAMP(d.attendance_date,'08:00:00'),
       TIMESTAMP(d.attendance_date,'08:00:00')
FROM users t
CROSS JOIN school_days d
JOIN users admin ON admin.email='principal@airforceschool.demo'
WHERE t.role='teacher' AND t.active=TRUE;

-- Daily demo assessments. Subjects vary by class/stream.
INSERT INTO results
    (student_id,subject_name,score,max_score,term,entered_by,created_at)
WITH RECURSIVE calendar_dates AS (
    SELECT DATE('2026-06-01') assessment_date
    UNION ALL
    SELECT assessment_date + INTERVAL 1 DAY
    FROM calendar_dates
    WHERE assessment_date < DATE('2026-10-19')
), school_days AS (
    SELECT assessment_date,
           ROW_NUMBER() OVER (ORDER BY assessment_date) day_no
    FROM calendar_dates
    WHERE WEEKDAY(assessment_date) < 5
      AND assessment_date <> DATE('2026-10-02')
), student_assessments AS (
    SELECT s.id student_id,
      CASE
        WHEN s.class_name IN ('XI','XII') AND s.section='Science' THEN
          CASE MOD(d.day_no-1,6)
            WHEN 0 THEN 'English' WHEN 1 THEN 'Physics' WHEN 2 THEN 'Chemistry'
            WHEN 3 THEN 'Mathematics' WHEN 4 THEN 'Computer Science'
            ELSE 'Physical Education' END
        WHEN s.class_name IN ('XI','XII') AND s.section='Commerce' THEN
          CASE MOD(d.day_no-1,6)
            WHEN 0 THEN 'English' WHEN 1 THEN 'Accountancy' WHEN 2 THEN 'Business Studies'
            WHEN 3 THEN 'Economics' WHEN 4 THEN 'Mathematics'
            ELSE 'Physical Education' END
        ELSE
          CASE MOD(d.day_no-1,6)
            WHEN 0 THEN 'English' WHEN 1 THEN 'Mathematics' WHEN 2 THEN 'Science'
            WHEN 3 THEN 'Social Science' WHEN 4 THEN 'Hindi'
            ELSE 'Computer Applications' END
      END subject_name,
      50+MOD(s.id*13+d.day_no*7,51) score,
      CONCAT('Daily Assessment Day ',LPAD(d.day_no,3,'0')) term,
      d.assessment_date,
      teacher.id entered_by
    FROM users s
    CROSS JOIN school_days d
    JOIN users teacher ON teacher.email='teacher@airforceschool.demo'
    WHERE s.role='student' AND s.active=TRUE
)
SELECT a.student_id,a.subject_name,a.score,100,a.term,a.entered_by,
       TIMESTAMP(a.assessment_date,'15:00:00')
FROM student_assessments a
WHERE NOT EXISTS (
    SELECT 1
    FROM results old_r
    WHERE old_r.student_id=a.student_id
      AND old_r.term=a.term
      AND DATE(old_r.created_at)=a.assessment_date
);

-- ------------------------------------------------
-- 6. HOMEWORK
-- ------------------------------------------------

INSERT INTO homework_assignments
    (class_name,section,subject_name,title,description,due_date,created_by)
SELECT h.class_name,h.section,h.subject_name,h.title,h.description,h.due_date,teacher.id
FROM (
    SELECT 'XII' class_name,'Science' section,'Physics' subject_name,'Electrostatics numericals' title,'Solve questions 1-15 from the electrostatics worksheet. Show all steps.' description,'2026-11-04' due_date
    UNION ALL SELECT 'XII','Science','Chemistry','Chemical kinetics worksheet','Complete the numerical problems on rate laws and half-life.','2026-11-06'
    UNION ALL SELECT 'XII','Science','Mathematics','Differential calculus practice','Complete the assigned derivative and application-of-derivatives problems.','2026-11-05'
    UNION ALL SELECT 'XII','Science','English','Flamingo chapter reflection','Write a 250-word reflection on the prescribed prose chapter.','2026-11-07'
    UNION ALL SELECT 'XII','Science','Computer Applications','SQL query practice','Write and test queries using SELECT, GROUP BY, ORDER BY and JOIN.','2026-11-08'
    UNION ALL SELECT 'XI','Commerce','Accountancy','Journal entries exercise','Prepare journal entries for the transactions in Exercise 4.','2026-11-04'
    UNION ALL SELECT 'XI','Commerce','Business Studies','Forms of business organisation','Create a comparison chart of the major forms of business organisation.','2026-11-06'
    UNION ALL SELECT 'XI','Commerce','Economics','Demand schedule activity','Prepare a demand schedule and draw the corresponding demand curve.','2026-11-05'
    UNION ALL SELECT 'XI','Commerce','English','Writing skills - notice','Draft a notice for an inter-school commerce quiz.','2026-11-07'
    UNION ALL SELECT 'X','A','Mathematics','Quadratic equations revision','Solve the selected word problems and verify the roots.','2026-11-04'
    UNION ALL SELECT 'X','A','Science','Chemical reactions revision','Balance the equations and classify each reaction.','2026-11-06'
    UNION ALL SELECT 'X','A','Social Science','Agriculture map work','Complete the map activity and short-answer questions.','2026-11-05'
    UNION ALL SELECT 'X','A','English','Analytical paragraph','Write an analytical paragraph based on the supplied chart.','2026-11-07'
    UNION ALL SELECT 'X','B','Mathematics','Trigonometry worksheet','Complete the identities worksheet and show the proof for each answer.','2026-11-04'
    UNION ALL SELECT 'X','B','Science','Life processes notes','Prepare concise notes on nutrition and respiration.','2026-11-06'
    UNION ALL SELECT 'IX','A','Mathematics','Linear equations practice','Solve the graph-based questions from the exercise sheet.','2026-11-04'
    UNION ALL SELECT 'IX','A','Science','Atoms and molecules','Complete the formula-writing and mole-concept questions.','2026-11-06'
    UNION ALL SELECT 'IX','B','English','Reading comprehension','Complete the unseen passage and vocabulary questions.','2026-11-05'
    UNION ALL SELECT 'IX','B','Social Science','Democratic rights summary','Prepare a one-page summary of the chapter and key terms.','2026-11-07'
    UNION ALL SELECT 'VIII','A','Mathematics','Comparing quantities','Solve the percentage and discount problems from the worksheet.','2026-11-04'
    UNION ALL SELECT 'VIII','A','Science','Microorganisms project','Create a labelled chart describing useful and harmful microorganisms.','2026-11-06'
    UNION ALL SELECT 'VIII','B','English','Diary entry','Write a diary entry describing a memorable school activity.','2026-11-05'
    UNION ALL SELECT 'VII','A','Mathematics','Fractions and decimals','Complete the mixed practice exercise.','2026-11-04'
    UNION ALL SELECT 'VII','B','Science','Heat and temperature','Answer the short questions and complete the observation table.','2026-11-06'
    UNION ALL SELECT 'VI','A','Social Science','Map skills','Label the physical features shown on the worksheet map.','2026-11-05'
    UNION ALL SELECT 'VI','B','English','Grammar practice','Complete the tense and sentence-correction exercises.','2026-11-07'
    UNION ALL SELECT 'XII','Commerce','Accountancy','Cash flow statement exercise','Prepare the assigned cash flow statement using the indirect method.','2026-11-09'
    UNION ALL SELECT 'XII','Commerce','Economics','National income numericals','Solve the numerical questions on national income aggregates.','2026-11-10'
    UNION ALL SELECT 'XI','Science','Biology','Cell structure diagram','Draw and label the diagrams of plant and animal cells.','2026-11-09'
    UNION ALL SELECT 'XI','Science','Physics','Motion in a straight line','Complete the velocity-time graph questions.','2026-11-10'
    UNION ALL SELECT 'VIII','A','Computer Applications','Presentation design task','Create a five-slide presentation on responsible internet use.','2026-11-10'
    UNION ALL SELECT 'VII','A','Hindi','पाठ अभ्यास','पाठ के प्रश्नों के उत्तर लिखें और नए शब्दों के अर्थ याद करें।','2026-11-10'
) h
JOIN users teacher ON teacher.email='teacher@airforceschool.demo'
WHERE NOT EXISTS (
    SELECT 1 FROM homework_assignments old_h
    WHERE old_h.class_name=h.class_name
      AND old_h.section=h.section
      AND old_h.subject_name=h.subject_name
      AND old_h.title=h.title
      AND old_h.due_date=h.due_date
);

-- ------------------------------------------------
-- 7. TIMETABLE
-- ------------------------------------------------

INSERT INTO timetable_slots
    (class_name,section,weekday,start_time,end_time,subject_name,teacher_id,room,created_by)
SELECT x.class_name,x.section,x.weekday,x.start_time,x.end_time,x.subject_name,
       teacher.id,x.room,admin.id
FROM (
    SELECT 'XII' class_name,'Science' section,1 weekday,'08:00:00' start_time,'08:45:00' end_time,'Physics' subject_name,'teacher@airforceschool.demo' teacher_email,'Block A - Room 101' room
    UNION ALL SELECT 'XII','Science',2,'08:50:00','09:35:00','Chemistry','ramesh.teacher@airforceschool.demo','Block A - Room 101'
    UNION ALL SELECT 'XII','Science',3,'09:40:00','10:25:00','Mathematics','sunita.teacher@airforceschool.demo','Block A - Room 101'
    UNION ALL SELECT 'XII','Science',4,'10:45:00','11:30:00','English','manoj.teacher@airforceschool.demo','Block A - Room 101'
    UNION ALL SELECT 'XII','Science',5,'11:35:00','12:20:00','Computer Applications','pooja.teacher@airforceschool.demo','Block A - Room 101'
    UNION ALL SELECT 'XI','Commerce',1,'08:50:00','09:35:00','Accountancy','alok.teacher@airforceschool.demo','Block B - Room 102'
    UNION ALL SELECT 'XI','Commerce',2,'09:40:00','10:25:00','Business Studies','deepika.teacher@airforceschool.demo','Block B - Room 102'
    UNION ALL SELECT 'XI','Commerce',3,'10:45:00','11:30:00','Economics','vikas.teacher@airforceschool.demo','Block B - Room 102'
    UNION ALL SELECT 'XI','Commerce',4,'11:35:00','12:20:00','English','neha.teacher@airforceschool.demo','Block B - Room 102'
    UNION ALL SELECT 'X','A',1,'08:00:00','08:45:00','Mathematics','teacher@airforceschool.demo','Block C - Room 203'
    UNION ALL SELECT 'X','A',2,'08:50:00','09:35:00','Science','ramesh.teacher@airforceschool.demo','Block C - Room 203'
    UNION ALL SELECT 'X','A',3,'09:40:00','10:25:00','Social Science','sunita.teacher@airforceschool.demo','Block C - Room 203'
    UNION ALL SELECT 'IX','A',1,'08:00:00','08:45:00','English','manoj.teacher@airforceschool.demo','Block C - Room 204'
    UNION ALL SELECT 'VIII','B',2,'08:50:00','09:35:00','Science','pooja.teacher@airforceschool.demo','Block D - Room 301'
    UNION ALL SELECT 'VII','A',3,'09:40:00','10:25:00','Mathematics','alok.teacher@airforceschool.demo','Block D - Room 302'
) x
JOIN users teacher ON teacher.email=x.teacher_email
JOIN users admin ON admin.email='principal@airforceschool.demo'
WHERE NOT EXISTS (
    SELECT 1 FROM timetable_slots old_t
    WHERE old_t.class_name=x.class_name
      AND old_t.section=x.section
      AND old_t.weekday=x.weekday
      AND old_t.start_time=x.start_time
);

-- ------------------------------------------------
-- 8. LIBRARY CATALOGUE AND DEMO LOANS
-- ------------------------------------------------

INSERT INTO library_books (title,author,isbn,copies_total,active)
SELECT b.title,b.author,b.isbn,b.copies_total,TRUE
FROM (
    SELECT 'Wings of Fire' title,'A. P. J. Abdul Kalam' author,'9788173711466' isbn,8 copies_total
    UNION ALL SELECT 'The Discovery of India','Jawaharlal Nehru','9780143031031',4
    UNION ALL SELECT 'The Blue Umbrella','Ruskin Bond','9788171673407',10
    UNION ALL SELECT 'Malgudi Days','R. K. Narayan','9788185986005',7
    UNION ALL SELECT 'The Guide','R. K. Narayan','9788185986012',5
    UNION ALL SELECT 'The Alchemist','Paulo Coelho','9780061122415',6
    UNION ALL SELECT 'Animal Farm','George Orwell','9780451526342',5
    UNION ALL SELECT 'A Brief History of Time','Stephen Hawking','9780553380163',3
    UNION ALL SELECT 'The Selfish Gene','Richard Dawkins','9780199291151',3
    UNION ALL SELECT 'Concepts of Physics Volume 1','H. C. Verma','9788177091878',12
    UNION ALL SELECT 'Concepts of Physics Volume 2','H. C. Verma','9788177092325',12
    UNION ALL SELECT 'NCERT Mathematics Class X','NCERT','9788174506346',15
    UNION ALL SELECT 'NCERT Science Class X','NCERT','9788174506353',15
    UNION ALL SELECT 'NCERT Biology Class XII','NCERT','9788174506810',10
    UNION ALL SELECT 'NCERT Chemistry Class XII','NCERT','9788174506827',10
    UNION ALL SELECT 'NCERT Physics Class XII','NCERT','9788174506834',10
    UNION ALL SELECT 'Computer Science with Python','Sumita Arora','9788177002389',8
    UNION ALL SELECT 'A Suitable Boy','Vikram Seth','9780140230338',3
    UNION ALL SELECT 'The Hobbit','J. R. R. Tolkien','9780547928227',5
    UNION ALL SELECT 'Harry Potter and the Philosopher''s Stone','J. K. Rowling','9780747532699',6
    UNION ALL SELECT 'The Diary of a Young Girl','Anne Frank','9780553296983',4
    UNION ALL SELECT 'Gulliver''s Travels','Jonathan Swift','9780141439495',3
    UNION ALL SELECT 'Pride and Prejudice','Jane Austen','9780141439518',4
    UNION ALL SELECT 'The Art of Public Speaking','Stephen E. Lucas','9780073406732',2
    UNION ALL SELECT 'Introduction to Economics','N. Gregory Mankiw','9780357133484',4
) b
WHERE NOT EXISTS (SELECT 1 FROM library_books old_b WHERE old_b.isbn=b.isbn);

INSERT INTO library_loans
    (book_id,student_id,issued_by,loan_date,due_date,returned_at,returned_by)
SELECT b.id,s.id,issuer.id,x.loan_date,x.due_date,x.returned_at,
       IF(x.returned_at IS NULL,NULL,issuer.id)
FROM (
    SELECT '9780143031031' isbn,'vivaan.student@airforceschool.demo' student_email,'2026-08-03' loan_date,'2026-08-17' due_date,'2026-08-15' returned_at
    UNION ALL SELECT '9788185986012','krishna.student@airforceschool.demo','2026-08-05','2026-08-19','2026-08-14'
    UNION ALL SELECT '9780553380163','ananya.student@airforceschool.demo','2026-08-07','2026-08-21','2026-08-17'
    UNION ALL SELECT '9788177092325','meera.student@airforceschool.demo','2026-08-09','2026-08-23','2026-08-20'
    UNION ALL SELECT '9788174506810','zara.student@airforceschool.demo','2026-08-11','2026-08-25',NULL
    UNION ALL SELECT '9788177002389','arjun2.student@airforceschool.demo','2026-08-13','2026-08-27','2026-08-26'
    UNION ALL SELECT '9780747532699','kabir.student@airforceschool.demo','2026-08-15','2026-08-29','2026-08-29'
    UNION ALL SELECT '9780141439518','pari.student@airforceschool.demo','2026-08-17','2026-08-31','2026-08-25'
    UNION ALL SELECT '9788173711466','prisha.student@airforceschool.demo','2026-08-19','2026-09-02',NULL
    UNION ALL SELECT '9788185986005','aarav.student@airforceschool.demo','2026-08-21','2026-09-04','2026-08-31'
    UNION ALL SELECT '9780451526342','ayaan.student@airforceschool.demo','2026-08-23','2026-09-06','2026-09-03'
    UNION ALL SELECT '9788177091878','aarav2.student@airforceschool.demo','2026-08-25','2026-09-08','2026-09-06'
    UNION ALL SELECT '9788174506353','riya.student@airforceschool.demo','2026-08-27','2026-09-10',NULL
    UNION ALL SELECT '9788174506834','myra.student@airforceschool.demo','2026-08-29','2026-09-12','2026-09-12'
    UNION ALL SELECT '9780547928227','vihaan.student@airforceschool.demo','2026-08-31','2026-09-14','2026-09-08'
    UNION ALL SELECT '9780141439495','dhruv.student@airforceschool.demo','2026-09-02','2026-09-16','2026-09-11'
    UNION ALL SELECT '9780357133484','saanvi.student@airforceschool.demo','2026-09-04','2026-09-18',NULL
    UNION ALL SELECT '9788171673407','ahana.student@airforceschool.demo','2026-09-06','2026-09-20','2026-09-17'
    UNION ALL SELECT '9780061122415','student@airforceschool.demo','2026-09-08','2026-09-22','2026-09-20'
    UNION ALL SELECT '9780199291151','reyansh.student@airforceschool.demo','2026-09-10','2026-09-24','2026-09-23'
    UNION ALL SELECT '9788174506346','anshul.student@airforceschool.demo','2026-09-12','2026-09-26',NULL
    UNION ALL SELECT '9788174506827','aadhya.student@airforceschool.demo','2026-09-14','2026-09-28','2026-09-22'
    UNION ALL SELECT '9780140230338','avani.student@airforceschool.demo','2026-09-16','2026-09-30','2026-09-25'
    UNION ALL SELECT '9780553296983','aditya.student@airforceschool.demo','2026-09-18','2026-10-02','2026-09-28'
    UNION ALL SELECT '9780073406732','ishaan.student@airforceschool.demo','2026-09-20','2026-10-04',NULL
    UNION ALL SELECT '9780143031031','diya.student@airforceschool.demo','2026-09-22','2026-10-06','2026-10-04'
    UNION ALL SELECT '9788185986012','kavya.student@airforceschool.demo','2026-09-24','2026-10-08','2026-10-07'
    UNION ALL SELECT '9780553380163','akshatdemo1234@gmail.com','2026-09-26','2026-10-10','2026-10-10'
    UNION ALL SELECT '9788177092325','sai.student@airforceschool.demo','2026-09-28','2026-10-12',NULL
    UNION ALL SELECT '9788174506810','rudra.student@airforceschool.demo','2026-09-30','2026-10-14','2026-10-09'
    UNION ALL SELECT '9788177002389','navya.student@airforceschool.demo','2026-10-02','2026-10-16','2026-10-12'
    UNION ALL SELECT '9780747532699','shanaya.student@airforceschool.demo','2026-10-04','2026-10-18','2026-10-15'
    UNION ALL SELECT '9780141439518','vivaan.student@airforceschool.demo','2026-10-06','2026-10-20',NULL
    UNION ALL SELECT '9788173711466','krishna.student@airforceschool.demo','2026-10-08','2026-10-22','2026-10-21'
    UNION ALL SELECT '9788185986005','ananya.student@airforceschool.demo','2026-10-10','2026-10-24','2026-10-24'
    UNION ALL SELECT '9780451526342','meera.student@airforceschool.demo','2026-10-12','2026-10-26','2026-10-20'
    UNION ALL SELECT '9788177091878','zara.student@airforceschool.demo','2026-10-14','2026-10-28',NULL
    UNION ALL SELECT '9788174506353','arjun2.student@airforceschool.demo','2026-10-16','2026-10-30','2026-10-26'
    UNION ALL SELECT '9788174506834','kabir.student@airforceschool.demo','2026-10-18','2026-11-01','2026-10-29'
    UNION ALL SELECT '9780547928227','pari.student@airforceschool.demo','2026-10-20','2026-11-03','2026-11-01'
) x
JOIN library_books b ON b.isbn=x.isbn
JOIN users s ON s.email=x.student_email
JOIN users issuer ON issuer.email='teacher@airforceschool.demo'
WHERE NOT EXISTS (
    SELECT 1 FROM library_loans old_l
    WHERE old_l.book_id=b.id
      AND old_l.student_id=s.id
      AND old_l.loan_date=x.loan_date
);

-- ------------------------------------------------
-- 9. DEMO FEE ITEMS, INVOICES, PAYMENT TRANSACTIONS
-- ------------------------------------------------

INSERT INTO fee_items (title,description,amount,frequency,active,created_by)
SELECT f.title,f.description,f.amount,f.frequency,TRUE,admin.id
FROM (
    SELECT 'Annual Tuition Fee' title,'Annual tuition charges for the 2026-27 academic year.' description,48000.00 amount,'yearly' frequency
    UNION ALL SELECT 'Transport Fee','School bus transport charges for the academic year.',18000.00,'yearly'
    UNION ALL SELECT 'Science Laboratory Fee','Science laboratory consumables and practical resources.',2500.00,'per-term'
    UNION ALL SELECT 'Computer Laboratory Fee','Computer laboratory and learning-resource charges.',2000.00,'yearly'
    UNION ALL SELECT 'Library Fee','Library access, catalogue and reading programme charges.',1200.00,'yearly'
    UNION ALL SELECT 'Examination Fee','Term examination administration and assessment charges.',1500.00,'per-term'
    UNION ALL SELECT 'Sports and Activities Fee','Sports, clubs and co-curricular activity charges.',1800.00,'yearly'
    UNION ALL SELECT 'Development Fee','Campus maintenance and educational infrastructure contribution.',3000.00,'yearly'
) f
JOIN users admin ON admin.email='principal@airforceschool.demo'
WHERE NOT EXISTS (SELECT 1 FROM fee_items old_f WHERE old_f.title=f.title);

INSERT IGNORE INTO fee_invoices
    (student_id,fee_item_id,invoice_number,academic_year,period_label,issue_date,due_date,amount_due,status,created_by)
SELECT s.id,f.id,x.invoice_number,x.academic_year,x.period_label,
       x.issue_date,x.due_date,x.amount_due,x.status,admin.id
FROM (
    SELECT 'aarav.student@airforceschool.demo' student_email,'Annual Tuition Fee' fee_title,'GS-2026-0001' invoice_number,'2026-27' academic_year,'Annual' period_label,'2026-04-01' issue_date,'2026-04-15' due_date,48000 amount_due,'paid' status
    UNION ALL SELECT 'aarav.student@airforceschool.demo','Transport Fee','GS-2026-0002','2026-27','Annual','2026-04-01','2026-04-15',18000,'partially_paid'
    UNION ALL SELECT 'vivaan.student@airforceschool.demo','Annual Tuition Fee','GS-2026-0003','2026-27','Annual','2026-04-01','2026-04-15',48000,'paid'
    UNION ALL SELECT 'vivaan.student@airforceschool.demo','Examination Fee','GS-2026-0004','2026-27','Term 1','2026-07-01','2026-07-15',1500,'paid'
    UNION ALL SELECT 'aditya.student@airforceschool.demo','Annual Tuition Fee','GS-2026-0005','2026-27','Annual','2026-04-01','2026-04-15',48000,'overdue'
    UNION ALL SELECT 'vihaan.student@airforceschool.demo','Science Laboratory Fee','GS-2026-0006','2026-27','Term 1','2026-07-01','2026-07-15',2500,'paid'
    UNION ALL SELECT 'arjun2.student@airforceschool.demo','Annual Tuition Fee','GS-2026-0007','2026-27','Annual','2026-04-01','2026-04-15',48000,'partially_paid'
    UNION ALL SELECT 'sai.student@airforceschool.demo','Computer Laboratory Fee','GS-2026-0008','2026-27','Annual','2026-04-01','2026-04-15',2000,'paid'
    UNION ALL SELECT 'reyansh.student@airforceschool.demo','Library Fee','GS-2026-0009','2026-27','Annual','2026-04-01','2026-04-15',1200,'overdue'
    UNION ALL SELECT 'ayaan.student@airforceschool.demo','Sports and Activities Fee','GS-2026-0010','2026-27','Annual','2026-04-01','2026-04-15',1800,'paid'
    UNION ALL SELECT 'krishna.student@airforceschool.demo','Annual Tuition Fee','GS-2026-0011','2026-27','Annual','2026-04-01','2026-04-15',48000,'paid'
    UNION ALL SELECT 'ishaan.student@airforceschool.demo','Examination Fee','GS-2026-0012','2026-27','Term 1','2026-07-01','2026-07-15',1500,'overdue'
    UNION ALL SELECT 'dhruv.student@airforceschool.demo','Annual Tuition Fee','GS-2026-0013','2026-27','Annual','2026-04-01','2026-04-15',48000,'partially_paid'
    UNION ALL SELECT 'kabir.student@airforceschool.demo','Transport Fee','GS-2026-0014','2026-27','Annual','2026-04-01','2026-04-15',18000,'paid'
    UNION ALL SELECT 'rudra.student@airforceschool.demo','Science Laboratory Fee','GS-2026-0015','2026-27','Term 1','2026-07-01','2026-07-15',2500,'overdue'
    UNION ALL SELECT 'ananya.student@airforceschool.demo','Annual Tuition Fee','GS-2026-0016','2026-27','Annual','2026-04-01','2026-04-15',48000,'paid'
    UNION ALL SELECT 'diya.student@airforceschool.demo','Examination Fee','GS-2026-0017','2026-27','Term 1','2026-07-01','2026-07-15',1500,'paid'
    UNION ALL SELECT 'saanvi.student@airforceschool.demo','Annual Tuition Fee','GS-2026-0018','2026-27','Annual','2026-04-01','2026-04-15',48000,'overdue'
    UNION ALL SELECT 'pari.student@airforceschool.demo','Computer Laboratory Fee','GS-2026-0019','2026-27','Annual','2026-04-01','2026-04-15',2000,'paid'
    UNION ALL SELECT 'zara.student@airforceschool.demo','Development Fee','GS-2026-0020','2026-27','Annual','2026-04-01','2026-04-15',3000,'partially_paid'
    UNION ALL SELECT 'navya.student@airforceschool.demo','Annual Tuition Fee','GS-2026-0021','2026-27','Annual','2026-04-01','2026-04-15',48000,'overdue'
    UNION ALL SELECT 'aadhya.student@airforceschool.demo','Sports and Activities Fee','GS-2026-0022','2026-27','Annual','2026-04-01','2026-04-15',1800,'paid'
    UNION ALL SELECT 'riya.student@airforceschool.demo','Library Fee','GS-2026-0023','2026-27','Annual','2026-04-01','2026-04-15',1200,'paid'
    UNION ALL SELECT 'meera.student@airforceschool.demo','Science Laboratory Fee','GS-2026-0024','2026-27','Term 1','2026-07-01','2026-07-15',2500,'partially_paid'
) x
JOIN users s ON s.email=x.student_email
JOIN fee_items f ON f.title=x.fee_title
JOIN users admin ON admin.email='principal@airforceschool.demo';

INSERT IGNORE INTO fee_payment_transactions
    (invoice_id,amount,payment_date,payment_method,transaction_reference,status,received_by)
SELECT i.id,x.amount,x.payment_date,x.payment_method,x.transaction_reference,x.status,admin.id
FROM (
    SELECT 'GS-2026-0001' invoice_number,48000 amount,'2026-04-08' payment_date,'upi' payment_method,'UPI-GS-0001' transaction_reference,'success' status
    UNION ALL SELECT 'GS-2026-0002',6000,'2026-04-09','bank_transfer','NEFT-GS-0002','success'
    UNION ALL SELECT 'GS-2026-0003',48000,'2026-04-06','card','CARD-GS-0003','success'
    UNION ALL SELECT 'GS-2026-0004',1500,'2026-07-10','upi','UPI-GS-0004','success'
    UNION ALL SELECT 'GS-2026-0006',2500,'2026-07-08','cash','CASH-GS-0006','success'
    UNION ALL SELECT 'GS-2026-0007',20000,'2026-04-12','upi','UPI-GS-0007-A','success'
    UNION ALL SELECT 'GS-2026-0008',2000,'2026-04-05','card','CARD-GS-0008','success'
    UNION ALL SELECT 'GS-2026-0010',1800,'2026-04-12','upi','UPI-GS-0010','success'
    UNION ALL SELECT 'GS-2026-0011',48000,'2026-04-11','bank_transfer','NEFT-GS-0011','success'
    UNION ALL SELECT 'GS-2026-0013',12000,'2026-04-10','upi','UPI-GS-0013','success'
    UNION ALL SELECT 'GS-2026-0014',18000,'2026-04-13','bank_transfer','NEFT-GS-0014','success'
    UNION ALL SELECT 'GS-2026-0016',48000,'2026-04-07','upi','UPI-GS-0016','success'
    UNION ALL SELECT 'GS-2026-0017',1500,'2026-07-09','card','CARD-GS-0017','success'
    UNION ALL SELECT 'GS-2026-0019',2000,'2026-04-14','cash','CASH-GS-0019','success'
    UNION ALL SELECT 'GS-2026-0020',1000,'2026-04-15','upi','UPI-GS-0020','success'
    UNION ALL SELECT 'GS-2026-0022',1800,'2026-04-10','upi','UPI-GS-0022','success'
    UNION ALL SELECT 'GS-2026-0023',1200,'2026-04-08','cash','CASH-GS-0023','success'
    UNION ALL SELECT 'GS-2026-0024',1000,'2026-07-12','upi','UPI-GS-0024','success'
    UNION ALL SELECT 'GS-2026-0009',1200,'2026-10-29','upi','UPI-GS-0009-P','pending'
) x
JOIN fee_invoices i ON i.invoice_number=x.invoice_number
JOIN users admin ON admin.email='principal@airforceschool.demo';

-- ------------------------------------------------
-- 10. FINAL VALIDATION SUMMARY
-- ------------------------------------------------

SELECT
  (SELECT COUNT(*) FROM users WHERE role='student' AND active=TRUE) AS active_students,
  (SELECT COUNT(*) FROM users WHERE role='teacher' AND active=TRUE) AS active_teachers,
  (SELECT COUNT(*) FROM users WHERE role='parent' AND active=TRUE) AS active_parents,
  (SELECT COUNT(*) FROM student_attendance WHERE attendance_date BETWEEN '2026-06-01' AND '2026-10-19') AS student_attendance_rows,
  (SELECT COUNT(*) FROM teacher_attendance WHERE attendance_date BETWEEN '2026-06-01' AND '2026-10-19') AS teacher_attendance_rows,
  (SELECT COUNT(*) FROM results WHERE term LIKE 'Daily Assessment Day %' AND created_at >= '2026-06-01' AND created_at < '2026-10-20') AS daily_result_rows,
  (SELECT COUNT(*) FROM parent_students) AS parent_child_links,
  (SELECT COUNT(*) FROM fee_invoices) AS fee_invoice_rows,
  (SELECT COUNT(*) FROM library_books) AS library_book_rows,
  (SELECT COUNT(*) FROM homework_assignments) AS homework_rows;

-- Optional verification: all GradeSphere tables should now report
-- utf8mb4_unicode_ci for their table collation.

USE gradesphere;

SHOW TABLES;

SELECT role, COUNT(*) AS total
FROM users
GROUP BY role;

SELECT COUNT(*) AS total_books
FROM library_books;

SELECT COUNT(*) AS total_invoices
FROM fee_invoices;
