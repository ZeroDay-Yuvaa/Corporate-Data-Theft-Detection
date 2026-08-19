


from flask import Flask, render_template_string, request, send_file, redirect, url_for, session
import hashlib
import os
import csv
import io
from datetime import datetime
from pypdf import PdfReader

app = Flask(__name__)
app.secret_key = "datashield-demo-secret-key"

# ============================================================
# FOLDERS
# ============================================================

UPLOAD_FOLDER = "uploads"
RECOVERED_FOLDER = "recovered"
REPORT_FOLDER = "reports"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RECOVERED_FOLDER, exist_ok=True)
os.makedirs(REPORT_FOLDER, exist_ok=True)


# ============================================================
# CASE INFORMATION
# ============================================================

CASE = {
    "id": "DF-2026-001",
    "name": "Operation DataShield",
    "organization": "TechNova Solutions",
    "incident": "Corporate Data Theft",
    "status": "Under Investigation",
    "priority": "HIGH"
}


# ============================================================
# SYNTHETIC DELETED FILE EVIDENCE
# ============================================================

FILES = [
    {
        "id": "FILE-001",
        "name": "Confidential_Project.pdf",
        "path": "Documents/Confidential/",
        "type": "PDF",
        "size": "2.4 MB",
        "deleted": "2026-08-16 11:02",
        "status": "Recoverable"
    },
    {
        "id": "FILE-002",
        "name": "Client_Data.xlsx",
        "path": "Documents/Finance/",
        "type": "XLSX",
        "size": "850 KB",
        "deleted": "2026-08-16 11:03",
        "status": "Partially Recoverable"
    },
    {
        "id": "FILE-003",
        "name": "Project_Notes.docx",
        "path": "Documents/",
        "type": "DOCX",
        "size": "320 KB",
        "deleted": "2026-08-16 11:04",
        "status": "Recoverable"
    },
    {
        "id": "FILE-004",
        "name": "Financial_Report.pdf",
        "path": "Documents/Finance/",
        "type": "PDF",
        "size": "1.7 MB",
        "deleted": "2026-08-16 11:05",
        "status": "Unrecoverable"
    },
    {
        "id": "FILE-005",
        "name": "Archive.zip",
        "path": "Temp/",
        "type": "ZIP",
        "size": "4.2 MB",
        "deleted": "2026-08-16 11:06",
        "status": "Recoverable"
    }
]


# ============================================================
# FORENSIC TIMELINE
# ============================================================

TIMELINE = [
    ("09:12 AM", "Workstation Login", "Normal"),
    ("10:05 AM", "Confidential Folder Accessed", "Suspicious"),
    ("10:18 AM", "USB Device Connected", "Suspicious"),
    ("10:24 AM", "Sensitive Files Accessed", "Suspicious"),
    ("10:31 AM", "Archive File Created", "Suspicious"),
    ("10:38 AM", "Browser Activity Detected", "Suspicious"),
    ("10:45 AM", "USB Device Disconnected", "Normal"),
    ("11:02 AM", "Files Deleted", "Suspicious"),
    ("11:20 AM", "Evidence Acquired", "Forensic"),
    ("12:10 PM", "Deleted Files Identified", "Forensic"),
    ("12:25 PM", "Files Recovered", "Forensic")
]


# ============================================================
# CHAIN OF CUSTODY
# ============================================================

CUSTODY = []


# ============================================================
# USER / ADMIN ACCESS & ACTIVITY LOG
# ============================================================

USERS = {
    # Admin credentials are intentionally easy to change here.
    "admin@example.com": {
        "password": "admin123",
        "role": "admin",
        "name": "Administrator",
        "status": "approved"
    }
}

PENDING_USERS = {}

ACTIVITY_LOG = []


def log_activity(action, details=""):
    username = session.get("username", "System")
    role = session.get("role", "system")
    ACTIVITY_LOG.append({
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "username": username,
        "role": role,
        "owner": username,
        "action": action,
        "details": details
    })


def current_user():
    username = session.get("username")
    if username and username in USERS:
        user = USERS[username]
        if user.get("status") == "approved":
            return user
    return None


def require_login():
    if not current_user():
        return redirect(url_for("login"))
    return None


def require_admin():
    user = current_user()
    if not user or user["role"] != "admin":
        return redirect(url_for("login"))
    return None


# ============================================================
# CSV ANALYSIS STORAGE
# ============================================================

CSV_ANALYSIS = {
    "filename": None,
    "hash": None,
    "rows": 0,
    "columns": 0,
    "column_names": [],
    "missing_values": 0,
    "duplicates": 0,
    "suspicious_records": 0,
    "risk_score": 0,
    "risk_level": "Not Analyzed",
    "headers": [],
    "preview": [],
    "findings": []
}


# ============================================================
# BEFORE / AFTER COMPARISON STORAGE
# ============================================================

COMPARISON = {
    "before_file": None,
    "after_file": None,
    "before_hash": None,
    "after_hash": None,
    "status": "Not Analyzed",
    "total_before": 0,
    "total_after": 0,
    "changed": 0,
    "deleted": 0,
    "added": 0,
    "unchanged": 0,
    "changes": []
}


# ============================================================
# CSS
# ============================================================

