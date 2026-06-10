# 🏥 AMC-B Patient Feedback System

![Version](https://img.shields.io/badge/Version-1.0_MVP-blue)
![Status](https://img.shields.io/badge/Status-Production_Ready-success)
![Platform](https://img.shields.io/badge/Platform-Windows_|_Mac_|_Linux-lightgrey)

A high-performance, responsive, and DPA-compliant digital feedback web application developed for the **Information Technology Services Department** of **Adventist Medical Center - Bacolod (AMC-B)**. 

This system replaces paper feedback forms with a secure, tablet/mobile-friendly digital interface. It features dynamic routing for In-Patient vs. Out-Patient contexts, digital signature capture, and a robust Admin Analytics dashboard for real-time service monitoring.

---

## 🛑 PHASE 1: Prerequisites (First-Time PC Setup)
If this is a brand new Windows computer, you must install Python before running this application.

**1. Install Python (CRITICAL STEP)**
1. Go to the official Python website: [https://www.python.org/downloads/windows/](https://www.python.org/downloads/windows/)
2. Click **"Download Python 3.12"** (or the newest stable version).
3. Open the downloaded `.exe` installer.
4. ⚠️ **EXTREMELY IMPORTANT:** At the very bottom of the installer window, **check the box that says "Add Python to PATH"** before you click Install. If you do not check this box, Windows will not know how to run Python commands!
5. Click **Install Now**.

**2. Get the Application Files**
You can get the application files in two ways:
* **Option A (If you have Git installed):** Open Command Prompt and type: `git clone https://github.com/YOUR_USERNAME/amcb-feedback.git`
* **Option B (No Git required):** Go to the GitHub repository page, click the green **"<> Code"** button, select **"Download ZIP"**, and extract the folder to your Desktop or Documents.

---

## 🛠️ PHASE 2: Step-by-Step Installation
Open your Windows **Command Prompt** (Press `Win + R`, type `cmd`, and hit Enter). Follow these exact commands to securely set up the app.

**1. Navigate to the project folder:**
*(Change the path below to wherever you saved or extracted the folder)*
```cmd
cd Desktop\amcb-feedback
```

**2. Create a Virtual Environment:**
*(This creates an isolated "bubble" so the app's files don't interfere with the rest of your Windows system).*
```cmd
python -m venv venv
```

**3. Activate the Virtual Environment:**
*(You must do this every time before running or installing things. You will know it worked when `(venv)` appears on the left side of your terminal).*
```cmd
venv\Scripts\activate
```

**4. Install the Required Software:**
*(This downloads the web framework, security tools, and the production server).*
```cmd
pip install Flask Werkzeug waitress
```

---

## 🚀 PHASE 3: Running the Application

Ensure you are in your project folder and your virtual environment is active `(venv)`.

**1. Start the Server:**
```cmd
python app.py
```
*You will see a message saying "AMC-B FEEDBACK SYSTEM RUNNING IN PRODUCTION MODE". The server is now live!*

**2. How to Access the App:**
* **From this exact PC:** Open Google Chrome or Microsoft Edge and go to: `http://localhost:5001`
* **From a Hospital iPad / Mobile Phone:** Look at the terminal output. It will tell you your PC's Network IP address (e.g., `http://192.168.1.50:5001`). Type that exact address into any phone connected to the hospital Wi-Fi. 
* **The Magic QR Code:** You can also just open `http://localhost:5001` on the PC, and scan the QR Code on the screen with your phone's camera!

---

## 🔑 Default IT Credentials
On the first run, the system automatically generated a local database (`amcb_feedback.db`) and seeded three default accounts. 

**Super Admin (Has access to System Config & Data Audit):**
* **Username:** `it_super`
* **Password:** `password123`

**Standard Admins (Can generate forms & view analytics):**
* **Username:** `it_admin1` / `it_admin2`
* **Password:** `password123`

*(Note: Staff can securely change their passwords via their Dashboard).*

---

## 🗄️ Database Migration Guide (Microsoft SQL Server)

This MVP is currently using a local SQLite file (`amcb_feedback.db`) for immediate testing, but it was architected specifically to be migrated to AMC-B's main **Microsoft SQL Server (MSSQL)** environment. 

The backend utilizes standard SQL logic and parameterized (`?`) queries to prevent SQL Injection. The transition to MSSQL is 95% complete out-of-the-box.

When the Database Team is ready to migrate the application, follow these 3 steps:

### 1. View Current Schema
You can inspect the current local database layout by downloading **DBeaver Community Edition**, creating a New SQLite Connection, and opening the `amcb_feedback.db` file.

### 2. SQL Schema Adjustments
When manually creating the tables in your MSSQL Server, please note these two dialect translations:
* Change SQLite's `INTEGER PRIMARY KEY AUTOINCREMENT` to MSSQL's `INT IDENTITY(1,1) PRIMARY KEY`.
* Ensure the `signature` column is assigned `VARCHAR(MAX)` to safely hold Base64 PNG image strings.

### 3. Update `app.py` Connections
The Backend Developer will need to install the Microsoft ODBC driver to the virtual environment:
```cmd
pip install pyodbc
```
Next, locate `def get_db():` at the top of `app.py`. Delete the `sqlite3` lines and replace them with `pyodbc`:
```python
import pyodbc

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        conn_str = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=amcb-db-server;DATABASE=Feedback_DB;UID=admin;PWD=password;"
        db = g._database = pyodbc.connect(conn_str)
        # Note: Depending on your pyodbc setup, you may need to map the cursor tuples to dictionaries for the Jinja templates.
    return db
```

**⚠️ Important Analytics Note:**
In the `/admin` route of `app.py`, the dynamic Month Filter relies on SQLite's native `strftime` function. Upon migrating to MSSQL, simply update that specific SQL string to use MSSQL's format engine: 
* *Change:* `strftime('%Y-%m', timestamp)`
* *To:* `FORMAT(timestamp, 'yyyy-MM')`

---

## 🎨 Frontend Re-compilation (Optional)
The styling is completely self-contained in `static/output.css`, allowing the app to run 100% offline without CDNs. If future developers wish to change the AMC-B brand colors, modify the Star Rating logic, or alter the UI, they must use Node.js to recompile the Tailwind CSS.

1. Download and Install Node.js for Windows.
2. In the project terminal, run: `npm install -D tailwindcss@3`.
3. Make changes to `tailwind.config.js` or `static/input.css`.
4. Compile the new styling:
   ```cmd
   npx tailwindcss -i ./static/input.css -o ./static/output.css --minify
   ```

---
*Developed as an Elite OJT Project for the Information Technology Services Department of AMC-B. Designed with a strict focus on Data Privacy (DPA/RA 10173), robust network security, and modern Human-Computer Interaction (HCI) standards.*