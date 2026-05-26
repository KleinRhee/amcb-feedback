import sqlite3
import os
import csv
import io
from flask import Flask, render_template, request, redirect, url_for, session, flash, g, Response
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# Initialize the Flask application
app = Flask(__name__)

# Security key required for session management (logging in/out securely)
app.secret_key = 'amcb_secure_secret_key_2026'

# Path to our local SQLite database file
DATABASE = 'amcb_feedback.db'

# ---------------------------------------------------------------------------
# DATABASE CONFIGURATION & HELPER FUNCTIONS
# ---------------------------------------------------------------------------

def get_db():
    """Opens a new database connection if there is none yet for the current application context."""
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        # This allows us to access columns by name (e.g., row['username'])
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    """Closes the database connection at the end of every request."""
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    """Creates the database tables and seeds default IT accounts."""
    # We use app.app_context() to safely interact with the DB during startup
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        
        # Create Users table (For IT Staff)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL
            )
        ''')
        
        # Create Feedback table (To store all patient responses)
        # Note: patient_name and room_number are NULLable because Out-Patients don't have them.
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                form_type TEXT NOT NULL, 
                admin_user_id INTEGER NOT NULL,
                department TEXT NOT NULL,
                date_admission TEXT NOT NULL,
                contact_number TEXT,
                rating_1 INTEGER,
                rating_2 INTEGER,
                rating_3 INTEGER,
                rating_4 INTEGER,
                rating_5 INTEGER,
                compliments TEXT,
                complaints TEXT,
                recommend TEXT,
                source TEXT,
                patient_name TEXT,
                room_number TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (admin_user_id) REFERENCES users (id)
            )
        ''')
        
        # --- SEED DEFAULT IT ACCOUNTS ---
        # Check if users already exist so we don't duplicate them
        cursor.execute("SELECT COUNT(*) as count FROM users")
        if cursor.fetchone()['count'] == 0:
            print("Seeding default IT Admin accounts...")
            # Generate secure hashes for the password 'password123'
            default_password = generate_password_hash('password123')
            default_users = [
                ('it_admin1', default_password),
                ('it_admin2', default_password),
                ('it_super', default_password)
            ]
            cursor.executemany("INSERT INTO users (username, password_hash) VALUES (?, ?)", default_users)
        
        db.commit()

# Run the database initialization immediately when the app starts
init_db()

# ---------------------------------------------------------------------------
# HARDCODED DATA
# ---------------------------------------------------------------------------

DEPARTMENTS = [
    "Accounting", "Auxiliary", "Clinical Laboratory", "Diagnostic & Imaging Services",
    "Emergency Room", "Engineering and Maintenance", "Finance", "Food Industry",
    "Health Information Management", "HPC", "Housekeeping", "Human Resource",
    "Information Technology Services", "Marketing", "Nutribites", "Operating Room",
    "Outpatient Health & Wellness Hub", "Patient Business", "Patient Care Unit 1",
    "Patient Care Unit 2", "Patient Care Unit 3", "Pharmacy", "PT Rehab", "QC",
    "Renal Care", "Supply Management Office"
]

RATING_QUESTIONS = [
    "Staff demonstrated honesty and professionalism",
    "Staff showed empathy, care, and respect.",
    "Concerns were handled responsibly and promptly.",
    "Needs were attended to efficiently",
    "Overall satisfaction with service received."
]

# ---------------------------------------------------------------------------
# ROUTES & LOGIC
# ---------------------------------------------------------------------------

@app.route('/')
def index():
    """Root route: Redirects to dashboard if logged in, else to login page."""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handles the IT Staff login process."""
    if request.method == 'POST':
        # Grab data from the HTML form
        username = request.form['username']
        password = request.form['password']
        
        db = get_db()
        # Look for the user in the database
        user = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        
        # Verify user exists AND password matches the stored hash
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid username or password. Please try again.", "error")
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logs out the IT Staff by clearing the session."""
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    """Main hub for IT staff to select which form to generate."""
    # Protect route: must be logged in
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    return render_template('dashboard.html', username=session['username'])

