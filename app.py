import sqlite3
import os
import csv
import io
import socket
import re
from waitress import serve  # <-- NEW: Production Server
from flask import Flask, render_template, request, redirect, url_for, session, flash, g, Response, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'amcb_secure_secret_key_2026_production'
DATABASE = 'amcb_feedback.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None: db.close()

def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS feedback (id INTEGER PRIMARY KEY AUTOINCREMENT, form_type TEXT NOT NULL, admin_user_id INTEGER NOT NULL, department TEXT NOT NULL, date_admission TEXT NOT NULL, contact_number TEXT, rating_1 INTEGER, rating_2 INTEGER, rating_3 INTEGER, rating_4 INTEGER, rating_5 INTEGER, compliments TEXT, complaints TEXT, recommend TEXT, source TEXT, patient_name TEXT, room_number TEXT, timestamp DATETIME, signature TEXT, status TEXT DEFAULT 'active', FOREIGN KEY (admin_user_id) REFERENCES users (id))''')
        
        try: cursor.execute("ALTER TABLE feedback ADD COLUMN status TEXT DEFAULT 'active'")
        except: pass 
        try: cursor.execute("ALTER TABLE feedback ADD COLUMN signature TEXT")
        except: pass

        cursor.execute("SELECT COUNT(*) as count FROM users")
        if cursor.fetchone()['count'] == 0:
            default_password = generate_password_hash('password123')
            default_users = [('it_admin1', default_password), ('it_admin2', default_password), ('it_super', default_password)]
            cursor.executemany("INSERT INTO users (username, password_hash) VALUES (?, ?)", default_users)
        db.commit()

init_db()

IN_PATIENT_DEPARTMENTS = ["ER", "HPC", "ICU", "IM-OPD", "ISOLATION", "LR/DR", "NICU", "OPD", "OR", "PCU1", "PCU2", "PCU3A", "PCU3B", "PCU4A", "PCU4B", "PCU5A", "PCU5B", "PICU", "PT/REHAB", "RCU"]
OUT_PATIENT_DEPARTMENTS = ["Accounting", "Auxiliary", "Clinical Laboratory", "Diagnostic & Imaging Services", "Emergency Room", "Engineering and Maintenance", "Finance", "Food Industry", "Health Information Management", "HPC", "Housekeeping", "Human Resource", "Information Technology Services", "Marketing", "Nutribites", "Operating Room", "Outpatient Health & Wellness Hub", "Patient Business", "Pharmacy", "PT Rehab", "QC", "Renal Care", "Supply Management Office"]
RATING_QUESTIONS = ["Staff demonstrated honesty and professionalism", "Staff showed empathy, care, and respect.", "Concerns were handled responsibly and promptly.", "Needs were attended to efficiently", "Overall satisfaction with service received."]

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception: return "127.0.0.1"

@app.route('/favicon.ico')
def favicon():
    """FIX: Satisfies Chrome's automatic request for a tab icon, preventing 404 errors in the console."""
    return send_from_directory(os.path.join(app.root_path, 'static'), 'logo.png', mimetype='image/png')

@app.route('/')
def index():
    if 'user_id' in session: return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid username or password.", "error")
    return render_template('login.html', mobile_url=f"http://{get_local_ip()}:5001")

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session: return redirect(url_for('login'))
    return render_template('dashboard.html', username=session['username'])

@app.route('/change_password', methods=['POST'])
def change_password():
    if 'user_id' not in session: return redirect(url_for('login'))
    db = get_db()
    user = db.execute("SELECT password_hash FROM users WHERE id = ?", (session['user_id'],)).fetchone()
    if user and check_password_hash(user['password_hash'], request.form['current_password']):
        db.execute("UPDATE users SET password_hash = ? WHERE id = ?", (generate_password_hash(request.form['new_password']), session['user_id']))
        db.commit()
        flash("Password updated successfully!", "success")
    else:
        flash("Incorrect current password.", "error")
    return redirect(url_for('dashboard'))

@app.route('/form/<form_type>')
def render_feedback_form(form_type):
    if 'user_id' not in session: return redirect(url_for('login'))
    departments = IN_PATIENT_DEPARTMENTS if form_type == 'in-patient' else OUT_PATIENT_DEPARTMENTS
    return render_template('form.html', form_type=form_type, departments=departments, questions=RATING_QUESTIONS)

@app.route('/submit_feedback', methods=['POST'])
def submit_feedback():
    if 'user_id' not in session: return redirect(url_for('login'))
    db = get_db()
    data = request.form
    
    # PERFECTED: Forces the exact Local Time of your Mac/System instead of UTC!
    current_local_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    db.execute('''INSERT INTO feedback (form_type, admin_user_id, department, date_admission, contact_number, rating_1, rating_2, rating_3, rating_4, rating_5, compliments, complaints, recommend, source, patient_name, room_number, signature, timestamp, status)
                  VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active')''', 
               (data.get('form_type'), session['user_id'], data.get('department'), data.get('date_admission'), data.get('contact_number'), 
                int(data.get('rating_0', 0)), int(data.get('rating_1', 0)), int(data.get('rating_2', 0)), int(data.get('rating_3', 0)), int(data.get('rating_4', 0)), 
                data.get('compliments'), data.get('complaints'), data.get('recommend'), ", ".join(data.getlist('source[]')), data.get('patient_name', None), data.get('room_number', None), data.get('signature', None), current_local_time))
    db.commit()
    return redirect(url_for('thank_you'))

