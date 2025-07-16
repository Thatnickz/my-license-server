# hwid_server.py (Version 3 - PermissionError Fix)
from flask import Flask, request, jsonify
import sqlite3
import os

app = Flask(__name__)
DB_FILE = os.path.join("/var/data", "hwid_allowlist.db")
ADMIN_SECRET_KEY = "change-this-to-a-very-long-and-random-password"

def db_connection():
    # --- THIS IS THE FIX ---
    # The os.makedirs line has been removed.
    # We trust that Render has created the /var/data directory for us.
    # sqlite3.connect is smart enough to create the file inside the existing directory.
    return sqlite3.connect(DB_FILE)

def setup_database():
    conn = db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS approved_hwids (
            id INTEGER PRIMARY KEY AUTOINCREMENT, hwid TEXT NOT NULL UNIQUE, name TEXT,
            is_active INTEGER DEFAULT 1, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    conn.close()
    print("Database checked and ready.")

# --- All other functions (/check, /add, /list, /deactivate) are unchanged ---

@app.route('/check', methods=['POST'])
def check_hwid():
    data = request.get_json(); hwid = data.get('hwid')
    if not hwid: return jsonify({"status": "error", "message": "HWID not provided"}), 400
    conn = db_connection(); cursor = conn.cursor()
    cursor.execute("SELECT * FROM approved_hwids WHERE hwid = ? AND is_active = 1", (hwid,))
    record = cursor.fetchone(); conn.close()
    if record: return jsonify({"status": "success", "message": "HWID is authorized"})
    else: return jsonify({"status": "error", "message": "HWID not authorized"}), 403

@app.route('/add', methods=['POST'])
def add_hwid():
    data = request.get_json(); secret = data.get('secret'); hwid = data.get('hwid'); name = data.get('name', 'Unnamed User')
    if secret != ADMIN_SECRET_KEY: return jsonify({"status": "error", "message": "Invalid secret key"}), 401
    if not hwid: return jsonify({"status": "error", "message": "HWID not provided"}), 400
    try:
        conn = db_connection(); cursor = conn.cursor()
        cursor.execute("INSERT INTO approved_hwids (hwid, name, is_active) VALUES (?, ?, 1) ON CONFLICT(hwid) DO UPDATE SET is_active=1, name=excluded.name", (hwid, name))
        conn.commit(); conn.close()
        return jsonify({"status": "success", "message": f"Added or reactivated {hwid} for {name}"})
    except sqlite3.Error as e: return jsonify({"status": "error", "message": str(e)})

@app.route('/list', methods=['POST'])
def list_hwids():
    data = request.get_json()
    if data.get('secret') != ADMIN_SECRET_KEY:
        return jsonify({"status": "error", "message": "Invalid secret key"}), 401
    conn = db_connection(); conn.row_factory = sqlite3.Row; cursor = conn.cursor()
    cursor.execute("SELECT id, hwid, name, is_active, created_at FROM approved_hwids ORDER BY id")
    records = cursor.fetchall(); conn.close()
    user_list = [dict(row) for row in records]
    return jsonify({"status": "success", "users": user_list})

@app.route('/deactivate', methods=['POST'])
def deactivate_hwid():
    data = request.get_json()
    if data.get('secret') != ADMIN_SECRET_KEY:
        return jsonify({"status": "error", "message": "Invalid secret key"}), 401
    hwid_to_deactivate = data.get('hwid')
    if not hwid_to_deactivate: return jsonify({"status": "error", "message": "HWID not provided"}), 400
    conn = db_connection(); cursor = conn.cursor()
    cursor.execute("UPDATE approved_hwids SET is_active = 0 WHERE hwid = ?", (hwid_to_deactivate,))
    conn.commit()
    message = f"Successfully deactivated HWID: {hwid_to_deactivate}" if cursor.rowcount > 0 else f"Could not find HWID to deactivate: {hwid_to_deactivate}"
    conn.close()
    return jsonify({"status": "success", "message": message})

# Run the setup function when the server starts
setup_database()