@app.route('/form/<form_type>')
def render_feedback_form(form_type):
    """Renders either the Out-Patient or In-Patient form based on the URL."""
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    # Validate form type
    if form_type not in ['in-patient', 'out-patient']:
        return "Invalid Form Type", 400
        
    return render_template('form.html', 
                           form_type=form_type, 
                           departments=DEPARTMENTS, 
                           questions=RATING_QUESTIONS)

@app.route('/submit_feedback', methods=['POST'])
def submit_feedback():
    """Receives data from the form and saves it to the database."""
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    db = get_db()
    
    # Extract data from the submitted form
    form_type = request.form.get('form_type')
    department = request.form.get('department')
    date_admission = request.form.get('date_admission')
    contact_number = request.form.get('contact_number')
    
    # Extract ratings (converting strings to integers)
    rating_1 = int(request.form.get('rating_0', 0)) # Using index 0 from loop
    rating_2 = int(request.form.get('rating_1', 0))
    rating_3 = int(request.form.get('rating_2', 0))
    rating_4 = int(request.form.get('rating_3', 0))
    rating_5 = int(request.form.get('rating_4', 0))
    
    compliments = request.form.get('compliments')
    complaints = request.form.get('complaints')
    recommend = request.form.get('recommend')
    
    # Sources are checkboxes, so they come as a list. We join them into a comma-separated string.
    sources_list = request.form.getlist('source[]')
    source = ", ".join(sources_list)
    
    # These only exist in the In-Patient form, so we use .get() which returns None if missing
    patient_name = request.form.get('patient_name', None)
    room_number = request.form.get('room_number', None)
    
    # Insert everything into the database
    db.execute('''
        INSERT INTO feedback 
        (form_type, admin_user_id, department, date_admission, contact_number, 
         rating_1, rating_2, rating_3, rating_4, rating_5, 
         compliments, complaints, recommend, source, patient_name, room_number)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (form_type, session['user_id'], department, date_admission, contact_number,
          rating_1, rating_2, rating_3, rating_4, rating_5,
          compliments, complaints, recommend, source, patient_name, room_number))
          
    db.commit()
    
    # Redirect to the thank you page
    return redirect(url_for('thank_you'))

@app.route('/thank-you')
def thank_you():
    """Displays the thank you page with a hidden reset button for IT."""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('thank_you.html')

@app.route('/admin')
@app.route('/admin')
def admin_analytics():
    """Displays the backend analytics with data prepared for Chart.js."""
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    db = get_db()
    
    # 1. TOTAL FEEDBACK COUNT
    total_feedback = db.execute("SELECT COUNT(*) as count FROM feedback").fetchone()['count']
    
    # 2. IT STAFF BREAKDOWN (Leaderboard)
    staff_breakdown = [dict(row) for row in db.execute('''
        SELECT users.username, COUNT(feedback.id) as count
        FROM users
        LEFT JOIN feedback ON users.id = feedback.admin_user_id
        GROUP BY users.username
        ORDER BY count DESC
    ''').fetchall()]
    
    # 3. RECENT COMMENTS (For the table)
    recent_comments = [dict(row) for row in db.execute('''
        SELECT department, compliments, complaints 
        FROM feedback 
        WHERE compliments != '' OR complaints != '' 
        ORDER BY timestamp DESC LIMIT 8
    ''').fetchall()]
    
    # 4. AVERAGE RATINGS (For the Bar Chart)
    # We calculate the average of columns rating_1 through rating_5
    avg_row = db.execute('''
        SELECT 
            AVG(rating_1) as r1, AVG(rating_2) as r2,
            AVG(rating_3) as r3, AVG(rating_4) as r4, AVG(rating_5) as r5
        FROM feedback
    ''').fetchone()
    
    # Safely round the averages (or default to 0 if the database is empty)
    avg_ratings = [
        round(avg_row['r1'] or 0, 1), round(avg_row['r2'] or 0, 1),
        round(avg_row['r3'] or 0, 1), round(avg_row['r4'] or 0, 1), round(avg_row['r5'] or 0, 1)
    ]
    # Rating 5 is "Overall Satisfaction", so we'll highlight it!
    overall_avg = round(avg_row['r5'] or 0, 1)
    
    # 5. DEPARTMENT BREAKDOWN (For the Doughnut Chart)
    dept_rows = db.execute('SELECT department, COUNT(*) as count FROM feedback GROUP BY department').fetchall()
    dept_labels = [row['department'] for row in dept_rows]
    dept_counts = [row['count'] for row in dept_rows]
    
    # 6. RECOMMENDATION RATE (For the Pie Chart)
    rec_rows = db.execute('SELECT recommend, COUNT(*) as count FROM feedback GROUP BY recommend').fetchall()
    rec_labels = [row['recommend'] for row in rec_rows]
    rec_counts = [row['count'] for row in rec_rows]
    
    # Calculate exactly what percentage said "Yes"
    yes_count = next((r['count'] for r in rec_rows if r['recommend'] == 'Yes'), 0)
    recommend_percent = int((yes_count / total_feedback * 100)) if total_feedback > 0 else 0
    
    # 7. SOURCE BREAKDOWN (For the Bar Chart)
    # Because sources are saved as a comma-separated string (e.g., "Newspaper, Social Media"), 
    # we have to split them up in Python to count them individually.
    all_sources = db.execute("SELECT source FROM feedback WHERE source != ''").fetchall()
    source_dict = {}
    for row in all_sources:
        sources = [s.strip() for s in row['source'].split(',')]
        for s in sources:
            if s:
                source_dict[s] = source_dict.get(s, 0) + 1
                
    source_labels = list(source_dict.keys())
    source_counts = list(source_dict.values())
    
    # Pass everything to the HTML template!
    return render_template('analytics.html', 
                           total_feedback=total_feedback,
                           overall_avg=overall_avg,
                           recommend_percent=recommend_percent,
                           staff_breakdown=staff_breakdown,
                           recent_comments=recent_comments,
                           avg_ratings=avg_ratings,
                           dept_labels=dept_labels,
                           dept_counts=dept_counts,
                           rec_labels=rec_labels,
                           rec_counts=rec_counts,
                           source_labels=source_labels,
                           source_counts=source_counts)

@app.route('/export')
def export_csv():
    """Exports all feedback database rows to a downloadable CSV file."""
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    db = get_db()
    # Join feedback with users to get the actual username of the IT staff
    data = db.execute('''
        SELECT f.id, f.form_type, u.username as it_staff, f.department, f.date_admission, 
               f.contact_number, f.rating_1, f.rating_2, f.rating_3, f.rating_4, f.rating_5,
               f.compliments, f.complaints, f.recommend, f.source, f.patient_name, f.room_number, f.timestamp
        FROM feedback f
        JOIN users u ON f.admin_user_id = u.id
        ORDER BY f.timestamp DESC
    ''').fetchall()
    
    # Create an in-memory text buffer
    si = io.StringIO()
    writer = csv.writer(si)
    
    # Write the CSV Header Row
    writer.writerow(['ID', 'Form Type', 'Administered By (IT Staff)', 'Department', 'Date of Admission', 
                     'Contact Number', 'Q1_Honesty', 'Q2_Empathy', 'Q3_Responsibility', 'Q4_Efficiency', 
                     'Q5_Overall', 'Compliments', 'Complaints', 'Recommend', 'Source', 
                     'Patient Name (In-Patient)', 'Room Number (In-Patient)', 'Timestamp'])
    
    # Write the actual data rows
    for row in data:
        writer.writerow([row['id'], row['form_type'], row['it_staff'], row['department'], row['date_admission'],
                         row['contact_number'], row['rating_1'], row['rating_2'], row['rating_3'], row['rating_4'],
                         row['rating_5'], row['compliments'], row['complaints'], row['recommend'], row['source'],
                         row['patient_name'], row['room_number'], row['timestamp']])
                         
    # Create HTTP response to force a file download
    output = Response(si.getvalue(), mimetype='text/csv')
    output.headers["Content-Disposition"] = f"attachment; filename=amcb_feedback_export_{datetime.now().strftime('%Y%m%d')}.csv"
    return output

# This block ensures the server runs on all local network IP addresses (0.0.0.0)
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)