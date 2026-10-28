"""Create the first Airforce School administrator without storing a plain password."""
from getpass import getpass
import os

import mysql.connector
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

load_dotenv()

name = input("Administrator name: ").strip()
email = input("Administrator email: ").strip().lower()
password = getpass("Choose a password (at least 8 characters): ")
confirmation = getpass("Enter it again: ")

if not name or not email or len(password) < 8 or password != confirmation:
    print("Please enter a name and email, use 8+ characters, and make both passwords match.")
    raise SystemExit(1)

connection = mysql.connector.connect(
    host=os.getenv("DB_HOST", "localhost"),
    user=os.getenv("DB_USER", "root"),
    password=os.getenv("DB_PASSWORD", ""),
    database=os.getenv("DB_NAME", "gradesphere"),
)
cursor = connection.cursor()
try:
    cursor.execute(
        "INSERT INTO users (full_name, email, password_hash, role) VALUES (%s, %s, %s, 'administrator')",
        (name, email, generate_password_hash(password)),
    )
    connection.commit()
    print("Administrator account created. Sign in to Airforce School.")
except mysql.connector.IntegrityError:
    connection.rollback()
    print("That email already has an Airforce School account.")
finally:
    cursor.close()
    connection.close()
