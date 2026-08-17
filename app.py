
from flask import Flask, render_template_string, request, redirect, url_for, send_file
import hashlib
import os
from datetime import datetime
from pypdf import PdfReader

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
RECOVERED_FOLDER = "recovered"
REPORT_FOLDER = "reports"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RECOVERED_FOLDER, exist_ok=True)
os.makedirs(REPORT_FOLDER, exist_ok=True)

CASE = {
    "id": "DF-2026-001",
    "name": "Operation DataShield",
    "organization": "TechNova Solutions",
    "incident": "Corporate Data Theft",
    "status": "Under Investigation",
    "priority": "HIGH"
}

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

CUSTODY = []

STYLE = """
<style>
* {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
    font-family: Arial, sans-serif;
}

body {
    background: #07111f;
    color: #e8f1ff;
}

nav {
    background: #0c1b2e;
    padding: 18px 35px;
    border-bottom: 1px solid #1c3958;
}

nav h1 {
    color: #36d9ff;
    display: inline;
}

nav a {
    color: #d9e9f7;
    text-decoration: none;
    margin-left: 25px;
    font-size: 14px;
}

.container {
    width: 92%;
    max-width: 1250px;
    margin: 30px auto;
}

.card {
    background: #0d1d31;
    border: 1px solid #1d3b59;
    border-radius: 12px;
    padding: 22px;
    margin-bottom: 22px;
}

.grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 18px;
}

.stat {
    background: #10263d;
    padding: 22px;
    border-radius: 12px;
    border: 1px solid #214664;
}

.stat h2 {
    color: #36d9ff;
    margin-top: 10px;
}

button, .btn {
    background: #087ea4;
    color: white;
    border: none;
    padding: 11px 18px;
    border-radius: 7px;
    cursor: pointer;
    text-decoration: none;
    display: inline-block;
    margin-top: 12px;
}

button:hover, .btn:hover {
    background: #0aa8d5;
}

table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 15px;
}

th, td {
    padding: 13px;
    border-bottom: 1px solid #23425f;
    text-align: left;
}

th {
    color: #36d9ff;
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
    border-left: 3px solid #36d9ff;
    padding-left: 25px;
}

.event {
    margin-bottom: 25px;
    padding: 15px;
    background: #10263d;
    border-radius: 8px;
}

input {
    background: #07111f;
    color: white;
    padding: 12px;
    border: 1px solid #31536e;
    border-radius: 7px;
    width: 100%;
    margin-top: 10px;
}

footer {
    text-align: center;
    padding: 30px;
    color: #7894aa;
}
</style>
"""

BASE = """
<!DOCTYPE html>
<html>
<head>
<title>ForensiX</title>
""" + STYLE + """
</head>
<body>

<nav>
    <h1>ForensiX</h1>
    <a href="/">Dashboard</a>
    <a href="/case">Case</a>
    <a href="/evidence">Evidence</a>
    <a href="/files">Deleted Files</a>
    <a href="/timeline">Timeline</a>
    <a href="/custody">Chain of Custody</a>
    <a href="/report">Report</a>
    <a href="/analyze-pdf">PDF Analysis</a>
</nav>

<div class="container">
{{ content|safe }}
</div>

<footer>
Educational Digital Forensics Simulation —
Analyze Only Authorized Evidence.
</footer>

</body>
</html>
"""


def page(content):
    return render_template_string(BASE, content=content)


def sha256_file(filepath):
    sha256 = hashlib.sha256()

    with open(filepath, "rb") as f:
        while chunk := f.read(4096):
            sha256.update(chunk)

    return sha256.hexdigest()