STYLE = """
<style>

* {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
    font-family: Arial, sans-serif;
}

body {
    background: #071525;
    color: white;
}

.header {
    background: #0d2138;
    padding: 20px 35px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 2px solid #19bfff;
}

.logo {
    font-size: 28px;
    font-weight: bold;
    color: #19cfff;
}

.status {
    color: #39e58c;
    font-weight: bold;
}

nav {
    background: #091a2c;
    padding: 15px 35px;
    border-bottom: 1px solid #1b4868;
    overflow-x: auto;
    white-space: nowrap;
}

nav a {
    color: #d7e7f5;
    text-decoration: none;
    margin-right: 20px;
    font-size: 14px;
}

nav a:hover {
    color: #20cfff;
}

.container {
    width: 94%;
    max-width: 1400px;
    margin: 30px auto;
}

h1 {
    margin-bottom: 8px;
}

h2 {
    color: #20cfff;
    margin-bottom: 15px;
}

h3 {
    margin-bottom: 8px;
}

.subtitle {
    color: #9bb0c5;
    margin-bottom: 30px;
}

.cards {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 18px;
}

.card {
    background: #0d2138;
    border: 1px solid #1b4868;
    border-radius: 14px;
    padding: 22px;
    margin-bottom: 22px;
    box-shadow: 0 5px 15px rgba(0,0,0,0.25);
}

.stat {
    background: #102a43;
    padding: 22px;
    border-radius: 12px;
    border: 1px solid #1b4868;
}

.stat-title {
    color: #a9bfd2;
    font-size: 14px;
}

.number {
    font-size: 32px;
    font-weight: bold;
    color: #20cfff;
    margin-top: 10px;
}

.danger {
    color: #ff4d6d;
}

.success {
    color: #39e58c;
}

.warning {
    color: #ffc857;
}

.info {
    color: #9bb0c5;
    line-height: 1.7;
}

.dashboard-grid {
    display: grid;
    grid-template-columns: 2fr 1fr;
    gap: 22px;
    margin-top: 25px;
}

.graph {
    display: flex;
    align-items: end;
    justify-content: space-around;
    height: 300px;
    border-left: 2px solid #587086;
    border-bottom: 2px solid #587086;
    padding: 20px;
}

.group {
    height: 100%;
    display: flex;
    align-items: end;
    gap: 8px;
}

.bar {
    width: 28px;
    border-radius: 5px 5px 0 0;
}

.normal-bar {
    background: #22c985;
}

.suspicious-bar {
    background: #ff4d6d;
}

.legend {
    text-align: center;
    margin-top: 20px;
    color: #b7c8d8;
}

.legend span {
    margin: 0 15px;
}

.risk-box {
    margin: 20px 0;
}

.risk-title {
    display: flex;
    justify-content: space-between;
    margin-bottom: 7px;
}

.progress {
    background: #203b52;
    height: 12px;
    border-radius: 10px;
    overflow: hidden;
}

.progress div {
    height: 100%;
    border-radius: 10px;
}

.low {
    width: 70%;
    background: #22c985;
}

.medium {
    width: 45%;
    background: #ffc857;
}

.high {
    width: 25%;
    background: #ff4d6d;
}

button,
.btn {
    background: #12aee8;
    color: white;
    border: none;
    padding: 11px 18px;
    margin-top: 12px;
    border-radius: 7px;
    cursor: pointer;
    text-decoration: none;
    display: inline-block;
    font-weight: bold;
}

button:hover,
.btn:hover {
    background: #078bc0;
}

table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 15px;
}

th,
td {
    padding: 13px;
    border-bottom: 1px solid #23425f;
    text-align: left;
}

th {
    color: #20cfff;
}

.badge {
    padding: 5px 9px;
    border-radius: 5px;
    background: #173a52;
}

.suspicious {
    color: #ffbd69;
}

.forensic {
    color: #61e6a8;
}

.normal {
    color: #9fb4c7;
}

.timeline {
    border-left: 3px solid #20cfff;
    padding-left: 25px;
}

.event {
    margin-bottom: 20px;
    padding: 15px;
    background: #102a43;
    border-radius: 8px;
}

.event.suspicious-event {
    border-left: 4px solid #ff4d6d;
}

.event.forensic-event {
    border-left: 4px solid #61e6a8;
}

input {
    background: #071525;
    color: white;
    padding: 12px;
    border: 1px solid #31536e;
    border-radius: 7px;
    width: 100%;
    margin-top: 10px;
}

.hash {
    word-break: break-all;
    background: #071525;
    padding: 12px;
    border-radius: 7px;
    margin-top: 8px;
    font-size: 13px;
}

.risk-score {
    font-size: 55px;
    font-weight: bold;
    color: #ff4d6d;
    margin: 15px 0;
}

.finding {
    padding: 12px;
    margin: 8px 0;
    background: #102a43;
    border-left: 4px solid #ffbd69;
    border-radius: 6px;
}

.preview {
    overflow-x: auto;
}


/* ============================================================
   BEFORE / AFTER GRAPH
   ============================================================ */

.comparison-graph {
    height: 330px;

    border-left: 2px solid #587086;
    border-bottom: 2px solid #587086;

    display: flex;
    align-items: end;
    justify-content: center;

    gap: 100px;

    padding: 20px;
}

.graph-column {
    height: 100%;

    display: flex;
    flex-direction: column;

    justify-content: end;
    align-items: center;
}

.graph-bar {
    width: 75px;
    min-height: 5px;

    border-radius: 8px 8px 0 0;

    transition: height 0.5s ease;
}

.before-bar {
    background: #20cfff;
}

.after-bar {
    background: #ffbd69;
}

.graph-value {
    margin-top: 10px;

    font-size: 18px;

    font-weight: bold;
}

.graph-label {
    margin-top: 5px;

    color: #9bb0c5;

    font-weight: bold;
}


/* ============================================================
   CHANGE STATUS
   ============================================================ */

.status-modified {
    background: #4b1825;
    border: 1px solid #ff4d6d;
    color: #ff7188;
    padding: 15px;
    border-radius: 8px;
    margin-bottom: 20px;
}

.status-safe {
    background: #123c2c;
    border: 1px solid #39e58c;
    color: #39e58c;
    padding: 15px;
    border-radius: 8px;
    margin-bottom: 20px;
}



.access-choice {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
    margin-top: 20px;
}

.access-choice .btn {
    text-align: center;
}

.login-card {
    max-width: 520px;
    margin: 60px auto;
}

.role-admin {
    color: #20cfff;
    font-weight: bold;
}

.pending {
    color: #ffc857;
    font-weight: bold;
}

.role-user {
    color: #39e58c;
    font-weight: bold;
}

.activity-user {
    background: #102a43;
    border-left: 4px solid #20cfff;
    padding: 15px;
    margin-bottom: 10px;
    border-radius: 7px;
}

footer {
    text-align: center;
    padding: 30px;
    color: #7894aa;
}

@media(max-width: 1000px) {

    .cards {
        grid-template-columns: repeat(2, 1fr);
    }

    .dashboard-grid {
        grid-template-columns: 1fr;
    }

    table {
        display: block;
        overflow-x: auto;
    }

    .comparison-graph {
        gap: 50px;
    }
}

</style>
"""


# ============================================================
# BASE HTML
# ============================================================

BASE = """
<!DOCTYPE html>

<html>

<head>

<title>Data Shield - Digital Forensics</title>

""" + STYLE + """

</head>

<body>

<div class="header">

<div class="logo">
DATA SHIELD
</div>

<div class="status">
● SYSTEM ACTIVE
</div>

</div>

<nav>

<a href="/">Dashboard</a>

{% if session.get("role") == "admin" %}
<a href="/admin">Admin Access</a>
<a href="/admin/users">Manage Users</a>
{% endif %}

{% if session.get("username") %}
<a href="/case">Case</a>
<a href="/evidence">Evidence</a>
<a href="/files">Deleted Files</a>
<a href="/pdf-analysis">PDF Analysis</a>
<a href="/csv-analysis">CSV Analysis</a>
<a href="/graph-analysis">Graph Analysis</a>
<a href="/timeline">Timeline</a>
<a href="/custody">Chain of Custody</a>
<a href="/report">Report</a>
<a href="/logout">Logout ({{ session.get("username") }})</a>
{% else %}
<a href="/login">Login</a>
{% endif %}

</nav>

<div class="container">

{{ content|safe }}

</div>

<footer>

Corporate Data Theft Detection —
Digital Forensic Investigation Prototype

<br><br>

Analyze Only Authorized Evidence.

</footer>

</body>

</html>
"""


