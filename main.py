import mysql.connector

def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="agam1234",
        database="student_result_system"
    )

# Terminal colours
CYAN = "\033[96m"
PURPLE = "\033[95m"
YELLOW = "\033[93m"
GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"
BOLD = "\033[1m"


def heading(text, colour):
    print(colour + "\n" + "=" * 45)
    print(BOLD + text + RESET)
    print("=" * 45 + RESET)


def success(text):
    print(GREEN + text + RESET)


def error(text):
    print(RED + text + RESET)


def message(text):
    print(YELLOW + text + RESET)


def show_pass_fail(marks, passing_marks):
    if float(marks) >= float(passing_marks):
        print(GREEN + "PASS" + RESET)
        return True
    else:
        print(RED + "FAIL" + RESET)
        return False


def add_student():
    heading("STUDENT MANAGEMENT - ADD STUDENT", CYAN)
    roll_no = input("Roll number: ").strip()
    name = input("Student name: ").strip()
    class_name = input("Class (Enter for 12): ").strip()
    section = input("Section (Enter for A): ").strip()
    if class_name == "":
        class_name = "12"
    if section == "":
        section = "A"
    if roll_no == "" or name == "":
        error("Roll number and name are required.")
        return
    connection = None
    cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        query = "INSERT INTO students (roll_no, name, class_name, section) VALUES (%s, %s, %s, %s)"
        cursor.execute(query, (roll_no, name, class_name, section))
        connection.commit()
        success("Student added.")
    except mysql.connector.Error as err:
        error("Could not add student: " + str(err))
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


def view_students():
    heading("STUDENT MANAGEMENT - VIEW STUDENTS", CYAN)
    connection = None
    cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT student_id, roll_no, name, class_name, section FROM students ORDER BY class_name, section, roll_no")
        rows = cursor.fetchall()
        if len(rows) == 0:
            message("No students found.")
        else:
            print("ID | Roll | Name | Class | Section")
            for row in rows:
                print(row[0], "|", row[1], "|", row[2], "|", row[3], "|", row[4])
    except mysql.connector.Error as err:
        error("Could not read students: " + str(err))
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


def search_student():
    heading("STUDENT MANAGEMENT - SEARCH STUDENT", CYAN)
    search = input("Enter roll number or part of name: ").strip()
    connection = None
    cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        query = "SELECT student_id, roll_no, name, class_name, section FROM students WHERE roll_no LIKE %s OR name LIKE %s"
        cursor.execute(query, ("%" + search + "%", "%" + search + "%"))
        rows = cursor.fetchall()
        if len(rows) == 0:
            message("No matching students found.")
        else:
            for row in rows:
                print(row[0], "|", row[1], "|", row[2], "|", row[3], "|", row[4])
    except mysql.connector.Error as err:
        error("Could not search students: " + str(err))
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


def update_student():
    heading("STUDENT MANAGEMENT - UPDATE STUDENT", CYAN)
    try:
        student_id = int(input("Student ID: "))
    except ValueError:
        error("Student ID must be a number.")
        return
    name = input("New name: ").strip()
    class_name = input("New class: ").strip()
    section = input("New section: ").strip()
    if name == "" or class_name == "" or section == "":
        error("All fields are required.")
        return
    connection = None
    cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        query = "UPDATE students SET name=%s, class_name=%s, section=%s WHERE student_id=%s"
        cursor.execute(query, (name, class_name, section, student_id))
        connection.commit()
        if cursor.rowcount == 0:
            message("Student not found or details were unchanged.")
        else:
            success("Student updated.")
    except mysql.connector.Error as err:
        error("Could not update student: " + str(err))
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


def delete_student():
    heading("STUDENT MANAGEMENT - DELETE STUDENT", CYAN)
    try:
        student_id = int(input("Student ID: "))
    except ValueError:
        error("Student ID must be a number.")
        return
    confirm = input("Delete this student? Type yes to confirm: ").strip().lower()
    if confirm != "yes":
        message("Delete cancelled.")
        return
    connection = None
    cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("DELETE FROM students WHERE student_id=%s", (student_id,))
        connection.commit()
        if cursor.rowcount == 0:
            message("Student not found.")
        else:
            success("Student deleted.")
    except mysql.connector.Error as err:
        error("Could not delete student. Saved marks may be linked to this student.")
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


def add_exam():
    heading("EXAM MANAGEMENT - ADD EXAM", GREEN)
    exam_name = input("Exam name: ").strip()
    academic_year = input("Academic year (example 2026-27): ").strip()
    exam_date = input("Exam date YYYY-MM-DD (Enter to skip): ").strip()
    if exam_name == "" or academic_year == "":
        error("Exam name and academic year are required.")
        return
    connection = None
    cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        if exam_date == "":
            query = "INSERT INTO exams (exam_name, academic_year) VALUES (%s, %s)"
            cursor.execute(query, (exam_name, academic_year))
        else:
            query = "INSERT INTO exams (exam_name, academic_year, exam_date) VALUES (%s, %s, %s)"
            cursor.execute(query, (exam_name, academic_year, exam_date))
        connection.commit()
        success("Exam added.")
    except mysql.connector.Error as err:
        error("Could not add exam: " + str(err))
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