@app.route("/")
def dashboard():

    recoverable = len([
        f for f in FILES
        if f["status"] in ["Recoverable", "Partially Recoverable"]
    ])

    recovered = len([
        f for f in FILES
        if os.path.exists(
            os.path.join(RECOVERED_FOLDER, f["name"])
        )
    ])

    content = f"""
    <h2>Digital Forensics Investigation Dashboard</h2>
    <br>

    <div class="card">
        <h2>Operation DataShield</h2>
        <p>Corporate Data Theft Investigation</p>
        <br>
        <b>Case ID:</b> {CASE["id"]}<br>
        <b>Organization:</b> {CASE["organization"]}<br>
        <b>Status:</b> {CASE["status"]}<br>
        <b>Priority:</b> {CASE["priority"]}
    </div>

    <div class="grid">

        <div class="stat">
            <p>Total Evidence</p>
            <h2>5</h2>
        </div>

        <div class="stat">
            <p>Deleted Files</p>
            <h2>{len(FILES)}</h2>
        </div>

        <div class="stat">
            <p>Recoverable</p>
            <h2>{recoverable}</h2>
        </div>

        <div class="stat">
            <p>Recovered</p>
            <h2>{recovered}</h2>
        </div>

        <div class="stat">
            <p>Suspicious Events</p>
            <h2>6</h2>
        </div>

    </div>

    <div class="card">
        <h2>Forensic Workflow</h2>
        <br>
        Evidence Input →
        Hash Verification →
        Artifact Analysis →
        Deleted File Detection →
        Recovery →
        Timeline →
        Report
        <br><br>

        <a class="btn" href="/evidence">Start Investigation</a>
    </div>
    """

    return page(content)


@app.route("/case")
def case():

    content = f"""
    <h2>Case Information</h2>

    <div class="card">
        <p><b>Case ID:</b> {CASE["id"]}</p>
        <p><b>Case Name:</b> {CASE["name"]}</p>
        <p><b>Organization:</b> {CASE["organization"]}</p>
        <p><b>Incident:</b> {CASE["incident"]}</p>
        <p><b>Status:</b> {CASE["status"]}</p>
        <p><b>Priority:</b> {CASE["priority"]}</p>
    </div>
    """

    return page(content)


@app.route("/evidence", methods=["GET", "POST"])
def evidence():

    result = ""

    if request.method == "POST":

        uploaded = request.files.get("evidence")

        if uploaded and uploaded.filename:

            safe_name = os.path.basename(uploaded.filename)
            path = os.path.join(
                UPLOAD_FOLDER,
                safe_name
            )

            uploaded.save(path)

            file_hash = sha256_file(path)

            result = f"""
            <div class="card">
                <h3>✓ Evidence Successfully Added</h3>
                <br>
                <p><b>File:</b> {safe_name}</p>
                <p><b>SHA-256:</b></p>
                <p>{file_hash}</p>
                <p><b>Integrity:</b> VERIFIED</p>
            </div>
            """

    content = f"""
    <h2>Evidence Management</h2>

    {result}

    <div class="card">

        <h3>Upload Authorized Evidence</h3>

        <form method="POST"
              enctype="multipart/form-data">

            <input type="file" name="evidence" required>

            <button type="submit">
                Calculate SHA-256 & Verify
            </button>

        </form>

    </div>

    <div class="card">

        <h3>Demo Evidence</h3>

        <p>
        Use the synthetic case data to demonstrate
        forensic analysis and file recovery.
        </p>

        <br>

        <a class="btn" href="/files">
            Analyze Demo Evidence
        </a>

    </div>
    """

    return page(content)