def page(content):
    return render_template_string(BASE, content=content)


# ============================================================
# SHA-256
# ============================================================

def sha256_file(filepath):

    sha256 = hashlib.sha256()

    with open(filepath, "rb") as file:

        while True:

            chunk = file.read(4096)

            if not chunk:
                break

            sha256.update(chunk)

    return sha256.hexdigest()


# ============================================================
# LOGIN / LOGOUT
# ============================================================


@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():

    error = ""

    if request.method == "POST":

        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = USERS.get(email)

        if (
            user
            and user.get("role") == "admin"
            and user.get("status") == "approved"
            and user.get("password") == password
        ):

            session.clear()
            session["username"] = email
            session["role"] = "admin"

            log_activity(
                "Admin Login",
                "Successful administrator login"
            )

            return redirect(url_for("dashboard"))

        error = "Invalid administrator email or password."

    content = f"""
    <div class="card login-card">

        <h2>🔐 Admin Login</h2>

        <p class="info">
            Administrator access only.
            This area contains private user activity and
            access-control information.
        </p>

        <br>

        <p class="danger"><b>{error}</b></p>

        <form method="POST">

            <label><b>Admin Email ID</b></label>

            <input
                type="email"
                name="email"
                required
            >

            <br>

            <label><b>Admin Password</b></label>

            <input
                type="password"
                name="password"
                required
            >

            <button type="submit">
                Admin Login
            </button>

        </form>

        <br>

        <a class="btn" href="/login">
            ← User Login
        </a>

    </div>
    """

    return page(content)


@app.route("/login", methods=["GET", "POST"])
def login():

    error = ""

    if request.method == "POST":

        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = USERS.get(email)

        if (
            user
            and user.get("role") == "user"
            and user.get("status") == "approved"
            and user.get("password") == password
        ):

            session.clear()
            session["username"] = email
            session["role"] = "user"

            log_activity(
                "User Login",
                "Successful user login"
            )

            return redirect(url_for("dashboard"))

        if email in PENDING_USERS:
            error = (
                "Your account is waiting for administrator approval."
            )
        else:
            error = "Invalid user email or password."

    content = f"""
    <div class="card login-card">

        <h2>👤 User Login</h2>

        <p class="info">
            Only administrator-approved user accounts can
            access the forensic system.
        </p>

        <br>

        <p class="danger"><b>{error}</b></p>

        <form method="POST">

            <label><b>User Email ID</b></label>

            <input
                type="email"
                name="email"
                required
            >

            <br>

            <label><b>User Password</b></label>

            <input
                type="password"
                name="password"
                required
            >

            <button type="submit">
                User Login
            </button>

        </form>

        <br>

        <a class="btn" href="/register">
            Create User Account
        </a>

        <br><br>

        <a class="btn" href="/admin-login">
            🔐 Admin Login
        </a>

    </div>
    """

    return page(content)


@app.route("/register", methods=["GET", "POST"])
def register():

    message = ""
    error = ""

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not name or not email or not password:

            error = "All fields are required."

        elif email in USERS:

            error = "An account with this email already exists."

        elif email in PENDING_USERS:

            error = "This account is already waiting for approval."

        elif len(password) < 6:

            error = "Password must contain at least 6 characters."

        else:

            PENDING_USERS[email] = {
                "name": name,
                "email": email,
                "password": password,
                "role": "user",
                "status": "pending",
                "requested_at":
                    datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
            }

            message = (
                "Registration submitted successfully. "
                "An administrator must approve your account "
                "before you can log in."
            )

    content = f"""
    <div class="card login-card">

        <h2>Create User Account</h2>

        <p class="success"><b>{message}</b></p>
        <p class="danger"><b>{error}</b></p>

        <form method="POST">

            <label><b>Name</b></label>

            <input
                type="text"
                name="name"
                required
            >

            <br>

            <label><b>Email ID</b></label>

            <input
                type="email"
                name="email"
                required
            >

            <br>

            <label><b>Password</b></label>

            <input
                type="password"
                name="password"
                minlength="6"
                required
            >

            <button type="submit">
                Request Access
            </button>

        </form>

        <br>

        <a class="btn" href="/login">
            Back to Login
        </a>

    </div>
    """

    return page(content)


@app.route("/logout")
def logout():

    if session.get("username"):
        log_activity("Logout", "User logged out")

    session.clear()

    return redirect(url_for("login"))


# ============================================================
# ADMIN ACCESS
# ============================================================

@app.route("/admin/users")
def admin_users():

    guard = require_admin()
    if guard:
        return guard

    rows = ""

    for email, user in list(PENDING_USERS.items()):

        rows += f"""
        <tr>

            <td>{user["name"]}</td>
            <td>{email}</td>
            <td>{user["requested_at"]}</td>

            <td>

                <a class="btn"
                   href="/admin/approve/{email}">
                    ✓ Approve
                </a>

                <a class="btn"
                   href="/admin/reject/{email}">
                    ✕ Reject
                </a>

            </td>

        </tr>
        """

    if not rows:
        rows = """
        <tr>
            <td colspan="4">
                No pending access requests.
            </td>
        </tr>
        """

    content = f"""

    <h2>User Access Requests</h2>

    <div class="card">

        <h3>Pending User Registrations</h3>

        <p class="info">
            A user cannot access the forensic system until
            an administrator approves the account.
        </p>

        <table>

            <tr>
                <th>Name</th>
                <th>Email</th>
                <th>Requested At</th>
                <th>Action</th>
            </tr>

            {rows}

        </table>

    </div>

    <a class="btn" href="/admin">
        ← Back to Admin Access
    </a>

    """

    return page(content)


@app.route("/admin/approve/<path:email>")
def approve_user(email):

    guard = require_admin()
    if guard:
        return guard

    email = email.lower()

    user = PENDING_USERS.pop(email, None)

    if user:

        USERS[email] = {
            "password": user["password"],
            "role": "user",
            "name": user["name"],
            "status": "approved"
        }

        log_activity(
            "User Approved",
            f"Approved user account: {email}"
        )

    return redirect(url_for("admin_users"))


@app.route("/admin/reject/<path:email>")
def reject_user(email):

    guard = require_admin()
    if guard:
        return guard

    email = email.lower()

    user = PENDING_USERS.pop(email, None)

    if user:

        log_activity(
            "User Rejected",
            f"Rejected user account: {email}"
        )

    return redirect(url_for("admin_users"))


