import base64
import datetime
import os
import smtplib
import sqlite3
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from flask import (
    Flask,
    Response,
    flash,
    jsonify,
    redirect,
    render_template_string,
    request,
    url_for,
)

app = Flask(__name__)
app.secret_key = "anudip_mca_secret_key"
DB_NAME = "anudip_attendance.db"
UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# --- EMAIL CONFIGURATION ---
SENDER_EMAIL = "rmjsecurities00@gmail.com"
SENDER_PASSWORD = (
    "bwmu swhu fimp mcnv"  # ⚠️ PASTE YOUR 16-CHAR GOOGLE APP PASSWORD HERE
)


# --- DATABASE INITIALIZATION ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL
        )
    """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            date TEXT NOT NULL,
            status TEXT NOT NULL,
            teacher_name TEXT DEFAULT 'Yellow Team Evaluator',
            UNIQUE(student_id, date)
        )
    """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS session_meta (
            date TEXT PRIMARY KEY,
            teacher_name TEXT,
            latitude TEXT,
            longitude TEXT,
            photo_path TEXT
        )
    """
    )
    conn.commit()
    conn.close()


init_db()


# --- HELPER: BUILD HIGH-RES REPORT HTML ---
def build_report_html(date, teacher_name):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT s.student_id, s.name, COALESCE(a.status, 'Present')
        FROM students s
        LEFT JOIN attendance a ON s.student_id = a.student_id AND a.date = ?
        ORDER BY s.student_id ASC
    """,
        (date,),
    )
    records = cursor.fetchall()

    cursor.execute(
        "SELECT latitude, longitude, photo_path FROM session_meta WHERE date = ?",
        (date,),
    )
    session_meta = cursor.fetchone()
    conn.close()

    total_students = len(records)
    present_count = sum(1 for r in records if r[2] == "Present")
    absent_count = sum(1 for r in records if r[2] == "Absent")
    pct = (
        round((present_count / total_students) * 100, 1)
        if total_students > 0
        else 0
    )

    gps_str = (
        f"Lat: {session_meta[0]}, Long: {session_meta[1]}"
        if session_meta and session_meta[0]
        else "N/A"
    )

    # Convert photo to Base64 JPEG for large inline display
    photo_html = ""
    if session_meta and session_meta[2] and os.path.exists(session_meta[2]):
        try:
            with open(session_meta[2], "rb") as img_file:
                b64_img = base64.b64encode(img_file.read()).decode("utf-8")
                photo_html = f"""
                <div style="margin: 20px 0; text-align: center; background-color: #f8f9fa; padding: 15px; border-radius: 8px; border: 1px solid #dee2e6;">
                    <p style="font-weight: bold; font-size: 15px; color: #002B49; margin-top: 0; margin-bottom: 10px;">
                        📷 VERIFIED GROUP SESSION PHOTO (JPG FORMAT)
                    </p>
                    <img src="data:image/jpeg;base64,{b64_img}" alt="Class Group Photo" style="width: 100%; max-width: 650px; height: auto; border-radius: 8px; border: 2px solid #002B49; box-shadow: 0 4px 12px rgba(0,0,0,0.15);" />
                </div>
                """
        except Exception:
            photo_html = ""

    rows_html = ""
    for idx, (s_id, name, status) in enumerate(records, 1):
        color = "#28a745" if status == "Present" else "#dc3545"
        rows_html += f"""
        <tr style="background-color: {'#f8f9fa' if idx % 2 == 0 else '#ffffff'};">
            <td style="padding: 10px; border: 1px solid #dee2e6; text-align: center;">{idx}</td>
            <td style="padding: 10px; border: 1px solid #dee2e6; text-align: center;"><b>{s_id}</b></td>
            <td style="padding: 10px; border: 1px solid #dee2e6;">{name}</td>
            <td style="padding: 10px; border: 1px solid #dee2e6; text-align: center;">09:00 AM - 03:00 PM (6 hrs)</td>
            <td style="padding: 10px; border: 1px solid #dee2e6; text-align: center; color: white; background-color: {color}; font-weight: bold; border-radius: 4px;">{status}</td>
        </tr>
        """

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Anudip MCA Attendance Report - {date}</title>
    </head>
    <body style="font-family: 'Segoe UI', Arial, sans-serif; background-color: #f4f6f9; padding: 20px; margin: 0;">
        <div style="max-width: 720px; margin: auto; background: #ffffff; padding: 25px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.08);">

            <!-- Header Banner -->
            <div style="background: linear-gradient(135deg, #002B49 0%, #004B87 100%); color: white; padding: 22px; text-align: center; border-radius: 8px;">
                <h2 style="margin:0; text-transform: uppercase; letter-spacing: 1px; font-size: 22px;">Anudip Foundation</h2>
                <p style="margin:6px 0 0 0; font-size:14px; opacity:0.9;">MCA Branch — Smart Attendance Summary</p>
            </div>

            <div style="margin-top: 20px; font-size: 14px; color: #333;">
                <p style="margin: 4px 0;"><b>Date:</b> {date} | <b>Evaluator:</b> {teacher_name}</p>
                <p style="margin: 4px 0;"><b>Shift Window:</b> 09:00 AM - 03:00 PM (6 Hours)</p>
                <p style="margin: 4px 0;"><b>Live Location GPS:</b> {gps_str}</p>
            </div>

            <!-- Large JPG Group Photo -->
            {photo_html}

            <!-- Summary KPI Cards -->
            <table width="100%" style="margin-bottom: 20px; border-collapse: separate; border-spacing: 6px;">
                <tr>
                    <td style="background: #e9ecef; padding: 12px; text-align: center; border-radius: 6px;"><b>Total Roster:</b> {total_students}</td>
                    <td style="background: #d4edda; color: #155724; padding: 12px; text-align: center; border-radius: 6px;"><b>Present:</b> {present_count}</td>
                    <td style="background: #f8d7da; color: #721c24; padding: 12px; text-align: center; border-radius: 6px;"><b>Absent:</b> {absent_count}</td>
                    <td style="background: #cce5ff; color: #004085; padding: 12px; text-align: center; border-radius: 6px;"><b>Rate:</b> {pct}%</td>
                </tr>
            </table>

            <!-- Roster Table -->
            <table width="100%" style="border-collapse: collapse; font-size: 13px;">
                <thead>
                    <tr style="background-color: #002B49; color: white;">
                        <th style="padding: 10px; border: 1px solid #dee2e6;">#</th>
                        <th style="padding: 10px; border: 1px solid #dee2e6;">Roll ID</th>
                        <th style="padding: 10px; border: 1px solid #dee2e6;">Student Name</th>
                        <th style="padding: 10px; border: 1px solid #dee2e6;">Shift Window</th>
                        <th style="padding: 10px; border: 1px solid #dee2e6;">Status</th>
                    </tr>
                </thead>
                <tbody>
                    {rows_html}
                </tbody>
            </table>

            <hr style="margin-top: 30px; border: none; border-top: 1px solid #eeeeee;">
            <p style="font-size: 12px; color: #888888; text-align: center; margin: 0;">
                Verified & Evaluated by <b>{teacher_name}</b> • Anudip Foundation MCA Yellow Team
            </p>
        </div>
    </body>
    </html>
    """
    return html_content


# --- WEB DASHBOARD TEMPLATE ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Anudip Foundation | Smart MCA Attendance Portal</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        :root { --primary-navy: #002B49; --bg-light: #F4F7FA; }
        body { background-color: var(--bg-light); font-family: 'Segoe UI', sans-serif; }
        .navbar-custom { background: linear-gradient(135deg, #002B49 0%, #004B87 100%); box-shadow: 0 4px 15px rgba(0,0,0,0.15); }
        .stat-card { border: none; border-radius: 14px; }
        .card-main { border: none; border-radius: 16px; box-shadow: 0 6px 20px rgba(0,0,0,0.04); }
        .status-badge { cursor: pointer; font-size: 0.9rem; padding: 8px 16px; border-radius: 20px; transition: all 0.2s; }
        .status-present { background-color: #d1e7dd; color: #0f5132; border: 1px solid #badbcc; }
        .status-absent { background-color: #f8d7da; color: #842029; border: 1px solid #f5c2c7; }
        #webcam, #captured-canvas { width: 100%; max-height: 280px; object-fit: cover; border-radius: 10px; border: 2px solid #0056b3; }
    </style>
</head>
<body>

    <nav class="navbar navbar-dark navbar-custom py-3 mb-4 sticky-top">
        <div class="container-fluid px-4">
            <a class="navbar-brand d-flex align-items-center" href="#">
                <i class="fa-solid fa-graduation-cap fa-2x me-3 text-warning"></i>
                <div>
                    <h4 class="m-0 fw-bold text-uppercase">Anudip Foundation</h4>
                    <small class="text-light opacity-75">MCA Branch — Digital Attendance Portal</small>
                </div>
            </a>
            <span class="badge bg-warning text-dark px-3 py-2 fs-6 rounded-pill">
                <i class="fa-solid fa-user-shield me-1"></i> Yellow Team
            </span>
        </div>
    </nav>

    <div class="container-fluid px-4 mb-5">

        {% with messages = get_flashed_messages(with_categories=true) %}
          {% if messages %}
            {% for category, message in messages %}
              <div class="alert alert-{{ category }} alert-dismissible fade show rounded-3 shadow-sm mb-4" role="alert">
                <i class="fa-solid fa-circle-info me-2"></i> {{ message }}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
              </div>
            {% endfor %}
          {% endif %}
        {% endwith %}

        <div class="card card-main mb-4 p-3">
            <div class="row g-3 align-items-center">
                <div class="col-lg-3 col-md-6">
                    <form method="GET" action="/" class="d-flex align-items-center gap-2">
                        <label for="date" class="fw-bold text-nowrap"><i class="fa-solid fa-calendar-day text-primary me-1"></i> Date:</label>
                        <input type="date" id="date" name="date" class="form-control" value="{{ selected_date }}" onchange="this.form.submit()">
                    </form>
                </div>

                <div class="col-lg-9 col-md-12 text-lg-end d-flex justify-content-lg-end gap-2 flex-wrap">
                    <button class="btn btn-outline-primary fw-bold" data-bs-toggle="modal" data-bs-target="#addStudentModal">
                        <i class="fa-solid fa-user-plus me-1"></i> Add Student
                    </button>
                    <button class="btn btn-primary fw-bold" data-bs-toggle="modal" data-bs-target="#cameraModal">
                        <i class="fa-solid fa-camera me-1"></i> Group Photo & GPS
                    </button>
                    <a href="/download_report?date={{ selected_date }}&teacher={{ current_teacher }}" class="btn btn-success fw-bold">
                        <i class="fa-solid fa-download me-1"></i> Download Report (Self)
                    </a>
                    <button class="btn btn-warning fw-bold text-dark" data-bs-toggle="modal" data-bs-target="#sendEmailModal">
                        <i class="fa-solid fa-paper-plane me-1"></i> Send Email Report
                    </button>
                </div>
            </div>
        </div>

        {% if session_meta and session_meta[3] %}
        <div class="alert alert-success d-flex align-items-center justify-content-between rounded-3 shadow-sm mb-4">
            <div>
                <i class="fa-solid fa-shield-halved fa-2x me-3 text-success"></i>
                <span><b>Verified Session:</b> Large Group Photo Saved • GPS: <b>Lat {{ session_meta[1] }}, Long {{ session_meta[2] }}</b></span>
            </div>
            <img src="/{{ session_meta[3] }}" alt="Group Photo" style="height: 60px; width: 100px; object-fit: cover; border-radius: 6px; border: 2px solid #28a745;">
        </div>
        {% endif %}

        <div class="row g-3 mb-4">
            <div class="col-md-3">
                <div class="card stat-card bg-white p-3 border-start border-4 border-primary shadow-sm">
                    <p class="text-muted small fw-bold text-uppercase mb-1">Total Roster</p>
                    <h3 class="fw-bold mb-0 text-dark">{{ total_students }}</h3>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card stat-card bg-white p-3 border-start border-4 border-success shadow-sm">
                    <p class="text-muted small fw-bold text-uppercase mb-1">Present Students</p>
                    <h3 class="fw-bold mb-0 text-success">{{ present_count }}</h3>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card stat-card bg-white p-3 border-start border-4 border-danger shadow-sm">
                    <p class="text-muted small fw-bold text-uppercase mb-1">Absent Students</p>
                    <h3 class="fw-bold mb-0 text-danger">{{ absent_count }}</h3>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card stat-card bg-white p-3 border-start border-4 border-info shadow-sm">
                    <p class="text-muted small fw-bold text-uppercase mb-1">Attendance Rate</p>
                    <h3 class="fw-bold mb-0 text-info">{{ attendance_rate }}%</h3>
                </div>
            </div>
        </div>

        <div class="card card-main p-4">
            <div class="table-responsive">
                <table class="table table-hover align-middle">
                    <thead class="table-light">
                        <tr>
                            <th>#</th>
                            <th>Roll ID</th>
                            <th>Student Name</th>
                            <th class="text-center">Shift Window</th>
                            <th class="text-center" style="width: 200px;">Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for student in students %}
                        <tr>
                            <td class="fw-bold text-secondary">{{ loop.index }}</td>
                            <td><span class="badge bg-light text-dark border font-monospace px-2 py-1">{{ student.student_id }}</span></td>
                            <td class="fw-semibold text-dark">{{ student.name }}</td>
                            <td class="text-center text-muted small">09:00 AM - 03:00 PM (6 hrs)</td>
                            <td class="text-center">
                                <button onclick="toggleStatus('{{ student.student_id }}', '{{ selected_date }}')" 
                                        class="btn w-100 status-badge {% if student.status == 'Present' %}status-present{% else %}status-absent{% endif %}">
                                    <i class="fa-solid {% if student.status == 'Present' %}fa-circle-check text-success{% else %}fa-circle-xmark text-danger{% endif %} me-1"></i>
                                    <span>{{ student.status }}</span>
                                </button>
                            </td>
                        </tr>
                        {% else %}
                        <tr>
                            <td colspan="5" class="text-center py-5 text-muted">No students added yet. Click <b>"Add Student"</b>.</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <!-- Modal 1: Camera & Location -->
    <div class="modal fade" id="cameraModal" tabindex="-1" aria-hidden="true">
        <div class="modal-dialog modal-dialog-centered modal-lg">
            <div class="modal-content border-0 shadow">
                <div class="modal-header text-white" style="background-color: var(--primary-navy);">
                    <h5 class="modal-title fw-bold text-white"><i class="fa-solid fa-camera me-2"></i> Live Verification</h5>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body p-4 text-center">
                    <button class="btn btn-outline-danger fw-bold mb-3" onclick="getLiveLocation()">
                        <i class="fa-solid fa-crosshairs me-1"></i> 1. Detect Live GPS Location
                    </button>
                    <div id="location-status" class="mb-3 fw-bold"></div>

                    <div id="camera-container" style="display: none;">
                        <video id="webcam" autoplay playsinline></video>
                        <canvas id="captured-canvas" style="display: none;"></canvas>

                        <div class="mt-3">
                            <button id="snap-btn" class="btn btn-success fw-bold" onclick="takeGroupPhoto()">
                                <i class="fa-solid fa-camera-retro me-1"></i> 2. Capture Group Photo (JPG)
                            </button>
                        </div>
                    </div>

                    <form id="photo-form" action="/save_group_photo" method="POST" style="display: none;" class="mt-3">
                        <input type="hidden" name="date" value="{{ selected_date }}">
                        <input type="hidden" name="latitude" id="lat-input">
                        <input type="hidden" name="longitude" id="lng-input">
                        <input type="hidden" name="image_data" id="image-data-input">
                        <button type="submit" class="btn btn-primary fw-bold w-100 py-2">
                            <i class="fa-solid fa-cloud-arrow-up me-1"></i> Save Large Photo & Verification
                        </button>
                    </form>
                </div>
            </div>
        </div>
    </div>

    <!-- Modal 2: Add Student -->
    <div class="modal fade" id="addStudentModal" tabindex="-1" aria-hidden="true">
        <div class="modal-dialog modal-dialog-centered">
            <div class="modal-content border-0 shadow">
                <div class="modal-header text-white" style="background-color: var(--primary-navy);">
                    <h5 class="modal-title fw-bold text-white"><i class="fa-solid fa-user-plus me-2"></i> Register New Student</h5>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <form action="/add_student" method="POST">
                    <div class="modal-body p-4">
                        <input type="hidden" name="date" value="{{ selected_date }}">
                        <div class="mb-3">
                            <label class="form-label fw-bold">Student Roll / ID</label>
                            <input type="text" name="student_id" class="form-control" placeholder="e.g., MCA2026-001" required>
                        </div>
                        <div class="mb-3">
                            <label class="form-label fw-bold">Full Name</label>
                            <input type="text" name="name" class="form-control" placeholder="e.g., Rahul Sharma" required>
                        </div>
                    </div>
                    <div class="modal-footer bg-light">
                        <button type="submit" class="btn btn-primary fw-bold">Save Student</button>
                    </div>
                </form>
            </div>
        </div>
    </div>

    <!-- Modal 3: Send HTML Email Report -->
    <div class="modal fade" id="sendEmailModal" tabindex="-1" aria-hidden="true">
        <div class="modal-dialog modal-dialog-centered">
            <div class="modal-content border-0 shadow">
                <div class="modal-header text-white" style="background-color: var(--primary-navy);">
                    <h5 class="modal-title fw-bold text-white"><i class="fa-solid fa-paper-plane me-2"></i> Send Email Report</h5>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <form action="/send_email" method="POST">
                    <div class="modal-body p-4">
                        <input type="hidden" name="date" value="{{ selected_date }}">
                        <div class="mb-3">
                            <label class="form-label fw-bold">Teacher / Evaluator Name:</label>
                            <input type="text" name="teacher_name" class="form-control" value="{{ current_teacher }}" required>
                        </div>
                        <div class="mb-3">
                            <label class="form-label fw-bold">Recipient Email Address:</label>
                            <input type="email" name="recipient_email" class="form-control" value="ajay.sawarnkar@anudip.org" required>
                        </div>
                    </div>
                    <div class="modal-footer bg-light">
                        <button type="submit" class="btn btn-warning fw-bold text-dark"><i class="fa-solid fa-paper-plane me-1"></i> Send Email Report</button>
                    </div>
                </form>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        let webcamStream = null;

        function toggleStatus(studentId, date) {
            fetch('/toggle_status', {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: `student_id=${studentId}&date=${date}`
            }).then(() => location.reload());
        }

        function getLiveLocation() {
            const statusDiv = document.getElementById('location-status');
            statusDiv.innerHTML = '<i class="fa-solid fa-spinner fa-spin me-1"></i> Fetching location...';

            if ("geolocation" in navigator) {
                navigator.geolocation.getCurrentPosition(position => {
                    const lat = position.coords.latitude.toFixed(6);
                    const lng = position.coords.longitude.toFixed(6);

                    document.getElementById('lat-input').value = lat;
                    document.getElementById('lng-input').value = lng;

                    statusDiv.className = "mb-3 fw-bold text-success";
                    statusDiv.innerHTML = `<i class="fa-solid fa-circle-check me-1"></i> GPS Detected: Lat ${lat}, Lng ${lng}`;

                    document.getElementById('camera-container').style.display = 'block';
                    startCamera();
                }, error => {
                    statusDiv.className = "mb-3 fw-bold text-danger";
                    statusDiv.innerHTML = "Location access denied. Please allow location access in browser.";
                });
            }
        }

        function startCamera() {
            const video = document.getElementById('webcam');
            navigator.mediaDevices.getUserMedia({ video: { width: 1280, height: 720 }, audio: false })
            .then(stream => {
                webcamStream = stream;
                video.srcObject = stream;
            }).catch(err => alert("Camera Error: " + err));
        }

        function takeGroupPhoto() {
            const video = document.getElementById('webcam');
            const canvas = document.getElementById('captured-canvas');
            const context = canvas.getContext('2d');

            canvas.width = video.videoWidth || 1280;
            canvas.height = video.videoHeight || 720;
            context.drawImage(video, 0, 0, canvas.width, canvas.height);

            document.getElementById('image-data-input').value = canvas.toDataURL('image/jpeg', 0.92);

            if(webcamStream) { webcamStream.getTracks().forEach(track => track.stop()); }

            video.style.display = 'none';
            canvas.style.display = 'block';
            document.getElementById('snap-btn').style.display = 'none';
            document.getElementById('photo-form').style.display = 'block';
        }
    </script>
</body>
</html>
"""