def view_exams():
    heading("EXAM MANAGEMENT - VIEW EXAMS", GREEN)
    connection = None
    cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT exam_id, exam_name, academic_year, exam_date FROM exams ORDER BY academic_year, exam_name")
        rows = cursor.fetchall()
        if len(rows) == 0:
            message("No exams found.")
        else:
            print("ID | Exam | Academic Year | Date")
            for row in rows:
                print(row[0], "|", row[1], "|", row[2], "|", row[3])
    except mysql.connector.Error as err:
        error("Could not read exams: " + str(err))
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


def view_subjects():
    heading("SUBJECTS", PURPLE)
    connection = None
    cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT subject_id, subject_name FROM subjects ORDER BY subject_name")
        rows = cursor.fetchall()
        if len(rows) == 0:
            message("No subjects found. Add subjects to the existing subjects table first.")
        else:
            print("ID | Subject")
            for row in rows:
                print(row[0], "|", row[1])
    except mysql.connector.Error as err:
        error("Could not read subjects: " + str(err))
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


def configure_subject():
    heading("SUBJECTS - SET EXAM SUBJECT AND MARKS", PURPLE)
    try:
        exam_id = int(input("Exam ID: "))
        subject_id = int(input("Subject ID: "))
        max_marks = int(input("Maximum marks: "))
        passing_marks = int(input("Passing marks: "))
    except ValueError:
        error("Enter whole numbers for IDs and marks.")
        return
    if max_marks <= 0 or passing_marks < 0 or passing_marks > max_marks:
        error("Passing marks must be between zero and maximum marks.")
        return
    connection = None
    cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        query = "SELECT exam_subject_id FROM exam_subjects WHERE exam_id=%s AND subject_id=%s"
        cursor.execute(query, (exam_id, subject_id))
        old_row = cursor.fetchone()
        if old_row:
            query = "UPDATE exam_subjects SET max_marks=%s, passing_marks=%s WHERE exam_subject_id=%s"
            cursor.execute(query, (max_marks, passing_marks, old_row[0]))
        else:
            query = "INSERT INTO exam_subjects (exam_id, subject_id, max_marks, passing_marks) VALUES (%s, %s, %s, %s)"
            cursor.execute(query, (exam_id, subject_id, max_marks, passing_marks))
        connection.commit()
        success("Exam subject settings saved.")
    except mysql.connector.Error as err:
        error("Could not save settings. Check the exam and subject IDs.")
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


def view_exam_subjects():
    heading("SUBJECTS SET FOR EACH EXAM", PURPLE)
    connection = None
    cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        query = "SELECT e.exam_name, e.academic_year, s.subject_name, es.max_marks, es.passing_marks FROM exam_subjects es, exams e, subjects s WHERE es.exam_id=e.exam_id AND es.subject_id=s.subject_id ORDER BY e.exam_name, s.subject_name"
        cursor.execute(query)
        rows = cursor.fetchall()
        if len(rows) == 0:
            message("No exam subjects have been set up.")
        else:
            print("Exam | Year | Subject | Maximum | Pass mark")
            for row in rows:
                print(row[0], "|", row[1], "|", row[2], "|", row[3], "|", row[4])
    except mysql.connector.Error as err:
        error("Could not read exam subjects: " + str(err))
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


def enter_marks():
    heading("MARKS - ENTER OR UPDATE", YELLOW)
    try:
        student_id = int(input("Student ID: "))
        exam_subject_id = int(input("Exam-subject ID: "))
        marks = float(input("Marks obtained: "))
    except ValueError:
        error("Enter valid numbers.")
        return
    if marks < 0:
        error("Marks cannot be negative.")
        return
    connection = None
    cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT max_marks FROM exam_subjects WHERE exam_subject_id=%s", (exam_subject_id,))
        subject = cursor.fetchone()
        if subject is None:
            error("Exam-subject ID not found.")
            return
        if marks > float(subject[0]):
            error("Marks cannot be greater than maximum marks.")
            return
        cursor.execute("SELECT mark_id FROM marks WHERE student_id=%s AND exam_subject_id=%s", (student_id, exam_subject_id))
        old_mark = cursor.fetchone()
        if old_mark:
            cursor.execute("UPDATE marks SET marks_obtained=%s WHERE mark_id=%s", (marks, old_mark[0]))
        else:
            query = "INSERT INTO marks (student_id, exam_subject_id, marks_obtained) VALUES (%s, %s, %s)"
            cursor.execute(query, (student_id, exam_subject_id, marks))
        connection.commit()
        success("Marks saved.")
    except mysql.connector.Error as err:
        error("Could not save marks. Check the student and exam-subject IDs.")
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


def grade_result(percentage):
    if percentage >= 90:
        return "A1"
    elif percentage >= 80:
        return "A2"
    elif percentage >= 70:
        return "B1"
    elif percentage >= 60:
        return "B2"
    elif percentage >= 50:
        return "C1"
    elif percentage >= 40:
        return "C2"
    elif percentage >= 33:
        return "D"
    else:
        return "E"


