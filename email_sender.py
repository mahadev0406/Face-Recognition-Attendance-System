import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")
FROM_NAME = os.getenv("FROM_NAME", "AIKR Attendance System")


def send_warning(name: str, to_email: str, avg_score: float, custom_msg: str = "") -> bool:
    if not SMTP_USER or not SMTP_PASS:
        print("SMTP not configured — check your .env file.")
        return False

    subject = f"⚠️ Attendance Warning — {name}"
## VIBE CODED PART #1 ##
    html = f"""
<!DOCTYPE html><html><head>
<style>
  body  {{ margin:0; padding:0; background:#06060f; font-family:'Segoe UI',sans-serif; color:#c8c8f0; }}
  .wrap {{ max-width:560px; margin:40px auto; background:#0d0d1f;
           border:1px solid #1e1e4a; border-radius:16px; overflow:hidden; }}
  .hdr  {{ background:linear-gradient(135deg,#13132e,#06060f);
           padding:32px; text-align:center; border-bottom:2px solid #ff3366; }}
  .hdr h1 {{ margin:0; font-size:22px; color:#ff6b6b; letter-spacing:3px; font-family:monospace; }}
  .hdr p  {{ margin:6px 0 0; color:#5a5a8a; font-size:12px; letter-spacing:2px; }}
  .body {{ padding:32px; line-height:1.7; }}
  .box  {{ background:#13132e; border:1px solid #ff3366; border-radius:12px;
           padding:24px; text-align:center; margin:20px 0; }}
  .box .num {{ font-size:52px; font-weight:900; color:#ff3366; font-family:monospace; line-height:1; }}
  .box .lbl {{ font-size:11px; color:#5a5a8a; letter-spacing:3px; margin-top:6px; }}
  .note {{ background:#1e1e3f; border-left:3px solid #4d4dff;
           padding:12px 16px; border-radius:0 8px 8px 0; margin:16px 0;
           font-size:14px; color:#a0a0d0; }}
  .ftr  {{ text-align:center; padding:16px; border-top:1px solid #1e1e4a;
           font-size:11px; color:#3a3a6a; }}
</style></head><body>
<div class="wrap">
  <div class="hdr">
    <h1>⚠ ATTENDANCE WARNING</h1>
    <p>AIKR ATTENDANCE MANAGEMENT SYSTEM</p>
  </div>
  <div class="body">
    <p>Dear <strong>{name}</strong>,</p>
    <p>Your current average attendance score is below the required threshold:</p>
    <div class="box">
      <div class="num">{avg_score:.1f}</div>
      <div class="lbl">AVERAGE SCORE / 100</div>
    </div>
    <p>Please ensure you attend all upcoming sessions <strong>on time</strong> to improve your standing.</p>
    {f'<div class="note"><strong>Note from instructor:</strong><br>{custom_msg}</div>' if custom_msg else ''}
    <p>Contact your instructor if you have any concerns.</p>
    <p style="color:#5a5a8a;">— AIKR System</p>
  </div>
  <div class="ftr">Automated message · Do not reply</div>
</div>
</body></html>
"""

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = f"{FROM_NAME} <{SMTP_USER}>"
        msg["To"]      = to_email
        msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
            s.ehlo()
            s.starttls()
            s.login(SMTP_USER, SMTP_PASS)
            s.sendmail(SMTP_USER, to_email, msg.as_string())

        print(f"[EMAIL] Sent warning to {name} <{to_email}>")
        return True

    except Exception as e:
        print(f"[EMAIL] Failed for {name}: {e}")
        return False