# --- ROUTES ---
@app.route("/")
def index():
    selected_date = request.args.get(
        "date", datetime.date.today().strftime("%Y-%m-%d")
    )
    current_teacher = request.args.get("teacher", "Yellow Team Evaluator")

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT s.student_id, s.name, COALESCE(a.status, 'Present')
        FROM students s
        LEFT JOIN attendance a ON s.student_id = a.student_id AND a.date = ?
        ORDER BY s.student_id ASC
    """,
        (selected_date,),
    )
    rows = cursor.fetchall()

    cursor.execute(
        "SELECT teacher_name, latitude, longitude, photo_path FROM session_meta WHERE date = ?",
        (selected_date,),
    )
    session_meta = cursor.fetchone()
    conn.close()

    students = [
        {"student_id": row[0], "name": row[1], "status": row[2]} for row in rows
    ]

    total_students = len(students)
    present_count = sum(1 for s in students if s["status"] == "Present")
    absent_count = sum(1 for s in students if s["status"] == "Absent")
    attendance_rate = (
        round((present_count / total_students) * 100, 1)
        if total_students > 0
        else 0
    )

    return render_template_string(
        HTML_TEMPLATE,
        students=students,
        selected_date=selected_date,
        current_teacher=current_teacher,
        session_meta=session_meta,
        total_students=total_students,
        present_count=present_count,
        absent_count=absent_count,
        attendance_rate=attendance_rate,
    )


@app.route("/add_student", methods=["POST"])
def add_student():
    s_id = request.form.get("student_id").strip()
    name = request.form.get("name").strip()
    date = request.form.get("date")

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO students (student_id, name) VALUES (?, ?)",
            (s_id, name),
        )
        conn.commit()
        flash(f"Student '{name}' registered successfully!", "success")
    except sqlite3.IntegrityError:
        flash(f"Error: Student ID '{s_id}' already exists.", "danger")
    finally:
        conn.close()

    return redirect(url_for("index", date=date))


@app.route("/toggle_status", methods=["POST"])
def toggle_status():
    s_id = request.form.get("student_id")
    date = request.form.get("date")

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT status FROM attendance WHERE student_id = ? AND date = ?",
        (s_id, date),
    )
    res = cursor.fetchone()

    current_status = res[0] if res else "Present"
    new_status = "Absent" if current_status == "Present" else "Present"

    cursor.execute(
        """
        INSERT INTO attendance (student_id, date, status)
        VALUES (?, ?, ?)
        ON CONFLICT(student_id, date) DO UPDATE SET status=excluded.status
    """,
        (s_id, date, new_status),
    )

    conn.commit()
    conn.close()

    return jsonify({"success": True, "new_status": new_status})


@app.route("/save_group_photo", methods=["POST"])
def save_group_photo():
    date = request.form.get("date")
    lat = request.form.get("latitude")
    lng = request.form.get("longitude")
    image_data = request.form.get("image_data")

    if not image_data:
        flash("No photo captured!", "danger")
        return redirect(url_for("index", date=date))

    header, encoded = image_data.split(",", 1)
    binary_data = base64.b64decode(encoded)
    filename = f"group_photo_{date}.jpg"
    filepath = os.path.join(UPLOAD_FOLDER, filename)

    with open(filepath, "wb") as f:
        f.write(binary_data)

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO session_meta (date, teacher_name, latitude, longitude, photo_path)
        VALUES (?, 'Yellow Team Evaluator', ?, ?, ?)
        ON CONFLICT(date) DO UPDATE SET latitude=excluded.latitude, longitude=excluded.longitude, photo_path=excluded.photo_path
    """,
        (date, lat, lng, filepath),
    )
    conn.commit()
    conn.close()

    flash(
        "Large high-resolution group photo (JPG) and live location saved!",
        "success",
    )
    return redirect(url_for("index", date=date))


