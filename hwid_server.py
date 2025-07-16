# hwid_server.py
from flask import Flask, request, jsonify
import sqlite3
import os

app = Flask(__name__)
DB_FILE = os.path.join(os.path.dirname(__file__), "hwid_allowlist.db")

# !!! IMPORTANT: Change this to your own secret key! Make it long and random. !!!
ADMIN_SECRET_KEY = "change-this-to-a-very-long-and-random-password"

def db_connection():
    return sqlite3.connect(DB_FILE)

def setup_database():
    if not os.path.exists(DB_FILE):
        conn = db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS approved_hwids (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hwid TEXT NOT NULL UNIQUE,
                name TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()
        conn.close()
        print("Database created.")

@app.route('/check', methods=['POST'])
def check_hwid():
    data = request.get_json()
    hwid = data.get('hwid')
    if not hwid: return jsonify({"status": "error", "message": "HWID not provided"}), 400
    
    conn = db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM approved_hwids WHERE hwid = ? AND is_active = 1", (hwid,))
    record = cursor.fetchone()
    conn.close()
    
    if record: return jsonify({"status": "success", "message": "HWID is authorized"})
    else: return jsonify({"status": "error", "message": "HWID not authorized"}), 403

@app.route('/add', methods=['POST'])
def add_hwid():
    data = request.get_json()
    secret = data.get('secret')
    hwid = data.get('hwid')
    name = data.get('name', 'Unnamed User')

    if secret != ADMIN_SECRET_KEY:
        return jsonify({"status": "error", "message": "Invalid secret key"}), 401
    if not hwid:
        return jsonify({"status": "error", "message": "HWID not provided"}), 400

    try:
        conn = db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO approved_hwids (hwid, name) VALUES (?, ?)", (hwid, name))
        conn.commit()
        conn.close()
        return jsonify({"status": "success", "message": f"Added {hwid} for {name}"})
    except sqlite3.IntegrityError:
        return jsonify({"status": "error", "message": f"HWID {hwid} already exists"})

# This ensures the database is created when the server starts
setup_database()