@app.route('/thank-you')
def thank_you():
    if 'user_id' not in session: return redirect(url_for('login'))
    return render_template('thank_you.html')

@app.route('/admin')
def admin_analytics():
    if 'user_id' not in session: return redirect(url_for('login'))
    db = get_db()
    
    month_filter = request.args.get('month', '').strip()
    tab_filter = request.args.get('tab', 'all').strip()
    
    if month_filter and not re.match(r'^\d{4}-\d{2}$', month_filter): month_filter = ''
    if tab_filter not in ['all', 'in-patient', 'out-patient']: tab_filter = 'all'
        
    base_where = "WHERE status = 'active'"
    params = []
    
    if month_filter:
        base_where += " AND timestamp LIKE ?"
        params.append(f"{month_filter}%")
    if tab_filter != 'all':
        base_where += " AND form_type = ?"
        params.append(tab_filter)
        
    params = tuple(params)

    total_feedback = db.execute(f"SELECT COUNT(*) as count FROM feedback {base_where}", params).fetchone()['count']
    
    staff_query = f"SELECT users.username, COUNT(feedback.id) as count FROM users LEFT JOIN feedback ON users.id = feedback.admin_user_id AND feedback.status = 'active'"
    if month_filter: staff_query += f" AND feedback.timestamp LIKE '{month_filter}%'"
    if tab_filter != 'all': staff_query += f" AND feedback.form_type = '{tab_filter}'"
    staff_query += " GROUP BY users.username ORDER BY count DESC"
    staff_breakdown = [dict(row) for row in db.execute(staff_query).fetchall()]
    
    recent_comments = [dict(row) for row in db.execute(f"SELECT department, compliments, complaints, timestamp FROM feedback {base_where} AND (compliments != '' OR complaints != '') ORDER BY timestamp DESC LIMIT 8", params).fetchall()]
    
    avg_row = db.execute(f"SELECT AVG(rating_1) as r1, AVG(rating_2) as r2, AVG(rating_3) as r3, AVG(rating_4) as r4, AVG(rating_5) as r5 FROM feedback {base_where}", params).fetchone()
    avg_ratings = [round(avg_row['r1'] or 0, 1), round(avg_row['r2'] or 0, 1), round(avg_row['r3'] or 0, 1), round(avg_row['r4'] or 0, 1), round(avg_row['r5'] or 0, 1)]
    overall_avg = round(avg_row['r5'] or 0, 1)
    
    dept_rows = db.execute(f"SELECT department, COUNT(*) as count FROM feedback {base_where} GROUP BY department", params).fetchall()
    rec_rows = db.execute(f"SELECT recommend, COUNT(*) as count FROM feedback {base_where} GROUP BY recommend", params).fetchall()
    yes_count = next((r['count'] for r in rec_rows if r['recommend'] == 'Yes'), 0)
    recommend_percent = int((yes_count / total_feedback * 100)) if total_feedback > 0 else 0
    
    all_sources = db.execute(f"SELECT source FROM feedback {base_where} AND source != ''", params).fetchall()
    source_dict = {}
    for row in all_sources:
        for s in [s.strip() for s in row['source'].split(',')]:
            if s: source_dict[s] = source_dict.get(s, 0) + 1
            
    months_raw = db.execute("SELECT DISTINCT strftime('%Y-%m', timestamp) as month FROM feedback WHERE status = 'active' ORDER BY month DESC").fetchall()
    
    return render_template('analytics.html', total_feedback=total_feedback, overall_avg=overall_avg, recommend_percent=recommend_percent, staff_breakdown=staff_breakdown, recent_comments=recent_comments, avg_ratings=avg_ratings, dept_labels=[row['department'] for row in dept_rows], dept_counts=[row['count'] for row in dept_rows], source_labels=list(source_dict.keys()), source_counts=list(source_dict.values()), available_months=[row['month'] for row in months_raw if row['month']], current_month=month_filter, current_tab=tab_filter)