# --- DOWNLOAD HTML REPORT TO SELF ---
@app.route("/download_report")
def download_report():
    date = request.args.get("date", datetime.date.today().strftime("%Y-%m-%d"))
    teacher_name = request.args.get("teacher", "Yellow Team Evaluator")

    html_content = build_report_html(date, teacher_name)

    return Response(
        html_content,
        mimetype="text/html",
        headers={
            "Content-Disposition": f"attachment; filename=Anudip_MCA_Attendance_{date}.html"
        },
    )


# --- SEND EMAIL REPORT ---
@app.route("/send_email", methods=["POST"])
def send_email():
    date = request.form.get("date")
    recipient_email = request.form.get("recipient_email").strip()
    teacher_name = request.form.get("teacher_name").strip()

    html_body = build_report_html(date, teacher_name)

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = (
            f"Anudip MCA Attendance Report ({date}) - Evaluator: {teacher_name}"
        )
        msg["From"] = SENDER_EMAIL
        msg["To"] = recipient_email
        msg.attach(MIMEText(html_body, "html"))

        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, recipient_email, msg.as_string())
        server.quit()

        flash(
            f"Attendance Report with large group photo successfully emailed to {recipient_email}!",
            "success",
        )
    except Exception as e:
        flash(
            f"Email Sending Failed! Please check SENDER_PASSWORD in app.py. Details: {e}",
            "danger",
        )

    return redirect(url_for("index", date=date, teacher=teacher_name))


if __name__ == "__main__":
    app.run(debug=True, port=5000)