@app.route("/admin")
def admin_access():

    guard = require_admin()
    if guard:
        return guard

    rows = ""

    for item in reversed(ACTIVITY_LOG):

        rows += f"""
        <tr>
            <td>{item["time"]}</td>
            <td>{item["username"]}</td>
            <td>{item["role"]}</td>
            <td>{item["action"]}</td>
            <td>{item["details"]}</td>
        </tr>
        """

    content = f"""

    <h2>Admin Access</h2>

    <div class="card">

        <h3>Access Control</h3>

        <p class="info">
            New users must register first. Only approved users
            can log in and access investigation features.
        </p>

        <a class="btn" href="/admin/users">
            Manage Access Requests ({len(PENDING_USERS)})
        </a>

    </div>

    <p class="subtitle">
        Private administrator activity monitoring
    </p>

    <div class="cards">

        <div class="stat">
            <div class="stat-title">Total Activities</div>
            <div class="number">{len(ACTIVITY_LOG)}</div>
        </div>

        <div class="stat">
            <div class="stat-title">Registered Users</div>
            <div class="number">{len(USERS) - 1}</div>
        </div>

        <div class="stat">
            <div class="stat-title">Current Admin</div>
            <div class="number">1</div>
        </div>

    </div>

    <div class="card">

        <h2>All User Activity</h2>

        <p class="info">
            Only the administrator can see this page.
            Users cannot see another user's upload, analysis,
            recovery or other activity. Only the administrator
            can see the complete activity audit.
        </p>

        <table>

            <tr>
                <th>Time</th>
                <th>User</th>
                <th>Role</th>
                <th>Action</th>
                <th>Details</th>
            </tr>

            {rows}

        </table>

    </div>

    """

    return page(content)


# ============================================================
# DASHBOARD
# ============================================================

@app.route("/")
def dashboard():
    guard = require_login()
    if guard:
        return guard



    recoverable = len([
        f for f in FILES
        if f["status"] in [
            "Recoverable",
            "Partially Recoverable"
        ]
    ])

    recovered = len([
        f for f in FILES
        if os.path.exists(
            os.path.join(
                RECOVERED_FOLDER,
                f["name"]
            )
        )
    ])

    suspicious_events = len([
        e for e in TIMELINE
        if e[2] == "Suspicious"
    ])

    csv_risk = CSV_ANALYSIS["risk_score"]

    csv_risk_text = (
        f"{csv_risk}/100"
        if csv_risk
        else "Not Analyzed"
    )

    content = f"""

<h1>Corporate Data Theft Detection</h1>

<div class="subtitle">

Digital Forensic Investigation & Security Monitoring Dashboard

</div>


<div class="cards">

<div class="stat">
<div class="stat-title">Total Evidence</div>
<div class="number">{len(FILES)}</div>
</div>

<div class="stat">
<div class="stat-title">Deleted Files</div>
<div class="number">{len(FILES)}</div>
</div>

<div class="stat">
<div class="stat-title">Recoverable</div>
<div class="number">{recoverable}</div>
</div>

<div class="stat">
<div class="stat-title">Recovered</div>
<div class="number">{recovered}</div>
</div>

<div class="stat">
<div class="stat-title">High Risk Events</div>
<div class="number danger">{suspicious_events}</div>
</div>

</div>


<div class="dashboard-grid">

<div class="card">

<h2>Normal vs Suspicious Activity</h2>

<div class="graph">

<div class="group">
<div class="bar normal-bar" style="height:80%"></div>
<div class="bar suspicious-bar" style="height:35%"></div>
</div>

<div class="group">
<div class="bar normal-bar" style="height:55%"></div>
<div class="bar suspicious-bar" style="height:65%"></div>
</div>

<div class="group">
<div class="bar normal-bar" style="height:30%"></div>
<div class="bar suspicious-bar" style="height:75%"></div>
</div>

<div class="group">
<div class="bar normal-bar" style="height:45%"></div>
<div class="bar suspicious-bar" style="height:90%"></div>
</div>

<div class="group">
<div class="bar normal-bar" style="height:20%"></div>
<div class="bar suspicious-bar" style="height:95%"></div>
</div>

</div>

<div class="legend">

<span>🟢 Normal Activity</span>
<span>🔴 Suspicious Activity</span>

</div>

</div>


<div class="card">

<h2>Risk Analysis</h2>

<div class="risk-box">

<div class="risk-title">
<span>Low Risk</span>
<span>70%</span>
</div>

<div class="progress">
<div class="low"></div>
</div>

</div>

<div class="risk-box">

<div class="risk-title">
<span>Medium Risk</span>
<span>45%</span>
</div>

<div class="progress">
<div class="medium"></div>
</div>

</div>

<div class="risk-box">

<div class="risk-title">
<span>High Risk</span>
<span>25%</span>
</div>

<div class="progress">
<div class="high"></div>
</div>

</div>

<br>

<h3>CSV Dataset Risk</h3>

<p class="number">{csv_risk_text}</p>

<a class="btn" href="/csv-analysis">
Analyze CSV
</a>

</div>

</div>


<div class="card">

<h2>Case Overview</h2>

<p><b>Case ID:</b> {CASE["id"]}</p>
<p><b>Case:</b> {CASE["name"]}</p>
<p><b>Organization:</b> {CASE["organization"]}</p>
<p><b>Incident:</b> {CASE["incident"]}</p>
<p><b>Status:</b> {CASE["status"]}</p>

<p>
<b>Priority:</b>
<span class="danger">{CASE["priority"]}</span>
</p>

<br>

<a class="btn" href="/evidence">
Start Investigation
</a>

</div>

"""

    return page(content)


# ============================================================
# CASE
# ============================================================

@app.route("/case")
def case():
    guard = require_login()
    if guard:
        return guard



    content = f"""

<h2>Case Information</h2>

<div class="card">

<p><b>Case ID:</b> {CASE["id"]}</p>
<p><b>Case Name:</b> {CASE["name"]}</p>
<p><b>Organization:</b> {CASE["organization"]}</p>
<p><b>Incident:</b> {CASE["incident"]}</p>
<p><b>Status:</b> {CASE["status"]}</p>
<p><b>Priority:</b> {CASE["priority"]}</p>

<br>

<p class="info">

This case represents a synthetic corporate data theft
investigation used for educational digital-forensics
demonstration.

</p>

</div>

"""

    return page(content)


# ============================================================
# EVIDENCE UPLOAD
# ============================================================