@app.route('/export')
def export_csv():
    if 'user_id' not in session: return redirect(url_for('login'))
    month_filter = request.args.get('month', '').strip()
    tab_filter = request.args.get('tab', 'all').strip()
    
    if month_filter and not re.match(r'^\d{4}-\d{2}$', month_filter): month_filter = ''
        
    query = "SELECT f.*, u.username FROM feedback f JOIN users u ON f.admin_user_id = u.id WHERE f.status = 'active'"
    params = []
    
    if month_filter: 
        query += " AND f.timestamp LIKE ?"
        params.append(f"{month_filter}%")
    if tab_filter != 'all':
        query += " AND f.form_type = ?"
        params.append(tab_filter)
        
    query += " ORDER BY f.timestamp DESC"
    
    db = get_db()
    data = db.execute(query, tuple(params)).fetchall()
    
    si = io.StringIO()
    writer = csv.writer(si)
    writer.writerow(['ID', 'Form Type', 'Admin', 'Department', 'Date', 'Contact', 'Q1_Honesty', 'Q2_Empathy', 'Q3_Responsibility', 'Q4_Efficiency', 'Q5_Overall', 'Compliments', 'Complaints', 'Recommend', 'Source', 'Patient Name', 'Room Number', 'Timestamp'])
    for row in data: writer.writerow([row['id'], row['form_type'], row['username'], row['department'], row['date_admission'], row['contact_number'], row['rating_1'], row['rating_2'], row['rating_3'], row['rating_4'], row['rating_5'], row['compliments'], row['complaints'], row['recommend'], row['source'], row['patient_name'], row['room_number'], row['timestamp']])
    
    output = Response(si.getvalue(), mimetype='text/csv')
    output.headers["Content-Disposition"] = f"attachment; filename=amcb_export_{tab_filter}_{month_filter or 'ALL'}.csv"
    return output

@app.route('/manage_records')
def manage_records():
    if session.get('username') != 'it_super': return redirect(url_for('dashboard'))
    db = get_db()
    records = db.execute("SELECT f.*, u.username FROM feedback f JOIN users u ON f.admin_user_id = u.id ORDER BY f.timestamp DESC").fetchall()
    return render_template('manage_records.html', records=records)

@app.route('/toggle_record/<int:record_id>/<action>')
def toggle_record(record_id, action):
    if session.get('username') != 'it_super': return redirect(url_for('dashboard'))
    new_status = 'trashed' if action == 'trash' else 'active'
    db = get_db()
    db.execute("UPDATE feedback SET status = ? WHERE id = ?", (new_status, record_id))
    db.commit()
    flash("Record moved to Trash." if new_status == 'trashed' else "Record restored successfully.", "success")
    return redirect(url_for('manage_records'))

@app.route('/hard_delete/<int:record_id>')
def hard_delete(record_id):
    if session.get('username') != 'it_super': return redirect(url_for('dashboard'))
    db = get_db()
    db.execute("DELETE FROM feedback WHERE id = ?", (record_id,))
    db.commit()
    flash("Record permanently deleted.", "success")
    return redirect(url_for('manage_records'))

@app.route('/settings')
def system_settings():
    if session.get('username') != 'it_super': return redirect(url_for('dashboard'))
    db = get_db()
    all_users = db.execute("SELECT id, username FROM users WHERE username != 'it_super'").fetchall()
    return render_template('settings.html', users=all_users, username=session['username'])

@app.route('/add_user', methods=['POST'])
def add_user():
    if session.get('username') != 'it_super': return redirect(url_for('dashboard'))
    new_username = request.form['username'].strip()
    db = get_db()
    try:
        db.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (new_username, generate_password_hash(request.form['password'])))
        db.commit()
        flash(f"User '{new_username}' added successfully!", "success")
    except sqlite3.IntegrityError: flash("Error: Username already exists.", "error")
    return redirect(url_for('system_settings'))

@app.route('/delete_user/<int:user_id>')
def delete_user(user_id):
    if session.get('username') != 'it_super': return redirect(url_for('dashboard'))
    db = get_db()
    db.execute("DELETE FROM users WHERE id = ?", (user_id,))
    db.commit()
    flash("User account securely deleted.", "success")
    return redirect(url_for('system_settings'))

@app.route('/reset_data', methods=['POST'])
def reset_data():
    if session.get('username') != 'it_super': return redirect(url_for('dashboard'))
    db = get_db()
    db.execute("DELETE FROM feedback")
    db.commit()
    flash("System Reset Successful. All feedback data has been wiped.", "success")
    return redirect(url_for('system_settings'))

if __name__ == '__main__':
    # PERFECTED: Replaced Flask Development Server with Waitress Production Server
    # This safely handles concurrent submissions and is 100% Windows-ready!
    
    # Get the local IP to print a helpful message in the terminal
    local_ip = get_local_ip()
    print("=========================================================")
    print(" 🚀 AMC-B FEEDBACK SYSTEM RUNNING IN PRODUCTION MODE 🚀 ")
    print(f" -> Local Mac/PC Access: http://localhost:5001")
    print(f" -> Mobile/Network Access: http://{local_ip}:5001")
    print("=========================================================")
    print("Press CTRL+C to stop the server.")
    
    # Run the app using Waitress
    serve(app, host='0.0.0.0', port=5001)