@app.route("/files")
def files():

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
    """

    return page(content)


@app.route("/recover/<file_id>")
def recover(file_id):

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
FORENSIX RECOVERED DEMO FILE

Case ID: {CASE["id"]}
Evidence ID: {selected["id"]}

File Name:
{selected["name"]}

Original Path:
{selected["path"]}

Recovery Status:
RECOVERED

This is synthetic educational evidence.
"""

    with open(recovered_path, "w", encoding="utf-8") as f:
        f.write(demo_content)

    file_hash = sha256_file(recovered_path)

    CUSTODY.append({
        "evidence": selected["id"],
        "time": datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        ),
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

        <p><b>File Name:</b>
        {selected["name"]}</p>

        <p><b>Original Path:</b>
        {selected["path"]}</p>

        <p><b>Recovery Time:</b>
        {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>

        <p><b>SHA-256:</b>
        {file_hash}</p>

        <p><b>Integrity:</b>
        VERIFIED</p>

    </div>

    <a class="btn"
       href="/files">
       Back to Files
    </a>
    """

    return page(content)


@app.route("/timeline")
def timeline():

    events = ""

    for time, event, category in TIMELINE:

        css = category.lower()

        events += f"""
        <div class="event">

            <h3>{time}</h3>

            <p class="{css}">
            {event}
            </p>

            <small>
            Category: {category}
            </small>

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


@app.route("/custody")
def custody():

    rows = ""

    for item in CUSTODY:

        rows += f"""
        <tr>
            <td>{item["evidence"]}</td>
            <td>{item["time"]}</td>
            <td>{item["action"]}</td>
            <td>{item["hash"]}</td>
            <td>{item["integrity"]}</td>
        </tr>
        """

    content = f"""
    <h2>Chain of Custody</h2>

    <div class="card">

    <table>

    <tr>
        <th>Evidence ID</th>
        <th>Date/Time</th>
        <th>Action</th>
        <th>SHA-256</th>
        <th>Integrity</th>
    </tr>

    {rows}

    </table>

    </div>
    """

    return page(content)


@app.route("/report")
def report():

    recovered = [
        f for f in FILES
        if os.path.exists(
            os.path.join(
                RECOVERED_FOLDER,
                f["name"]
            )
        )
    ]

    recovered_text = ""

    for f in recovered:
        recovered_text += f"""
        <li>{f["name"]} — {f["status"]}</li>
        """

    content = f"""
    <h2>Digital Forensic Report</h2>

    <div class="card">

        <h3>Case Information</h3>

        <p>Case ID: {CASE["id"]}</p>
        <p>Case: {CASE["name"]}</p>
        <p>Organization: {CASE["organization"]}</p>
        <p>Incident: {CASE["incident"]}</p>

        <br>

        <h3>Forensic Observations</h3>

        <ul>
            <li>Confidential files were accessed.</li>
            <li>A removable storage event was recorded.</li>
            <li>An archive file was created.</li>
            <li>Several files were marked deleted.</li>
            <li>Recoverable demo evidence was identified.</li>
        </ul>

        <br>

        <h3>Recovered Evidence</h3>

        <ul>
            {recovered_text}
        </ul>

        <br>

        <h3>Investigation Limitation</h3>

        <p>
        This is a synthetic educational forensic simulation.
        It does not establish criminal responsibility.
        </p>

        <br>

        <a class="btn"
           href="/generate-report">
           Generate TXT Report
        </a>

    </div>
    """

    return page(content)


@app.route("/generate-report")
def generate_report():

    filename = "ForensiX_Report.txt"

    path = os.path.join(
        REPORT_FOLDER,
        filename
    )

    report = f"""
FORENSIX DIGITAL FORENSIC REPORT
================================

CASE ID:
{CASE["id"]}

CASE:
{CASE["name"]}

ORGANIZATION:
{CASE["organization"]}

INCIDENT:
{CASE["incident"]}

FORENSIC OBSERVATIONS
---------------------

1. Confidential files were accessed.
2. USB activity was recorded.
3. An archive file was created.
4. Several files were marked as deleted.
5. Recoverable synthetic evidence was identified.

RECOVERY
--------

"""

    for f in FILES:

        if os.path.exists(
            os.path.join(
                RECOVERED_FOLDER,
                f["name"]
            )
        ):

            report += f"""
{f["id"]} - {f["name"]}
Status: Recovered
"""

    report += """

LIMITATIONS
-----------

This is an educational digital-forensics simulation.
All evidence is synthetic.
Findings must not be treated as proof of criminal responsibility.

================================
Generated by ForensiX
"""

    with open(path, "w", encoding="utf-8") as f:
        f.write(report)

    return send_file(
        path,
        as_attachment=True,
        download_name=filename
    )


def analyze_pdf_file(filepath, search_term):
    """Analyze an authorized PDF and search its currently extractable text.

    Not finding a term does not prove deletion; it only means the term was
    not found in the text that the PDF parser could extract.
    """
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
                "Author": reader.metadata.get("/Author", "Not available"),
                "Creator": reader.metadata.get("/Creator", "Not available"),
                "Producer": reader.metadata.get("/Producer", "Not available"),
                "CreationDate": reader.metadata.get(
                    "/CreationDate", "Not available"
                ),
                "ModificationDate": reader.metadata.get(
                    "/ModDate", "Not available"
                )
            }

        for page_number, page in enumerate(reader.pages, start=1):
            page_text = page.extract_text() or ""

            if search_term.casefold() in page_text.casefold():
                result["found"] = True
                result["pages_found"].append(page_number)

        if result["found"]:
            result["finding"] = (
                f'Target "{search_term}" was found on page(s): '
                f'{", ".join(map(str, result["pages_found"]))}.'
            )
        else:
            result["finding"] = (
                f'Target "{search_term}" was not found in the currently '
                f'extractable PDF text. This does NOT prove that the '
                f'content was deleted.'
            )

    except Exception as error:
        result["finding"] = f"PDF analysis failed: {error}"

    return result


@app.route("/analyze-pdf", methods=["GET", "POST"])
def analyze_pdf():
    result_html = ""

    if request.method == "POST":
        uploaded = request.files.get("pdf_file")
        search_term = request.form.get("search_term", "").strip()

        if not uploaded or not uploaded.filename:
            result_html = """
            <div class="card">
                <h3>❌ Please select a PDF file.</h3>
            </div>
            """

        elif not uploaded.filename.lower().endswith(".pdf"):
            result_html = """
            <div class="card">
                <h3>❌ Only PDF files are supported.</h3>
            </div>
            """

        elif not search_term:
            result_html = """
            <div class="card">
                <h3>❌ Enter the content you want to find.</h3>
            </div>
            """

        else:
            safe_name = os.path.basename(uploaded.filename)
            filepath = os.path.join(UPLOAD_FOLDER, safe_name)
            uploaded.save(filepath)

            file_hash = sha256_file(filepath)
            result = analyze_pdf_file(filepath, search_term)

            if result["found"]:
                status = "FOUND"
                status_class = "forensic"
                pages = ", ".join(map(str, result["pages_found"]))
            else:
                status = "NOT FOUND"
                status_class = "suspicious"
                pages = "None"

            metadata = result["metadata"]

            result_html = f"""
            <div class="card">
                <h2>PDF Forensic Analysis Result</h2>
                <br>

                <p><b>File:</b> {result["filename"]}</p>
                <p><b>Pages:</b> {result["pages"]}</p>

                <br>

                <h3>SHA-256 Integrity</h3>
                <p style="word-break:break-all;">{file_hash}</p>
                <p class="forensic"><b>Integrity: VERIFIED</b></p>

                <br>

                <h3>Target Search</h3>
                <p><b>Target:</b> {result["term"]}</p>
                <p class="{status_class}">
                    <b>Status: {status}</b>
                </p>
                <p><b>Pages Found:</b> {pages}</p>

                <br>

                <h3>PDF Metadata</h3>
                <p><b>Author:</b> {metadata.get("Author", "Not available")}</p>
                <p><b>Creator:</b> {metadata.get("Creator", "Not available")}</p>
                <p><b>Producer:</b> {metadata.get("Producer", "Not available")}</p>
                <p><b>Creation Date:</b>
                    {metadata.get("CreationDate", "Not available")}
                </p>
                <p><b>Modification Date:</b>
                    {metadata.get("ModificationDate", "Not available")}
                </p>

                <br>

                <h3>Forensic Finding</h3>
                <p>{result["finding"]}</p>
            </div>
            """

    content = f"""
    <h2>PDF Forensic Analysis</h2>

    <div class="card">
        <h3>Upload PDF & Search for Evidence</h3>

        <p>
            Upload an authorized PDF and enter a particular term,
            project name, document ID, or other text to check whether
            it is present in the currently extractable PDF content.
        </p>

        <br>

        <form method="POST" enctype="multipart/form-data">

            <label><b>Select PDF Evidence</b></label>

            <input
                type="file"
                name="pdf_file"
                accept=".pdf,application/pdf"
                required
            >

            <br><br>

            <label><b>What do you want to find?</b></label>

            <input
                type="text"
                name="search_term"
                placeholder="Example: Project Alpha"
                required
            >

            <button type="submit">
                Analyze PDF
            </button>

        </form>
    </div>

    {result_html}

    <div class="card">
        <h3>⚠ Forensic Limitation</h3>
        <p>
            If a term is not found, this tool cannot conclude that the
            term was deleted. It only means the term was not found in
            the text currently extractable from the PDF.
        </p>
    </div>
    """

    return page(content)


if __name__ == "__main__":
    app.run(
        debug=True,
        host="127.0.0.1",
        port=5000
    )