def show_result_summary(total, maximum, passed):
    if maximum == 0:
        return
    percentage = total * 100 / maximum
    grade = grade_result(percentage)
    print("Total:", total, "/", maximum)
    print("Percentage:", round(percentage, 2), "%")
    print("Grade:", grade)
    if passed:
        print(GREEN + "Overall result: PASS" + RESET)
    else:
        print(RED + "Overall result: FAIL" + RESET)


def get_result_rows(student_id):
    connection = None
    cursor = None
    rows = []
    try:
        connection = get_connection()
        cursor = connection.cursor()
        query = "SELECT s.student_id, s.roll_no, s.name, e.exam_id, e.exam_name, e.academic_year, sub.subject_name, m.marks_obtained, es.max_marks, es.passing_marks FROM marks m, students s, exam_subjects es, exams e, subjects sub WHERE m.student_id=s.student_id AND m.exam_subject_id=es.exam_subject_id AND es.exam_id=e.exam_id AND es.subject_id=sub.subject_id"
        if student_id != 0:
            query = query + " AND s.student_id=%s ORDER BY e.exam_id, sub.subject_name"
            cursor.execute(query, (student_id,))
        else:
            query = query + " ORDER BY s.student_id, e.exam_id, sub.subject_name"
            cursor.execute(query)
        rows = cursor.fetchall()
    except mysql.connector.Error as err:
        error("Could not read results: " + str(err))
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
    return rows


def view_student_result():
    heading("RESULTS - ONE STUDENT", GREEN)
    try:
        student_id = int(input("Student ID: "))
    except ValueError:
        error("Student ID must be a number.")
        return
    rows = get_result_rows(student_id)
    if len(rows) == 0:
        message("No results found for this student.")
        return
    current_exam = 0
    total = 0
    maximum = 0
    passed = True
    for row in rows:
        if current_exam != 0 and current_exam != row[3]:
            show_result_summary(total, maximum, passed)
            total = 0
            maximum = 0
            passed = True
        if current_exam != row[3]:
            current_exam = row[3]
            print("\nStudent:", row[2], "| Roll:", row[1])
            print("Exam:", row[4], "| Year:", row[5])
            print("Subject | Marks | Maximum | Pass mark | Result")
        print(row[6], "|", row[7], "|", row[8], "|", row[9], end=" | ")
        subject_passed = show_pass_fail(row[7], row[9])
        total = total + float(row[7])
        maximum = maximum + float(row[8])
        if not subject_passed:
            passed = False
    show_result_summary(total, maximum, passed)


def view_all_results():
    heading("RESULTS - ALL STUDENTS", GREEN)
    rows = get_result_rows(0)
    if len(rows) == 0:
        message("No results found.")
        return
    current_student = 0
    current_exam = 0
    total = 0
    maximum = 0
    passed = True
    for row in rows:
        if current_student != 0 and (current_student != row[0] or current_exam != row[3]):
            show_result_summary(total, maximum, passed)
            total = 0
            maximum = 0
            passed = True
        if current_student != row[0] or current_exam != row[3]:
            current_student = row[0]
            current_exam = row[3]
            print("\nStudent:", row[2], "| Roll:", row[1])
            print("Exam:", row[4], "| Year:", row[5])
            print("Subject | Marks | Maximum | Pass mark | Result")
        print(row[6], "|", row[7], "|", row[8], "|", row[9], end=" | ")
        subject_passed = show_pass_fail(row[7], row[9])
        total = total + float(row[7])
        maximum = maximum + float(row[8])
        if not subject_passed:
            passed = False
    show_result_summary(total, maximum, passed)


def main():
    while True:
        print(PURPLE + BOLD)
        print("+" + "=" * 48 + "+")
        print("|" + "STUDENT RESULT MANAGEMENT".center(48) + "|")
        print("|" + "SYSTEM".center(48) + "|")
        print("+" + "=" * 48 + "+" + RESET)
        heading("MAIN MENU", YELLOW)
        print("1. Add student")
        print("2. View students")
        print("3. Search student")
        print("4. Update student")
        print("5. Delete student")
        print("6. Add exam")
        print("7. View exams")
        print("8. View subjects")
        print("9. Set exam subjects and marks")
        print("10. View subjects set for exams")
        print("11. Enter or update marks")
        print("12. View one student's result")
        print("13. View all results")
        print("0. Exit")
        choice = input("Enter your choice: ").strip()
        if choice == "1":
            add_student()
        elif choice == "2":
            view_students()
        elif choice == "3":
            search_student()
        elif choice == "4":
            update_student()
        elif choice == "5":
            delete_student()
        elif choice == "6":
            add_exam()
        elif choice == "7":
            view_exams()
        elif choice == "8":
            view_subjects()
        elif choice == "9":
            configure_subject()
        elif choice == "10":
            view_exam_subjects()
        elif choice == "11":
            enter_marks()
        elif choice == "12":
            view_student_result()
        elif choice == "13":
            view_all_results()
        elif choice == "0":
            success("Goodbye!")
            break
        else:
            error("Invalid choice. Please try again.")


main()
