import sqlite3
import os

db_path = r'd:\Projects\CrimeRakshak\android-app\app\src\main\assets\databases\crimerakshak.db'
if not os.path.exists(db_path):
    print(f"DB not found: {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("SELECT sql FROM sqlite_master WHERE type='table';")
for row in cursor.fetchall():
    if row[0]:
        print(row[0])
