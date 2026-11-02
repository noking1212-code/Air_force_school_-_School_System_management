<div align="center">

# 🌌 GradeSphere

### A modern, role-based school management portal

**Bringing everyday school workflows together in one simple web application.**

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-Web%20Framework-000000?style=for-the-badge&logo=flask&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-Database-4479A1?style=for-the-badge&logo=mysql&logoColor=white)
![TiDB](https://img.shields.io/badge/TiDB-Cloud%20Option-00A3E0?style=for-the-badge&logo=tidb&logoColor=white)

[✨ Features](#-features) · [🧭 About](#-about-gradesphere) · [⚙️ Setup](#-getting-started) · [🗄️ Database](#-database-configuration) · [🧪 Demo accounts](#-demo-accounts)

</div>

---

## 🧭 About GradeSphere

**GradeSphere** is a web-based school management system created as a school Computer Science project. It brings common school activities into one place and presents different views for the people who use them.

The application is built with **Python and Flask** on the backend, **MySQL-compatible database support** for storing school records, and **HTML, CSS and JavaScript** for the interface. It is designed as a practical demonstration of database connectivity, CRUD operations, role-based pages, file handling and PDF report generation.

The project includes five account roles:

| Role | What the portal is for |
|---|---|
| 🏫 **Administrator / Principal** | Manage school information, users, notices, schedules and school records. |
| 👩‍🏫 **Teacher** | Work with attendance, student results, homework and class information. |
| 🎓 **Student** | View student information, ID details, attendance, results and school updates. |
| 👨‍👩‍👧 **Parent** | View information connected to their linked student account. |
| 🌐 **Visitor** | Explore public information and use the contact page. |

> **Project note:** The demonstration interface uses the sample school name **Airforce School**. GradeSphere is an independent student project and is not an official Air Force or school website.

---

## ✨ Features

<table>
  <tr>
    <td width="50%">
      <h3>🎓 Student information</h3>
      <ul>
        <li>Student profiles and digital ID cards</li>
        <li>Profile photo uploads</li>
        <li>Student attendance records and personal history</li>
        <li>Date-range attendance summaries</li>
        <li>Individual result views</li>
      </ul>
    </td>
    <td width="50%">
      <h3>📊 Academic management</h3>
      <ul>
        <li>Individual and batch result entry</li>
        <li>PDF report-card generation</li>
        <li>Homework and timetable pages</li>
        <li>Teacher attendance records and personal history</li>
        <li>Administrator attendance history for students and teachers</li>
      </ul>
    </td>
  </tr>
  <tr>
    <td>
      <h3>📅 School updates</h3>
      <ul>
        <li>School notices</li>
        <li>Calendar events, holidays and exams</li>
        <li>Optional exam-document uploads</li>
        <li>Role-based information views</li>
      </ul>
    </td>
    <td>
      <h3>🏛️ School operations</h3>
      <ul>
        <li>Fee information and demo fee records</li>
        <li>Library catalogue and book issue/return</li>
        <li>Public contact form</li>
        <li>Administrator message inbox</li>
      </ul>
    </td>
  </tr>
</table>

🎨 **Interface:** Responsive pages with light and dark theme support.

---

## 🧰 Technology stack

| Layer | Technology |
|---|---|
| Backend | Python, Flask |
| Database | MySQL 8.0+ or TiDB Cloud (MySQL-compatible connection) |
| Database connector | MySQL Connector/Python |
| Configuration | `python-dotenv` |
| Frontend | HTML, CSS, JavaScript, Jinja templates |
| PDF reports | ReportLab |

---

## 📁 Project structure

```text
GradeSphere/
│
├── app.py                  # Main Flask application
├── requirements.txt        # Python dependencies
├── .env.example            # Sample configuration; copy this to .env
├── .gitignore              # Files and folders ignored by Git
├── README.md               # Project guide
├── schema.sql              # Initial database schema and demo records
├── templates/              # HTML/Jinja pages
└── static/                 # CSS and JavaScript assets


```

---

## ⚙️ Getting started

### ✅ Prerequisites

Install these before running the project:

- **Python 3.10 or newer**
- **MySQL Server 8.0+** or a compatible **TiDB Cloud** cluster
- A terminal such as PowerShell or Command Prompt
- MySQL Workbench is optional; TiDB Cloud's SQL Editor can also run the setup script.

### 1. Open the project folder

Open PowerShell in the folder containing `app.py`.

### 2. Create and activate a virtual environment

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

If PowerShell does not allow activation, use Command Prompt instead:

```bat
.venv\Scripts\activate.bat
```

### 3. Install dependencies

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Create your environment configuration

Copy `.env.example` to a new file named `.env` in the project root. Then edit `.env` with the connection details for the database you want to use.

PowerShell:

```powershell
Copy-Item .env.example .env
```

> Keep `.env` on your own computer. Do not replace it with `.env.example` after you have entered your database details.

---

## 🗄️ Database configuration

GradeSphere can use **local MySQL** or **TiDB Cloud**. The application reads the connection settings from `.env`, so you can switch databases without editing Python code.

### 💻 Option A — Local MySQL

Example `.env` settings:

```env
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_local_mysql_password
DB_NAME=gradesphere

GRADESPHERE_SECRET=replace_with_a_long_random_value
FLASK_DEBUG=false
```

### ☁️ Option B — TiDB Cloud

Replace the database values with the credentials displayed in your TiDB Cloud connection settings:

```env
DB_HOST=your_tidb_host
DB_PORT=4000
DB_USER=your_tidb_user
DB_PASSWORD=your_tidb_password
DB_NAME=gradesphere
FLASK_DEBUG=false

GRADESPHERE_SECRET=replace_with_a_long_random_value
```

Use the host and port shown by your TiDB cluster. `4000` is an example port; follow the connection details provided by your cluster.

### 🔁 Switch between local MySQL and TiDB

1. Stop the Flask application with `Ctrl + C`.
2. Open `.env`.
3. Change `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD` and `DB_NAME` to the other database's settings.
4. Save `.env` and start GradeSphere again.

**Important:** Local MySQL and TiDB are two separate databases. Switching the connection does not copy or synchronise records between them. Import or transfer the data separately when you need both databases to contain the same records.

### 5. Create the database tables

The supplied `schema.sql` creates the `gradesphere` database, creates the tables and inserts sample records.

**Using MySQL Workbench:**

1. Connect to your local MySQL server.
2. Open `schema.sql` in Workbench.
3. Execute the complete script.
4. Refresh the Schemas panel and check that `gradesphere` appears.

**Using TiDB Cloud:**

1. Open the SQL Editor for the correct TiDB cluster.
2. Open or paste the contents of `schema.sql`.
3. Execute the script.
4. Confirm that the `gradesphere` database and its tables are available.

> ⚠️ Run `schema.sql` for a fresh project database. Do not use it as an update/migration script on a database containing records you need to preserve.

---

## 🚀 Run GradeSphere

With the virtual environment active, run:

```powershell
python app.py
```

Open the application in your browser:

```text
http://127.0.0.1:5000
```

Stop the development server by pressing `Ctrl + C` in the terminal.

---

## 🧪 Demo accounts

The supplied `schema.sql` contains fictional demonstration accounts for these roles:

| Role | Demo email |
|---|---|
| 🏫 Administrator / Principal | `principal@airforceschool.demo` |
| 👩‍🏫 Teacher | `teacher@airforceschool.demo` |
| 🎓 Student | `student@airforceschool.demo` |
| 👨‍👩‍👧 Parent | `parent@airforceschool.demo` |
| 🌐 Visitor | `visitor@airforceschool.demo` |

**Demo password:** `Airforce@123` for the five demo accounts listed above.

The parent demo account is linked to the demo student account. These records are for project demonstration and testing.

---

The supplied `schema.sql` includes demo accounts and sample records. To create additional accounts, sign in as an administrator and use **People**.

---

## 🛠️ Troubleshooting

| Problem | What to check |
|---|---|
| `ModuleNotFoundError` | Activate `.venv` and run `pip install -r requirements.txt`. |
| Database connection refused | Check that the selected database server is running and `DB_HOST` / `DB_PORT` are correct. |
| `Access denied` | Recheck `DB_USER` and `DB_PASSWORD`. |
| Unknown database `gradesphere` | Run `schema.sql` on the database selected in `.env`. |
| Demo login does not work | Confirm that the demo records were imported and that you are using the correct demo email and password. |
| Latest database changes are not visible | Check `.env`, then stop and restart Flask. Local MySQL and TiDB do not sync automatically. |
| Uploaded photo or PDF is missing | Check the `instance/student_photos/` or `instance/exam_uploads/` folder on the computer running the app. |

---

## 📌 Project notes

- `app.py` is the main application entry point.
- `schema.sql` is the initial database setup script.
- `requirements.txt` lists the external Python packages.
- `templates/` contains the Jinja/HTML pages.
- `static/` contains the frontend CSS and JavaScript.
- The project stores uploaded photos and exam documents in the local `instance/` directory by default.
- Database backups should be kept separately from the main source-code folder.

---

<div align="center">

### 💙 Built to bring school workflows into one place.

**GradeSphere — School Management Portal**

<sub>Created by <b>Prabhsamrath Singh</b> & <b>Abhinav Pathak</b><br>
as a student Computer Science project<br>
using Python and MySQL.</sub>

</div>