@app.route("/evidence", methods=["GET", "POST"])
def evidence():
    guard = require_login()
    if guard:
        return guard



    result = ""

    if request.method == "POST":

        uploaded = request.files.get("evidence")

        if uploaded and uploaded.filename:

            safe_name = os.path.basename(
                uploaded.filename
            )

            filepath = os.path.join(
                UPLOAD_FOLDER,
                safe_name
            )

            uploaded.save(filepath)

            file_hash = sha256_file(filepath)

            log_activity("Evidence Upload", f"Uploaded {safe_name}")

            CUSTODY.append({
                "evidence": safe_name,
                "time": datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                "action": "Evidence Uploaded",
                "hash": file_hash,
                "integrity": "VERIFIED"
            })

            result = f"""

<div class="card">

<h2>✓ Evidence Successfully Added</h2>

<p><b>File:</b> {safe_name}</p>

<p>
<b>Size:</b>
{os.path.getsize(filepath)} bytes
</p>

<br>

<h3>SHA-256 Hash</h3>

<div class="hash">
{file_hash}
</div>

<br>

<p class="forensic">
<b>Integrity: VERIFIED</b>
</p>

</div>

"""

    content = f"""

<h2>Evidence Management</h2>

{result}

<div class="card">

<h3>Upload Authorized Evidence</h3>

<p class="info">

Upload an authorized evidence file.
The system calculates a SHA-256 hash
to establish an integrity value.

</p>

<form method="POST"
enctype="multipart/form-data">

<input
type="file"
name="evidence"
required
>

<button type="submit">
Calculate SHA-256 & Verify
</button>

</form>

</div>

"""

    return page(content)


# ============================================================
# DELETED FILES
# ============================================================

@app.route("/files")
def files():
    guard = require_login()
    if guard:
        return guard



    rows = ""

    for f in FILES:

        if f["status"] == "Recoverable":

            action = f"""

<a class="btn"
href="/recover/{f['id']}">

Recover

</a>

"""

        elif f["status"] == "Partially Recoverable":

            action = """
<span class="badge">
Partial Recovery
</span>
"""

        else:

            action = """
<span class="badge">
Not Recoverable
</span>
"""

        rows += f"""

<tr>

<td>{f["id"]}</td>
<td>{f["name"]}</td>
<td>{f["path"]}</td>
<td>{f["type"]}</td>
<td>{f["size"]}</td>
<td>{f["deleted"]}</td>
<td>{f["status"]}</td>
<td>{action}</td>

</tr>

"""

    content = f"""

<h2>Deleted File Analysis</h2>

<div class="card">

<table>

<tr>
<th>ID</th>
<th>File</th>
<th>Original Path</th>
<th>Type</th>
<th>Size</th>
<th>Deleted</th>
<th>Status</th>
<th>Action</th>
</tr>

{rows}

</table>

</div>

<div class="card">

<h3>Important Forensic Note</h3>

<p class="info">

The files displayed here are synthetic demonstration
evidence. Recovery demonstrates the workflow but does
not perform low-level disk carving or filesystem recovery.

</p>

</div>

"""

    return page(content)


# ============================================================
# RECOVERY
# ============================================================

