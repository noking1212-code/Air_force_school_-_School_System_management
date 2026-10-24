
# Student Result Management System

**Class XII – Computer Science Project**  
**Academic Session: 2026–2027**

---

## 1. Project Overview

The Student Result Management System is a menu-driven application developed using Python and MySQL. It helps manage student records, examination details, subject information, marks, and academic results.

The project demonstrates the use of Python programming, database connectivity, SQL queries, functions, conditional statements, loops, and exception handling.

## 2. Objectives

- Store and manage student information.
- Add, view, search, update, and delete student records.
- Manage subjects and examination details.
- Enter and maintain students' marks.
- Calculate total marks and percentages.
- Display examination results in an organised format.
- Understand Python–MySQL connectivity.

## 3. Features

- Menu-driven terminal interface.
- Student record management.
- Subject and examination management.
- Marks entry and result calculation.
- MySQL database for permanent data storage.
- Colourful terminal headings and messages.
- Sample data for demonstration and testing.
- Basic error handling for database operations.

## 4. Technologies Used

| Technology | Purpose |
|---|---|
| Python 3.x | Application logic |
| MySQL | Database management |
| mysql-connector-python | Python–MySQL connectivity |
| Colorama | Colourful terminal output |
| Visual Studio Code | Code editing and development |

## 5. System Requirements

    ### Hardware Requirements
    - Processor: Intel Core i3 or equivalent
    - RAM: Minimum 4 GB
    - Storage: At least 500 MB of free space
    - Keyboard and mouse
    - Monitor or laptop display

    ### Software Requirements
    - Windows 10/11 or another compatible operating system
    - Python 3.x
    - MySQL Server
    - Visual Studio Code or another Python editor
    - MySQL Workbench (optional)

## 6. Project Structure

The project may contain the following files:

```text
StudentResultManagement/
│
├── main.py
├── database.py
├── schema.sql
├── demo_data.sql
├── requirements.txt
└── README.md
```

- **main.py:** Main menu and application operations.
- **database.py:** MySQL database connection.
- **schema.sql:** SQL commands to create database tables.
- **demo_data.sql:** Sample records for demonstration.
- **requirements.txt:** Python package dependencies.
- **README.md:** Project documentation.

The exact structure depends on the final version of the project.

## 7. Database Design

Database name: `student_result_system`

The database contains the following tables:

1. **students** – Stores student details.
2. **subjects** – Stores subject information.
3. **exams** – Stores examination details.
4. **exam_subjects** – Connects examinations with subjects.
5. **marks** – Stores marks obtained by students.

These tables organise the information and establish relationships between students, subjects, examinations, and marks.

## 8. Installation and Setup

### Step 1: Install Python

Download and install Python from:

https://www.python.org/downloads/

Verify the installation:

```bash
python --version
```

### Step 2: Install MySQL

Install MySQL Server and ensure that the database service is running.

MySQL Workbench may also be installed to execute SQL commands graphically.

### Step 3: Install Python Dependencies

Open the project folder in Visual Studio Code and run:

```bash
pip install -r requirements.txt
```

### Step 4: Configure the Database

Open `database.py` and enter the correct MySQL username and password for your computer.

Make sure the database name matches:

```text
student_result_system
```

### Step 5: Create the Database Tables

Open MySQL Workbench or the MySQL command-line client.

Execute the commands in `schema.sql` to create the database and required tables.

### Step 6: Insert Demonstration Data

Execute `demo_data.sql` after creating the tables.

This inserts sample students, subjects, examinations, and marks for testing the application.

**Important:** Do not repeatedly execute setup scripts that insert sample records unless they are designed to handle duplicates. Do not drop or reset an existing database containing important records.

## 9. How to Run the Project

Open the project folder in Visual Studio Code.

Open the terminal and run:

```bash
python main.py
```

The main menu will appear in the terminal. Select an available option and follow the instructions displayed by the program.

## 10. Sample Demonstration

The application can be demonstrated using sample student records.

Example activities include:

- Displaying all student records.
- Searching for a student using the available search option.
- Updating a student's information.
- Entering examination marks.
- Viewing calculated results and percentages.
- Demonstrating appropriate success and error messages.

The available operations depend on the implemented version of the application.

## 11. Advantages

- Reduces manual record-keeping.
- Stores information in a structured database.
- Makes searching and updating records easier.
- Helps calculate examination results consistently.
- Demonstrates practical use of Python and SQL.
- Can be extended with additional features in the future.

## 12. Limitations

- The application requires a working MySQL database connection.
- Database credentials must be configured correctly.
- The current interface is terminal-based rather than graphical.
- The application is intended for educational use and is not a complete production-grade school management system.

## 13. Future Scope

Possible improvements include:

- A graphical user interface.
- Student login and individual result access.
- Report generation and printing.
- Attendance management.
- Data export to CSV or PDF.
- More detailed academic performance reports.

## 14. Conclusion

The Student Result Management System provides practical experience in Python programming and MySQL database management. It demonstrates how a menu-driven application can be used to store student records, manage examinations, maintain marks, and calculate academic results.

The project strengthens understanding of database connectivity, SQL operations, programming logic, and basic software development.

---

**Submitted as part of the Class XII Computer Science Project**  
**Academic Session: 2026–2027**
## 14. Submitted By

| Student Name | Roll Number | Class |
|---|---:|---|
| Abhinav Pathak | 2 | XII A |
| Prabhsamrath Singh | 17 | XII A |
