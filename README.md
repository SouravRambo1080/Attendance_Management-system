# Attendance_Management-system
A smart, full-stack Flask web application for **Anudip Foundation (MCA Branch - Yellow Team)** designed to digitize, verify, and automate daily student attendance tracking.
# 🎓 Anudip Foundation — Smart MCA Attendance & Verification Portal

A smart, full-stack Flask web application for **Anudip Foundation (MCA Branch - Yellow Team)** designed to digitize, verify, and automate daily student attendance tracking.

---

## ✨ Features

- ⚡ **One-Click Attendance Roster:** Real-time AJAX toggling between `Present` and `Absent` states.
- 📸 **Live Webcam Group Photo Capture:** Captures a high-resolution single group photo (`.jpg`) for the entire class session.
- 📍 **Live GPS Location Verification:** Detects exact Latitude & Longitude using the browser Geolocation API.
- ⏰ **6-Hour Shift Clock Tracking:** Standardized shift logging (09:00 AM - 03:00 PM) for training compliance.
- 📊 **Real-Time KPI Dashboard:** Live cards tracking Total Roster, Present Count, Absent Count, and Attendance Rate (%).
- ✉️ **Executive HTML Email Reports:** Automatically dispatches styled HTML summary reports—including embedded group photos and GPS coordinates—to stakeholders (`ajay.sawarnkar@anudip.org`).
- 💾 **Offline Report Download:** Download complete HTML attendance summaries directly to your local computer for offline viewing.
- 🗄️ **SQLite Persistence:** Clean database storage across dates with `UPSERT` capabilities.

---

## 🛠️ Tech Stack

- **Frontend:** HTML5, CSS3, JavaScript (Fetch API, WebRTC MediaStream, Geolocation API), Bootstrap 5.3, FontAwesome 6
- **Backend:** Python 3, Flask
- **Database:** SQLite3
- **Email Engine:** Python `smtplib` (SSL Port 465) + `email.mime`

---

## 📂 Database Schema Design

### 1. `students` (Master Roster)
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Record ID |
| `student_id` | TEXT | UNIQUE, NOT NULL | Student Roll / ID |
| `name` | TEXT | NOT NULL | Student Full Name |

### 2. `attendance` (Daily Logs)
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Record ID |
| `student_id` | TEXT | FOREIGN KEY, NOT NULL | Student Roll ID |
| `date` | TEXT | NOT NULL | Date (`YYYY-MM-DD`) |
| `status` | TEXT | NOT NULL | `Present` / `Absent` |
| `teacher_name`| TEXT | DEFAULT 'Yellow Team' | Evaluator Name |

### 3. `session_meta` (Verification Metadata)
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `date` | TEXT | PRIMARY KEY | Session Date |
| `teacher_name`| TEXT | - | Trainer Name |
| `latitude` | TEXT | - | GPS Latitude |
| `longitude` | TEXT | - | GPS Longitude |
| `photo_path` | TEXT | - | Saved JPG image path |

---

## 🚀 Quick Start Guide

### 1. Install Dependencies
```bash
pip install flask
