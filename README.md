#  AIKR - Smart Face Attendance System v2.0

![AIKR Dashboard](AIKR.png)

AIKR is a premium, AI-powered attendance tracking system designed for modern classrooms and offices. It utilizes state-of-the-art Computer Vision to identify students in real-time, compute performance scores based on punctuality, and automate administrative tasks through a futuristic, Cyberpunk-inspired dashboard.

---

##  Key Features

- ** AI Identification**: High-accuracy face recognition using the HOG algorithm and Deep Learning embeddings.
- ** Liveness Detection**: Integrated "Blink-to-Verify" mechanism to prevent spoofing via photos or screens.
- ** Cyber HUD**: A real-time camera overlay featuring scanning effects, elapsed session timers, and status tracking.
- ** Glassmorphism Dashboard**: A stunning web UI with live analytics, score distributions, and attendance trends.
- ** Dynamic Scoring**: Automated score calculation based on arrival time:
  - **On Time (≤ 5m)**: 100 Points
  - **Late (5 - 10m)**: 75 Points
  - **Too Late (10 - 15m)**: 50 Points
  - **Missed (> 15m)**: 0 Points
- ** Automated Warnings**: One-click email alerts for students falling below performance thresholds.

---

##  Tech Stack

- **Backend**: Python 3.10+, Flask
- **Frontend**: Vanilla JavaScript, Jinja2, Chart.js, Orbitron Typography
- **AI/CV**: OpenCV, Dlib, Face Recognition
- **Data**: Pandas (CSV-based persistent storage)
- **Email**: SMTP with HTML Templating

---

##  Installation Steps

```bash
# 1. Install dependencies
pip install -r requirements.txt
 
# 2. Copy and fill .env
cp .env.example .env
# Edit SMTP_USER and SMTP_PASS for Gmail App Password
 
# 3. Run the Flask dashboard
python app.py
 
# 4. Open browser at
http://localhost:5000
```

##  How to Run

1. **Prepare Student Data**:
   - Place student headshots in the `faces/` directory. Name files as `FullName.jpg` (e.g., `Mahadev.jpg`).
   - (Optional) Update `student.csv` with student names and emails for automated alerts.

2. **Launch the Application**:
   ```bash
   python app.py
   ```

3. **Access the Dashboard**:
   Open your browser and navigate to: `http://127.0.0.1:5000`

4. **Start a Session**:
   Click **"START SESSION"** on the top bar. The AI camera will initialize. Students simply need to look at the camera and **blink** to mark their attendance.

---

##  Example Input/Output

###  Input
- **Face Image**: `faces/Mahadev.jpg`
- **Session Start**: 10:00 AM
- **Student Arrives**: 10:04 AM (4 minutes elapsed)

###  Output
- **Camera Feedback**: `Mahadev - VERIFIED` (Green Box)
- **CSV Record**: `Mahadev,mahadev.d24@iiits.in,2024-05-03,10:04:12,100,20240503_100000`
- **Dashboard**: The "On Time" percentage increases; Gokul's average score is updated in the leaderboard.

---