@app.route("/recover/<file_id>")
def recover(file_id):
    guard = require_login()
    if guard:
        return guard



    selected = None

    for f in FILES:

        if f["id"] == file_id:
            selected = f
            break

    if not selected:
        return "File not found", 404

    if selected["status"] != "Recoverable":
        return "This file is not fully recoverable.", 400

    recovered_path = os.path.join(
        RECOVERED_FOLDER,
        selected["name"]
    )

    demo_content = f"""
DATA SHIELD - RECOVERED DEMO EVIDENCE

Case ID:
{CASE["id"]}

Evidence ID:
{selected["id"]}

File Name:
{selected["name"]}

Original Path:
{selected["path"]}

Original Size:
{selected["size"]}

Recovery Status:
RECOVERED

Recovery Time:
{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

This is synthetic educational evidence.
"""

    with open(
        recovered_path,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(demo_content)

    file_hash = sha256_file(recovered_path)

    recovery_time = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    CUSTODY.append({
        "evidence": selected["id"],
        "time": recovery_time,
        "action": "File Recovered",
        "hash": file_hash,
        "integrity": "VERIFIED"
    })

    content = f"""

<h2>File Recovery Result</h2>

<div class="card">

<h2>✓ Recovery Successful</h2>

<br>

<p><b>File ID:</b> {selected["id"]}</p>
<p><b>File Name:</b> {selected["name"]}</p>
<p><b>Original Path:</b> {selected["path"]}</p>
<p><b>Recovery Time:</b> {recovery_time}</p>

<br>

<h3>Recovered File SHA-256</h3>

<div class="hash">
{file_hash}
</div>

<br>

<p class="forensic">
<b>Integrity: VERIFIED</b>
</p>

</div>

<a class="btn" href="/files">
Back to Deleted Files
</a>

"""

    return page(content)


# ============================================================
# PDF ANALYSIS
# ============================================================

def analyze_pdf_file(filepath, search_term):

    result = {
        "filename": os.path.basename(filepath),
        "pages": 0,
        "term": search_term,
        "found": False,
        "pages_found": [],
        "metadata": {},
        "finding": ""
    }

    try:

        reader = PdfReader(filepath)

        result["pages"] = len(reader.pages)

        if reader.metadata:

            result["metadata"] = {

                "Author":
                    reader.metadata.get(
                        "/Author",
                        "Not available"
                    ),

                "Creator":
                    reader.metadata.get(
                        "/Creator",
                        "Not available"
                    ),

                "Title":
                    reader.metadata.get(
                        "/Title",
                        "Not available"
                    )
            }

        for page_number, page in enumerate(
            reader.pages,
            start=1
        ):

            text = page.extract_text() or ""

            if search_term.lower() in text.lower():

                result["found"] = True

                result["pages_found"].append(
                    page_number
                )

        if result["found"]:

            result["finding"] = (
                "Search term found in PDF."
            )

        else:

            result["finding"] = (
                "Search term not found."
            )

    except Exception as e:

        result["finding"] = str(e)

    return result


@app.route("/pdf-analysis", methods=["GET", "POST"])
def pdf_analysis():
    guard = require_login()
    if guard:
        return guard



    result_html = ""

    if request.method == "POST":

        uploaded = request.files.get("pdf_file")
        search_term = request.form.get(
            "search_term",
            ""
        )

        if uploaded and uploaded.filename:

            filename = os.path.basename(
                uploaded.filename
            )

            filepath = os.path.join(
                UPLOAD_FOLDER,
                filename
            )

            uploaded.save(filepath)

            result = analyze_pdf_file(
                filepath,
                search_term
            )

            log_activity(
                "PDF Analysis",
                f"Analyzed {filename}"
            )

            result_html = f"""

<div class="card">

<h2>PDF Analysis Result</h2>

<p>
<b>File:</b>
{result["filename"]}
</p>

<p>
<b>Total Pages:</b>
{result["pages"]}
</p>

<p>
<b>Search Term:</b>
{result["term"]}
</p>

<br>

<p class="{
    'success' if result['found']
    else 'danger'
}">

<b>{result["finding"]}</b>

</p>

<br>

<p>
<b>Pages Found:</b>
{result["pages_found"]}
</p>

<br>

<h3>PDF Metadata</h3>

"""

            for key, value in result[
                "metadata"
            ].items():

                result_html += f"""

<p>
<b>{key}:</b> {value}
</p>

"""

            result_html += "</div>"

    content = f"""

<h2>PDF Analysis</h2>

<div class="card">

<form method="POST"
enctype="multipart/form-data">

<label>
<b>Upload PDF</b>
</label>

<input
type="file"
name="pdf_file"
accept=".pdf"
required
>

<br>

<label>
<b>Search Term</b>
</label>

<input
type="text"
name="search_term"
placeholder="Enter keyword"
>

<button type="submit">
Analyze PDF
</button>

</form>

</div>

{result_html}

"""

    return page(content)


# ============================================================
# CSV ANALYSIS
# ============================================================

@app.route("/csv-analysis", methods=["GET", "POST"])
def csv_analysis():
    guard = require_login()
    if guard:
        return guard



    result_html = ""

    if request.method == "POST":

        uploaded = request.files.get(
            "csv_file"
        )

        if uploaded and uploaded.filename:

            filename = os.path.basename(
                uploaded.filename
            )

            filepath = os.path.join(
                UPLOAD_FOLDER,
                filename
            )

            uploaded.save(filepath)

            file_hash = sha256_file(
                filepath
            )

            with open(
                filepath,
                "r",
                encoding="utf-8-sig",
                newline=""
            ) as file:

                reader = csv.DictReader(file)

                rows = list(reader)

                headers = reader.fieldnames or []

            total_rows = len(rows)

            total_columns = len(headers)

            missing = 0

            for row in rows:

                for value in row.values():

                    if value is None or str(
                        value
                    ).strip() == "":

                        missing += 1

            duplicate_count = (
                total_rows - len(
                    {
                        tuple(row.items())
                        for row in rows
                    }
                )
            )

            suspicious = 0

            findings = []

            for row in rows:

                row_text = " ".join(
                    str(value)
                    for value in row.values()
                ).lower()

                keywords = [
                    "hack",
                    "fraud",
                    "stolen",
                    "deleted",
                    "suspicious",
                    "unauthorized"
                ]

                if any(
                    word in row_text
                    for word in keywords
                ):

                    suspicious += 1

            risk_score = 0

            if missing > 0:
                risk_score += 20

            if duplicate_count > 0:
                risk_score += 20

            if suspicious > 0:
                risk_score += 40

            risk_score = min(
                risk_score,
                100
            )

            if risk_score >= 70:
                risk_level = "HIGH"

            elif risk_score >= 40:
                risk_level = "MEDIUM"

            else:
                risk_level = "LOW"

            log_activity(
                "CSV Analysis",
                f"Analyzed {filename} | Risk={risk_score}/100"
            )

            CSV_ANALYSIS.update({

                "filename": filename,

                "hash": file_hash,

                "rows": total_rows,

                "columns": total_columns,

                "column_names": headers,

                "missing_values": missing,

                "duplicates": duplicate_count,

                "suspicious_records": suspicious,

                "risk_score": risk_score,

                "risk_level": risk_level,

                "headers": headers,

                "preview": rows[:10],

                "findings": findings

            })

            preview_html = ""

            if rows:

                preview_html += """

<table>

<tr>
"""

                for header in headers:

                    preview_html += f"""
<th>{header}</th>
"""

                preview_html += """
</tr>
"""

                for row in rows[:10]:

                    preview_html += "<tr>"

                    for header in headers:

                        preview_html += f"""
<td>
{row.get(header, "")}
</td>
"""

                    preview_html += "</tr>"

                preview_html += "</table>"

            result_html = f"""

<div class="card">

<h2>CSV Analysis Result</h2>

<p>
<b>File:</b> {filename}
</p>

<p>
<b>SHA-256:</b>
</p>

<div class="hash">
{file_hash}
</div>

<br>

<div class="cards">

<div class="stat">
<div class="stat-title">Rows</div>
<div class="number">{total_rows}</div>
</div>

<div class="stat">
<div class="stat-title">Columns</div>
<div class="number">{total_columns}</div>
</div>

<div class="stat">
<div class="stat-title">Missing</div>
<div class="number">{missing}</div>
</div>

<div class="stat">
<div class="stat-title">Duplicates</div>
<div class="number">{duplicate_count}</div>
</div>

<div class="stat">
<div class="stat-title">Risk</div>
<div class="number danger">
{risk_score}/100
</div>
</div>

</div>

<br>

<h3>
Risk Level:
<span class="danger">
{risk_level}
</span>
</h3>

</div>


<div class="card">

<h2>Dataset Preview</h2>

<div class="preview">

{preview_html}

</div>

</div>

"""

    content = f"""

<h2>CSV Analysis</h2>

<p class="subtitle">
Dataset structure, integrity and risk analysis
</p>

<div class="card">

<form method="POST"
enctype="multipart/form-data">

<input
type="file"
name="csv_file"
accept=".csv"
required
>

<button type="submit">
Analyze CSV
</button>

</form>

</div>

{result_html}

"""

    return page(content)


# ============================================================
# CSV BEFORE / AFTER COMPARISON
# ============================================================

def compare_csv_files(before_path, after_path):

    with open(
        before_path,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as f:

        before_rows = list(
            csv.DictReader(f)
        )

    with open(
        after_path,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as f:

        after_rows = list(
            csv.DictReader(f)
        )

    if not before_rows:

        return {
            "changes": [],
            "total_before": 0,
            "total_after": len(after_rows),
            "changed": 0,
            "deleted": 0,
            "added": len(after_rows),
            "unchanged": 0
        }

    if not after_rows:

        return {
            "changes": [],
            "total_before": len(before_rows),
            "total_after": 0,
            "changed": 0,
            "deleted": len(before_rows),
            "added": 0,
            "unchanged": 0
        }

    # First column is used as unique ID
    key_column = list(
        before_rows[0].keys()
    )[0]

    before_dict = {
        str(
            row.get(
                key_column,
                ""
            )
        ).strip(): row

        for row in before_rows
    }

    after_dict = {
        str(
            row.get(
                key_column,
                ""
            )
        ).strip(): row

        for row in after_rows
    }

    changes = []

    changed = 0
    deleted = 0
    added = 0
    unchanged = 0

    # --------------------------------------------------------
    # CHECK OLD RECORDS
    # --------------------------------------------------------

    for record_id, before_row in before_dict.items():

        if record_id not in after_dict:

            deleted += 1

            changes.append({

                "record": record_id,

                "type": "DELETED",

                "field": "-",

                "before": "Record Exists",

                "after": "Missing"

            })

            continue

        after_row = after_dict[record_id]

        record_changed = False

        all_columns = set(
            before_row.keys()
        ) | set(
            after_row.keys()
        )

        for column in all_columns:

            before_value = str(
                before_row.get(
                    column,
                    ""
                )
            )

            after_value = str(
                after_row.get(
                    column,
                    ""
                )
            )

            if before_value != after_value:

                record_changed = True

                changed += 1

                changes.append({

                    "record": record_id,

                    "type": "MODIFIED",

                    "field": column,

                    "before": before_value,

                    "after": after_value

                })

        if not record_changed:

            unchanged += 1

    # --------------------------------------------------------
    # CHECK NEW RECORDS
    # --------------------------------------------------------

    for record_id, after_row in after_dict.items():

        if record_id not in before_dict:

            added += 1

            changes.append({

                "record": record_id,

                "type": "ADDED",

                "field": "-",

                "before": "Not Present",

                "after": "New Record"

            })

    return {

        "changes": changes,

        "total_before": len(before_rows),

        "total_after": len(after_rows),

        "changed": changed,

        "deleted": deleted,

        "added": added,

        "unchanged": unchanged

    }


# ============================================================
# GRAPH ANALYSIS
# ============================================================

@app.route(
    "/graph-analysis",
    methods=["GET", "POST"]
)
def graph_analysis():
    guard = require_login()
    if guard:
        return guard



    message = ""

    if request.method == "POST":

        before_file = request.files.get(
            "before_file"
        )

        after_file = request.files.get(
            "after_file"
        )

        if not before_file or not after_file:

            message = """

<div class="status-modified">

<b>Error:</b>

Please upload both Before and After files.

</div>

"""

        elif not before_file.filename.lower().endswith(
            ".csv"
        ) or not after_file.filename.lower().endswith(
            ".csv"
        ):

            message = """

<div class="status-modified">

<b>Error:</b>

Only CSV files are supported.

</div>

"""

        else:

            before_name = (
                "BEFORE_" +
                os.path.basename(
                    before_file.filename
                )
            )

            after_name = (
                "AFTER_" +
                os.path.basename(
                    after_file.filename
                )
            )

            before_path = os.path.join(
                UPLOAD_FOLDER,
                before_name
            )

            after_path = os.path.join(
                UPLOAD_FOLDER,
                after_name
            )

            before_file.save(
                before_path
            )

            after_file.save(
                after_path
            )

            # SHA-256
            before_hash = sha256_file(
                before_path
            )

            after_hash = sha256_file(
                after_path
            )

            # Compare
            result = compare_csv_files(
                before_path,
                after_path
            )

            # Store results
            COMPARISON.update({

                "before_file":
                    before_name,

                "after_file":
                    after_name,

                "before_hash":
                    before_hash,

                "after_hash":
                    after_hash,

                "total_before":
                    result["total_before"],

                "total_after":
                    result["total_after"],

                "changed":
                    result["changed"],

                "deleted":
                    result["deleted"],

                "added":
                    result["added"],

                "unchanged":
                    result["unchanged"],

                "changes":
                    result["changes"]

            })

            log_activity(
                "Before/After Analysis",
                f"{before_name} vs {after_name} | "
                f"Modified={result["changed"]}, "
                f"Deleted={result["deleted"]}, "
                f"Added={result["added"]}"
            )

            if before_hash == after_hash:

                COMPARISON["status"] = (
                    "NO CHANGE"
                )

                message = """

<div class="status-safe">

<b>✓ VERIFIED</b><br>

SHA-256 hashes are identical.
No file-level modification detected.

</div>

"""

            else:

                COMPARISON["status"] = (
                    "MODIFICATION DETECTED"
                )

                message = """

<div class="status-modified">

<b>⚠ MODIFICATION DETECTED</b><br>

SHA-256 hashes are different.
The system identified differences
between the Before and After files.

</div>

"""

            # Chain of custody
            CUSTODY.append({

                "evidence": before_name,

                "time":
                    datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),

                "action":
                    "Before File Uploaded",

                "hash":
                    before_hash,

                "integrity":
                    "VERIFIED"

            })

            CUSTODY.append({

                "evidence": after_name,

                "time":
                    datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),

                "action":
                    "After File Uploaded",

                "hash":
                    after_hash,

                "integrity":
                    "VERIFIED"

            })

    before_count = COMPARISON[
        "total_before"
    ]

    after_count = COMPARISON[
        "total_after"
    ]

    changed = COMPARISON[
        "changed"
    ]

    deleted = COMPARISON[
        "deleted"
    ]

    added = COMPARISON[
        "added"
    ]

    unchanged = COMPARISON[
        "unchanged"
    ]

    max_value = max(
        before_count,
        after_count,
        1
    )

    before_height = int(
        (
            before_count /
            max_value
        ) * 240
    )

    after_height = int(
        (
            after_count /
            max_value
        ) * 240
    )

    content = f"""

<h2>Graph Analysis</h2>

<p class="subtitle">

Before vs After Evidence Comparison

</p>

{message}


<div class="card">

<h3>Upload Files for Comparison</h3>

<p class="info">

<b>Before:</b> Original / Reference file

<br>

<b>After:</b> Current / Suspected file

<br><br>

The system uses SHA-256 verification and
record-level comparison to detect
modified, deleted and added records.

</p>


<form method="POST"
enctype="multipart/form-data">

<label>

<b>BEFORE — Original File</b>

</label>

<input
type="file"
name="before_file"
accept=".csv"
required
>


<br><br>


<label>

<b>AFTER — Suspected File</b>

</label>

<input
type="file"
name="after_file"
accept=".csv"
required
>


<button type="submit">

🔍 Analyze Before vs After

</button>

</form>

</div>


<div class="cards">


<div class="stat">

<div class="stat-title">
Before Records
</div>

<div class="number">
{before_count}
</div>

</div>


<div class="stat">

<div class="stat-title">
After Records
</div>

<div class="number">
{after_count}
</div>

</div>


<div class="stat">

<div class="stat-title">
Modified Fields
</div>

<div class="number danger">
{changed}
</div>

</div>


<div class="stat">

<div class="stat-title">
Deleted
</div>

<div class="number danger">
{deleted}
</div>

</div>


<div class="stat">

<div class="stat-title">
Added
</div>

<div class="number success">
{added}
</div>

</div>

</div>


<div class="dashboard-grid">


<div class="card">

<h2>Before vs After Graph</h2>


<div class="comparison-graph">


<div class="graph-column">

<div
class="graph-bar before-bar"
style="height:{before_height}px">
</div>

<div class="graph-value">
{before_count}
</div>

<div class="graph-label">
BEFORE
</div>

</div>


<div class="graph-column">

<div
class="graph-bar after-bar"
style="height:{after_height}px">
</div>

<div class="graph-value">
{after_count}
</div>

<div class="graph-label">
AFTER
</div>

</div>


</div>


<div class="legend">

<span>
🔵 Original / Before
</span>

<span>
🟠 Current / After
</span>

</div>

</div>


<div class="card">

<h2>Change Summary</h2>


<div class="finding">

Modified Fields:

<b class="danger">
{changed}
</b>

</div>


<div class="finding">

Deleted Records:

<b class="danger">
{deleted}
</b>

</div>


<div class="finding">

Added Records:

<b class="success">
{added}
</b>

</div>


<div class="finding">

Unchanged Records:

<b class="success">
{unchanged}
</b>

</div>


</div>

</div>


<div class="card">

<h2>What Changed?</h2>

<div class="preview">

<table>

<tr>

<th>Record</th>

<th>Status</th>

<th>Field</th>

<th>Before</th>

<th>After</th>

</tr>

"""

    # --------------------------------------------------------
    # CHANGE TABLE
    # --------------------------------------------------------

    if COMPARISON["changes"]:

        for change in COMPARISON["changes"]:

            if change["type"] == "DELETED":

                status_class = "danger"

            elif change["type"] == "ADDED":

                status_class = "success"

            else:

                status_class = "warning"

            content += f"""

<tr>

<td>
{change["record"]}
</td>

<td class="{status_class}">

<b>
{change["type"]}
</b>

</td>

<td>
{change["field"]}
</td>

<td>
{change["before"]}
</td>

<td>
{change["after"]}
</td>

</tr>

"""

    else:

        content += """

<tr>

<td colspan="5">

No differences detected.

</td>

</tr>

"""

    content += """

</table>

</div>

</div>


<div class="card">

<h2>SHA-256 Verification</h2>

<p>
<b>Before File:</b>
</p>

<div class="hash">
""" + str(
        COMPARISON["before_hash"]
    ) + """
</div>

<br>

<p>
<b>After File:</b>
</p>

<div class="hash">
""" + str(
        COMPARISON["after_hash"]
    ) + """
</div>

</div>

"""

    return page(content)


# ============================================================
# TIMELINE
# ============================================================

@app.route("/timeline")
def timeline():
    guard = require_login()
    if guard:
        return guard



    events = ""

    for time, event, status in TIMELINE:

        if status == "Suspicious":

            event_class = (
                "event suspicious-event"
            )

            status_class = "suspicious"

        elif status == "Forensic":

            event_class = (
                "event forensic-event"
            )

            status_class = "forensic"

        else:

            event_class = "event"
            status_class = "normal"

        events += f"""

<div class="{event_class}">

<h3>{event}</h3>

<p>{time}</p>

<p class="{status_class}">
<b>{status}</b>
</p>

</div>

"""

    content = f"""

<h2>Forensic Timeline</h2>

<div class="card">

<div class="timeline">

{events}

</div>

</div>

"""

    return page(content)


# ============================================================
# CHAIN OF CUSTODY
# ============================================================

@app.route("/custody")
def custody():
    guard = require_login()
    if guard:
        return guard



    rows = ""

    for item in CUSTODY:

        rows += f"""

<tr>

<td>
{item["evidence"]}
</td>

<td>
{item["time"]}
</td>

<td>
{item["action"]}
</td>

<td>
<div class="hash">
{item["hash"]}
</div>
</td>

<td class="success">
{item["integrity"]}
</td>

</tr>

"""

    content = f"""

<h2>Chain of Custody</h2>

<div class="card">

<table>

<tr>

<th>Evidence</th>
<th>Time</th>
<th>Action</th>
<th>SHA-256</th>
<th>Integrity</th>

</tr>

{rows}

</table>

</div>

"""

    return page(content)


# ============================================================
# REPORT
# ============================================================

@app.route("/report")
def report():
    guard = require_login()
    if guard:
        return guard



    report_text = f"""
DATA SHIELD
DIGITAL FORENSIC INVESTIGATION REPORT
======================================

CASE INFORMATION

Case ID:
{CASE["id"]}

Case Name:
{CASE["name"]}

Organization:
{CASE["organization"]}

Incident:
{CASE["incident"]}

Priority:
{CASE["priority"]}


BEFORE / AFTER ANALYSIS

Before File:
{COMPARISON["before_file"]}

After File:
{COMPARISON["after_file"]}

Before SHA-256:
{COMPARISON["before_hash"]}

After SHA-256:
{COMPARISON["after_hash"]}

Analysis Status:
{COMPARISON["status"]}

Before Records:
{COMPARISON["total_before"]}

After Records:
{COMPARISON["total_after"]}

Modified Fields:
{COMPARISON["changed"]}

Deleted Records:
{COMPARISON["deleted"]}

Added Records:
{COMPARISON["added"]}

Unchanged Records:
{COMPARISON["unchanged"]}


CHANGE DETAILS
==============

"""

    for change in COMPARISON["changes"]:

        report_text += f"""
Record: {change["record"]}
Status: {change["type"]}
Field: {change["field"]}
Before: {change["before"]}
After: {change["after"]}
--------------------------------------
"""

    report_text += """

FORENSIC NOTE

SHA-256 verification confirms whether the
file contents differ. Record-level comparison
identifies the actual changes.

This report is generated for authorized
digital-forensics analysis.

"""

    report_path = os.path.join(
        REPORT_FOLDER,
        "DataShield_Forensic_Report.txt"
    )

    with open(
        report_path,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(report_text)

    content = """

<h2>Forensic Report</h2>

<div class="card">

<h3>Report Ready</h3>

<p class="info">

The report contains the case information,
SHA-256 verification, Before vs After
comparison and detected changes.

</p>

<a class="btn"
href="/download-report">

Download Report

</a>

</div>

"""

    return page(content)


# ============================================================
# DOWNLOAD REPORT
# ============================================================

@app.route("/download-report")
def download_report():

    report_path = os.path.join(
        REPORT_FOLDER,
        "DataShield_Forensic_Report.txt"
    )

    if not os.path.exists(report_path):

        return "Report not generated yet.", 404

    return send_file(
        report_path,
        as_attachment=True
    )


# ============================================================
# RUN APPLICATION
# ============================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )
