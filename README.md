# 🏥 AMC-B Patient Feedback System

![Version](https://img.shields.io/badge/Version-1.0_MVP-blue)
![Status](https://img.shields.io/badge/Status-Production_Ready-success)
![Platform](https://img.shields.io/badge/Platform-Cross_Platform-lightgrey)

A high-performance, responsive, and DPA-compliant digital feedback web application developed for the **Information Technology Services Department** of **Adventist Medical Center - Bacolod (AMC-B)**. 

This system replaces paper feedback forms with a secure, tablet/mobile-friendly digital interface. It features dynamic routing for In-Patient vs. Out-Patient contexts, digital signature capture, and a robust Admin Analytics dashboard for real-time service monitoring.

---

## 🚀 Key Features
* **Enterprise Security:** Parameterized SQL queries (SQLi protection), `Werkzeug` password hashing, and a strict DPA (Data Privacy Act of 2012) compliance workflow.
* **Production Web Server:** Powered by **Waitress**, capable of handling highly concurrent network requests securely over the hospital Intranet.
* **HCI-Optimized UI/UX:** Designed following strict Human-Computer Interaction (HCI) principles. Features fluid typography, Apple/Material-style glassmorphism, progressive disclosure, and a responsive "F-Pattern" layout.
* **100% Offline Capability:** Tailwind CSS has been fully pre-compiled via Node CLI. No external CDNs are required, ensuring the app runs flawlessly on isolated hospital Intranets.
* **Data Audit Trail:** An exclusive `it_super` portal for auditing records, tracking digital signatures (Base64), archiving mistaken inputs, and permanently wiping fake data.
* **Instant Mobile Connect:** Auto-generates a QR Code on the PC Login screen. Staff can simply scan it with a hospital tablet/phone to instantly open the form without typing IP addresses.

---

## 🛠️ Technology Stack
* **Backend:** Python 3.12+, Flask, Waitress (WSGI Server)
* **Database:** SQLite3 (Pre-configured for seamless Microsoft SQL Server migration)
* **Frontend:** HTML5, Vanilla JavaScript, Tailwind CSS v3 (Locally Compiled)
* **Libraries:** Chart.js (Analytics), Signature_Pad.js (Digital Canvas)

---

## 💻 Windows Installation & Quick Start

The app is currently configured with a zero-setup SQLite database for immediate testing. 

**1. Clone the Repository**
Open Command Prompt or PowerShell on your Windows Server/PC:
```cmd
git clone https://github.com/YOUR_USERNAME/amcb-feedback.git
cd amcb-feedback
```

**2. Set up the Python Environment**
It is highly recommended to run this inside an isolated virtual environment.
```cmd
python -m venv venv
venv\Scripts\activate
```

**3. Install Dependencies**
```cmd
pip install Flask Werkzeug waitress
```

**4. Run the Production Server**
```cmd
python app.py
```
*The terminal will output the exact `http://` Local Network IP address. You can type this address into any hospital iPad or mobile phone connected to the same Wi-Fi network.*

---

## 🔑 Default IT Credentials
On the first run, the system will automatically generate a blank database (`amcb_feedback.db`) and seed three default accounts. 

**Super Admin (Has access to System Config & Data Audit):**
* **Username:** `it_super`
* **Password:** `password123`

**Standard Admins (Can generate forms & view analytics):**
* **Username:** `it_admin1` / `it_admin2`
* **Password:** `password123`

*(Note: Any user can securely change their password via the Dashboard).*

---

## 🗄️ Database Migration Guide (Microsoft SQL Server)

This MVP was architected specifically to be migrated to AMC-B's main **Microsoft SQL Server (MSSQL)** environment. The backend utilizes standard SQL logic and parameterized (`?`) queries, making the transition 95% complete out-of-the-box.

When the Database Team is ready to migrate the application, follow these 3 steps:

### 1. View Current Schema
You can inspect the current local database by downloading **DBeaver Community Edition** and connecting it to the `amcb_feedback.db` file. 

### 2. SQL Schema Adjustments
When creating the tables in MSSQL, please note the following dialect translations:
* Change SQLite's `INTEGER PRIMARY KEY AUTOINCREMENT` to MSSQL's `INT IDENTITY(1,1) PRIMARY KEY`.
* Ensure the `signature` column is assigned `VARCHAR(MAX)` to safely hold Base64 PNG strings.

### 3. Update `app.py`
The Backend Developer will need to install the Microsoft ODBC driver and swap the connection string:
```cmd
pip install pyodbc
```
Locate `def get_db():` in `app.py` and replace the `sqlite3` connection with `pyodbc`:
```python
import pyodbc

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        conn_str = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=amcb-server;DATABASE=Feedback_DB;UID=admin;PWD=password;"
        db = g._database = pyodbc.connect(conn_str)
        # Note: Map pyodbc cursor tuples to dictionaries for Jinja compatibility
    return db
```

**⚠️ Important Analytics Note:**
In the `/admin` route of `app.py`, the dynamic Month filter relies on SQLite's `strftime` function. Upon migrating to MSSQL, simply update that specific SQL string to use MSSQL's format engine: 
* *Change:* `strftime('%Y-%m', timestamp)`
* *To:* `FORMAT(timestamp, 'yyyy-MM')`

---

## 🎨 Frontend Re-compilation (Optional)
The CSS is completely self-contained in `static/output.css`. If future developers wish to change the AMC-B brand colors or alter the UI, they must use Node.js to recompile the Tailwind CSS.

1. Install Node.js.
2. Run `npm install -D tailwindcss@3`.
3. Make changes to `tailwind.config.js` or `static/input.css`.
4. Compile the new styling:
   ```cmd
   npx tailwindcss -i ./static/input.css -o ./static/output.css --minify
   ```

---
*Developed as a capstone OJT Project for the Information Technology Services Department of AMC-B. Designed with a strict focus on data integrity, operational speed, and human-centered design.*