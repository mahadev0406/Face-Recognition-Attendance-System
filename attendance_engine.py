import cv2
import numpy as np
import face_recognition
import os
import pandas as pd
from datetime import datetime
import time

BASE_DIR       = os.path.dirname(os.path.abspath(__file__))
IMAGES_PATH    = os.path.join(BASE_DIR, "faces")
ATTENDANCE_CSV = os.path.join(BASE_DIR, "attendance.csv")
STUDENT_CSV    = os.path.join(BASE_DIR, "student.csv")

RESIZE_SCALE   = 0.40
FACE_TOLERANCE = 0.45

EYE_AR_THRESH       = 0.21
EYE_AR_CONSEC_FRAMES = 1
blink_counters = {}

# ── ENCODINGS ──────────────────────────────────────────────────────────────────

def load_encodings():
    names, encodings = [], []
    if not os.path.exists(IMAGES_PATH):
        print("ERROR: 'faces' folder not found!")
        return names, encodings
    for file in os.listdir(IMAGES_PATH):
        path = os.path.join(IMAGES_PATH, file)
        img  = cv2.imread(path)
        if img is None:
            continue
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        enc = face_recognition.face_encodings(rgb)
        if enc:
            names.append(os.path.splitext(file)[0].upper())
            encodings.append(enc[0])
    return names, encodings

# ── ATTENDANCE WRITE ────────────────────────────────────────────────────────────

def already_marked_in_session(name: str, session_id: str) -> bool:
    """
    Check if this student already has an entry for this specific session.
    """
    if not os.path.exists(ATTENDANCE_CSV):
        return False
    try:
        df = pd.read_csv(ATTENDANCE_CSV)
        df.columns = df.columns.str.strip()
        if "SessionID" not in df.columns:
            return False
        return not df[(df["Name"] == name) & (df["SessionID"] == session_id)].empty
    except Exception:
        return False


def mark_attendance(name: str, start_time: float, session_id: str, session_date: str = None):
    now   = datetime.now()
    today = session_date or now.strftime("%Y-%m-%d")

    # ── SESSION CHECK ──────────────────────────────────────────────────────────
    if already_marked_in_session(name, session_id):
        return

    delay = (time.time() - start_time) / 60

    if   delay <= 5:  score = 100
    elif delay <= 10: score = 75
    elif delay <= 15: score = 50
    else:             score = 0

    email = "N/A"
    if os.path.exists(STUDENT_CSV):
        df = pd.read_csv(STUDENT_CSV, sep=None, engine="python")
        m  = df[df["Name"].str.upper() == name]
        if not m.empty:
            email = m.iloc[0]["Email"]

    if not os.path.exists(ATTENDANCE_CSV):
        with open(ATTENDANCE_CSV, "w") as f:
            f.write("Name,Email,Date,Time,Score,SessionID\n")

    if os.path.exists(ATTENDANCE_CSV):
        with open(ATTENDANCE_CSV, "rb") as f:
            f.seek(0, 2)
            if f.tell() > 0:
                f.seek(-1, 2)
                if f.read(1) != b'\n':
                    with open(ATTENDANCE_CSV, "a") as fa:
                        fa.write("\n")

    with open(ATTENDANCE_CSV, "a") as f:
        f.write(f"{name},{email},{today},{now.strftime('%H:%M:%S')},{score},{session_id}\n")

# ── LIVENESS ───────────────────────────────────────────────────────────────────

def get_ear(eye):
    p1, p2, p3, p4, p5, p6 = [np.array(p) for p in eye]
    a = np.linalg.norm(p2 - p6)
    b = np.linalg.norm(p3 - p5)
    c = np.linalg.norm(p1 - p4)
    return (a + b) / (2.0 * c)

# ── CAMERA SESSION ──────────────────────────────────────────────────────────────

def run_camera():
    names_db, enc_db = load_encodings()
    if not enc_db:
        print("No face data. Add images to 'faces/' folder.")
        return

    cap        = cv2.VideoCapture(0)
    start_time = time.time()
    # session_date and session_id fixed at the moment camera starts
    session_date = datetime.now().strftime("%Y-%m-%d")
    session_id   = datetime.now().strftime("%Y%m%d_%H%M%S")
    # marked set is also keyed per-session to guard in-memory duplicates
    marked     = set()

    CYAN   = (255, 212, 0)
    GREEN  = (136, 255, 0)
    YELLOW = (0, 204, 255)
    ORANGE = (0, 123, 255)
    RED    = (51, 51, 255)
    PANEL  = (36, 15, 15)
    BORDER = (74, 30, 74)
    DIM    = (138, 138, 90)
    WHITE  = (240, 200, 240)

    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        frame     = cv2.flip(frame, 1)
        small     = cv2.resize(frame, (0, 0), fx=RESIZE_SCALE, fy=RESIZE_SCALE)
        rgb_small = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
        scale     = 1 / RESIZE_SCALE

        locs      = face_recognition.face_locations(rgb_small)
        encs      = face_recognition.face_encodings(rgb_small, locs)
        landmarks = face_recognition.face_landmarks(rgb_small, locs)

        h, w    = frame.shape[:2]
        overlay = frame.copy()

        c_len = 40
        cv2.line(frame, (20, 20), (20 + c_len, 20), CYAN, 2)
        cv2.line(frame, (20, 20), (20, 20 + c_len), CYAN, 2)
        cv2.line(frame, (w-20, 20), (w-20-c_len, 20), CYAN, 2)
        cv2.line(frame, (w-20, 20), (w-20, 20+c_len), CYAN, 2)
        cv2.line(frame, (20, h-20), (20+c_len, h-20), CYAN, 2)
        cv2.line(frame, (20, h-20), (20, h-20-c_len), CYAN, 2)
        cv2.line(frame, (w-20, h-20), (w-20-c_len, h-20), CYAN, 2)
        cv2.line(frame, (w-20, h-20), (w-20, h-20-c_len), CYAN, 2)

        for enc, loc, lmark in zip(encs, locs, landmarks):
            distances = face_recognition.face_distance(enc_db, enc)
            best      = np.argmin(distances)
            name      = names_db[best] if distances[best] < FACE_TOLERANCE else "UNKNOWN"

            top, right, bottom, left = [int(v * scale) for v in loc]

            if name != "UNKNOWN" and name not in marked:
                left_eye  = lmark.get('left_eye', [])
                right_eye = lmark.get('right_eye', [])

                if left_eye and right_eye:
                    ear = (get_ear(left_eye) + get_ear(right_eye)) / 2.0
                    print(f"Liveness [{name}]: EAR={ear:.3f}")

                    if ear < EYE_AR_THRESH:
                        blink_counters[name] = blink_counters.get(name, 0) + 1
                    else:
                        if blink_counters.get(name, 0) >= EYE_AR_CONSEC_FRAMES:
                            # Pass session_id so all entries in one session
                            # share the same ID for grouping
                            mark_attendance(name, start_time, session_id, session_date)
                            marked.add(name)
                        blink_counters[name] = 0

            if name in marked:
                box_col = GREEN
                tag_txt = f"{name} - VERIFIED"
            elif name != "UNKNOWN":
                box_col = YELLOW
                tag_txt = f"{name} - BLINK TO VERIFY"
                count = blink_counters.get(name, 0)
                if count > 0:
                    cv2.putText(frame, "DETECTING...", (left, bottom + 20),
                                cv2.FONT_HERSHEY_DUPLEX, 0.5, CYAN, 1)
            else:
                box_col = RED
                tag_txt = "UNKNOWN"

            cv2.rectangle(frame, (left, top), (right, bottom), box_col, 1)
            cv2.rectangle(overlay, (left, top - 25), (right, top), box_col, -1)
            cv2.putText(frame, tag_txt, (left + 5, top - 7),
                        cv2.FONT_HERSHEY_DUPLEX, 0.5, (0, 0, 0), 1)

        elapsed = (time.time() - start_time) / 60
        elapsed = min(elapsed, 15.0)

        if elapsed <= 5:
            status, s_col = "ON TIME", GREEN
        elif elapsed <= 10:
            status, s_col = "LATE", YELLOW
        elif elapsed < 15:
            status, s_col = "TOO LATE", ORANGE
        else:
            print("15-minute window expired. Closing...")
            break

        cv2.rectangle(overlay, (20, 20), (250, 68), PANEL, -1)
        cv2.rectangle(overlay, (20, 20), (250, 68), BORDER, 1)

        det_text = f"DETECTED: {len(marked)}"
        cv2.rectangle(overlay, (w-200, 20), (w-20, 68), PANEL, -1)
        cv2.rectangle(overlay, (w-200, 20), (w-20, 68), BORDER, 1)

        bar_h = 40
        bar_y = h - bar_h - 10
        cv2.rectangle(overlay, (20, bar_y), (w-20, bar_y + bar_h), PANEL, -1)
        cv2.rectangle(overlay, (20, bar_y), (w-20, bar_y + bar_h), BORDER, 1)
        cv2.line(overlay, (20, bar_y), (w-20, bar_y), RED, 2)

        cv2.addWeighted(overlay, 0.55, frame, 0.45, 0, frame)

        cv2.putText(frame, "AIKR LIVE", (35, 40), cv2.FONT_HERSHEY_DUPLEX, 0.4, DIM, 1)
        cv2.putText(frame, f"STATUS: {status}", (35, 60), cv2.FONT_HERSHEY_DUPLEX, 0.55, s_col, 1)
        cv2.putText(frame, det_text, (w-190, 40), cv2.FONT_HERSHEY_DUPLEX, 0.4, DIM, 1)
        mins = int(elapsed)
        secs = int((elapsed - mins) * 60)
        cv2.putText(frame, f"ELAPSED: {mins:02d}:{secs:02d}", (w-190, 60),
                    cv2.FONT_HERSHEY_DUPLEX, 0.45, CYAN, 1)
        cv2.putText(frame, "PRESS [Q] TO END SESSION", (w//2 - 130, bar_y + 26),
                    cv2.FONT_HERSHEY_DUPLEX, 0.55, RED, 1)

        cv2.imshow("AIKR - Face Attendance", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()

# ── DATA HELPERS ────────────────────────────────────────────────────────────────

def load_attendance():
    if not os.path.exists(ATTENDANCE_CSV):
        return pd.DataFrame(columns=["Name", "Email", "Date", "Time", "Score", "SessionID"])
    df = pd.read_csv(ATTENDANCE_CSV)
    df.columns = df.columns.str.strip()
    df["Date"]  = pd.to_datetime(df["Date"], errors="coerce")
    df["Score"] = pd.to_numeric(df["Score"], errors="coerce").fillna(0)
    return df


def compute_scores(df):
    if df.empty:
        return pd.DataFrame()
    group_col = "SessionID" if "SessionID" in df.columns else "Date"
    g = df.groupby("Name").agg(
        Sessions = (group_col,  "nunique"),
        AvgScore = ("Score", "mean"),
        Email    = ("Email", "first"),
    ).reset_index()
    g["AvgScore"] = g["AvgScore"].round(1)
    return g


def session_summary(df):
    if df.empty:
        return []
    out = []
    group_col = "SessionID" if "SessionID" in df.columns else "Date"
    for gid, grp in df.groupby(group_col):
        date_obj = grp["Date"].iloc[0]
        out.append({
            "date":     date_obj.strftime("%Y-%m-%d") if hasattr(date_obj, "strftime") else str(date_obj),
            "total":    len(grp),
            "on_time":  int((grp["Score"] == 100).sum()),
            "late":     int((grp["Score"] == 75).sum()),
            "too_late": int((grp["Score"] == 50).sum()),
            "absent":   int((grp["Score"] == 0).sum()),
            "sid":      gid
        })
    return sorted(out, key=lambda x: str(x["sid"]), reverse=True)


if __name__ == "__main__":
    run_camera()