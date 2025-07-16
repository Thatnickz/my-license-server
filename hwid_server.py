# hwid_server.py (Corrected for Render's Persistent Disk)
from flask import Flask, request, jsonify
import sqlite3
import os

app = Flask(__name__)

# --- CRITICAL FIX ---
# This path points to the persistent disk on Render, so your database will NOT be erased.
DB_FILE = os.path.join("/var/data", "hwid_allowlist.db") 

# This is your secret key for adding new users.
ADMIN_SECRET_KEY = "change-this-to-a-very-long-and-random-password"

def db_connection():
    # Ensure the directory for the database exists.
    os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
    return sqlite3.connect(DB_FILE)

def setup_database():
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
    print("Database checked and ready.")

@app.route('/check', methods=['POST'])
def check_hwid():
    # ... (This function is unchanged and correct) ...
    data = request.get_json(); hwid = data.get('hwid')
    if not hwid: return jsonify({"status": "error", "message": "HWID not provided"}), 400
    conn = db_connection(); cursor = conn.cursor()
    cursor.execute("SELECT * FROM approved_hwids WHERE hwid = ? AND is_active = 1", (hwid,))
    record = cursor.fetchone(); conn.close()
    if record: return jsonify({"status": "success", "message": "HWID is authorized"})
    else: return jsonify({"status": "error", "message": "HWID not authorized"}), 403

@app.route('/add', methods=['POST'])
def add_hwid():
    # ... (This function is unchanged and correct) ...
    data = request.get_json(); secret = data.get('secret'); hwid = data.get('hwid'); name = data.get('name', 'Unnamed User')
    if secret != ADMIN_SECRET_KEY: return jsonify({"status": "error", "message": "Invalid secret key"}), 401
    if not hwid: return jsonify({"status": "error", "message": "HWID not provided"}), 400
    try:
        conn = db_connection(); cursor = conn.cursor()
        cursor.execute("INSERT INTO approved_hwids (hwid, name) VALUES (?, ?)", (hwid, name))
        conn.commit(); conn.close()
        return jsonify({"status": "success", "message": f"Added {hwid} for {name}"})
    except sqlite3.IntegrityError: return jsonify({"status": "error", "message": f"HWID {hwid} already exists"})

# Run the setup function when the server starts
setup_database()
