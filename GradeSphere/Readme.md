# GradeSphere

GradeSphere is a school-management web application built with **Python, Flask, MySQL and HTML/CSS/JavaScript**. It is designed as a school project and includes demo records for testing the different school portals.

The current demonstration interface uses the school name **Airforce School**. GradeSphere is the name of the software project; it is not an official school or Indian Air Force website.

## Features

- Separate access for administrators, teachers, students, parents and visitors.
- Student profiles, digital student ID cards and profile-photo uploads.
- Student and teacher attendance records.
- Individual and batch result entry, result views and downloadable report-card PDFs.
- School notices, calendar events and optional exam-document uploads.
- Timetable and homework pages.
- Fee information and fee-record management for the demonstration database.
- Library catalogue and book issue/return tracking.
- Public contact form and an administrator inbox.
- Responsive interface with light/dark theme support.

## Technology

- Python 3.10 or newer
- Flask
- MySQL 8.0 or a compatible TiDB Cloud cluster
- MySQL Connector/Python
- HTML, CSS and JavaScript
- ReportLab for PDF report cards

## Project structure

```text
GradeSphere/
├── app.py                  # Main Flask application
├── requirements.txt        # Python packages required to run the app
├── .env.example            # Example database and Flask configuration
├── .env                    # Your local configuration (create this yourself)
├── .gitignore              # Files excluded from Git
├── README.md               # Project setup and usage guide
├── schema.sql              # Initial database schema plus demo records
├── seed_demo.py            # Optional demo-data helper
├── create_admin.py         # Optional administrator-account helper
├── templates/              # Jinja/HTML pages
├── static/                 # CSS and JavaScript files
└── instance/               # Created/used for uploaded photos and exam files
```

`instance/` is created automatically when the application needs to save an upload. It does not need to be created manually.

## 1. Requirements

Install the following before running the project:

1. Python 3.10 or newer.
2. MySQL Server 8.0+, or a TiDB Cloud cluster compatible with the MySQL protocol.
3. MySQL Workbench (optional, useful for local database management) or access to the TiDB Cloud SQL Editor.

## 2. Create the Python environment

Open Command Prompt or PowerShell in the `GradeSphere` project folder.

```powershell
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Activate the environment again whenever you open a new terminal for this project:

```powershell
.venv\Scripts\activate
```

## 3. Configure the database connection

The Flask app and both helper scripts read database settings from a `.env` file in the project root.

1. Copy `.env.example` and rename the copy to `.env`.
2. Open `.env` in a text editor.
3. Fill in the connection details for either local MySQL or TiDB Cloud.
4. Keep `DB_NAME=gradesphere` when using the supplied `schema.sql` file.

### Option A: Local MySQL

Use your local MySQL connection details. A typical local configuration is:

```env
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_local_mysql_password
DB_NAME=gradesphere
```

### Option B: TiDB Cloud

Replace the values with the connection details displayed for your TiDB Cloud cluster:

```env
DB_HOST=your_tidb_cluster_host
DB_PORT=4000
DB_USER=your_tidb_username
DB_PASSWORD=your_tidb_password
DB_NAME=gradesphere
```

Use the actual port shown by TiDB Cloud; `4000` is a common example. Do not keep both options active in `.env`: there should be only one active set of `DB_*` values.

### Switching between local MySQL and TiDB

No Python code needs to be edited to switch databases:

1. Stop the running Flask app with `Ctrl+C`.
2. Change `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD` and `DB_NAME` in `.env` to the other database's connection details.
3. Save `.env` and start the app again.

The two databases are separate. Changes made while connected to local MySQL do not automatically appear in TiDB, and vice versa. Import or transfer the database separately when you need the same records in both places.

## 4. Create the database

The supplied `schema.sql` is the initial setup script. It creates the `gradesphere` database, creates the required tables and inserts the demonstration records.

### Using MySQL Workbench

1. Start your local MySQL Server.
2. Open MySQL Workbench and connect to the server.
3. Open `schema.sql` from the project folder.
4. Execute the complete script.
5. Refresh the Schemas panel and confirm that `gradesphere` appears.

### Using TiDB Cloud

1. Open the SQL Editor for the correct TiDB cluster.
2. Open or paste the contents of `schema.sql`.
3. Execute the complete script.
4. Confirm that the `gradesphere` database and its tables have been created.

**Important:** Run `schema.sql` only when creating a fresh project database. Do not rerun it on a database that already contains records you need to keep. The project does not use the removed migration files and does not automatically alter an existing database structure.

## 5. Run GradeSphere

After installing the packages and configuring the database, run:

```powershell
python app.py
```

Open this address in your browser:

```text
http://127.0.0.1:5000
```

To stop the development server, press `Ctrl+C` in the terminal.

The app reads `FLASK_DEBUG` from `.env`. Use `FLASK_DEBUG=true` during local development. Set it to `false` when you do not want Flask debug mode.

## Demo accounts

The supplied `schema.sql` includes demonstration accounts. The listed demo accounts use the password **`Airforce@123`**.

| Role | Demo email |
|---|---|
| Administrator / Principal | `principal@airforceschool.demo` |
| Teacher | `teacher@airforceschool.demo` |
| Student | `student@airforceschool.demo` |
| Parent | `parent@airforceschool.demo` |
| Visitor | `visitor@airforceschool.demo` |

The parent demo account is linked to the demo student account. The visitor can also view public pages without signing in.

## Optional helper scripts

These scripts are utilities; they are not required to start the Flask application.

### Add missing demo data

```powershell
python seed_demo.py
```

The main `schema.sql` already contains a demonstration dataset, so you normally do **not** need to run this after a fresh schema import. The script is provided for adding missing demo users and filling certain empty sample sections in an existing database.

### Create another administrator

```powershell
python create_admin.py
```

Enter the administrator's name, email and password when prompted. This adds an administrator account to whichever database is currently selected in `.env`. The supplied schema already includes demo administrator accounts, so this script is optional.

## Uploaded files

Student photos and exam attachments are stored locally under the Flask `instance/` folder by default:

```text
instance/
├── student_photos/
└── exam_uploads/
```

These folders are created automatically when files are uploaded. Keep them when they contain photos or exam attachments that you want to retain. The uploaded files are stored on the machine running the Flask application, not inside the MySQL database.

## Common issues

| Problem | What to check |
|---|---|
| `ModuleNotFoundError` | Activate `.venv` and run `pip install -r requirements.txt`. |
| MySQL connection refused | Confirm MySQL is running and `DB_HOST` / `DB_PORT` are correct. |
| Access denied | Check `DB_USER` and `DB_PASSWORD`. |
| Unknown database `gradesphere` | Run `schema.sql` on the selected database server. |
| Login does not work | Confirm that the demo records were imported and use the matching demo email and password. |
| Photo or exam file is missing | Check the `instance/student_photos/` or `instance/exam_uploads/` folder on the server. |
| App is using the previous database | Stop Flask, update `.env`, save it and restart Flask. |

## Notes for the school project

- `app.py` is the main application file.
- `schema.sql` is the database setup file.
- `requirements.txt` lists the external Python packages.
- `templates/` contains the website pages.
- `static/` contains the CSS and JavaScript assets.
- `seed_demo.py` and `create_admin.py` are optional utilities, not files required for every run.
- Backups are useful for recovery but are not required by the running application. Keep database backups separately from the main source-code folder.
