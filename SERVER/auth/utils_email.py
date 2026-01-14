import os
from datetime import datetime
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import aiosmtplib

# ---------------- CONFIG ----------------
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")

SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")
SALT_EMAIL = "email-confirm"
SALT_RESET = "password-reset"

# ---------------- TOKEN ----------------
def generate_token(email: str, salt: str) -> str:
    serializer = URLSafeTimedSerializer(SECRET_KEY)
    return serializer.dumps(email, salt=salt)

def verify_token(token: str, salt: str, expiration: int = 3600) -> str | None:
    serializer = URLSafeTimedSerializer(SECRET_KEY)
    try:
        email = serializer.loads(token, salt=salt, max_age=expiration)
        return email
    except SignatureExpired:
        print("Token expired")
        return None
    except BadSignature:
        print("Invalid token")
        return None

# ---------------- HTML EMAIL ----------------
def create_email_html(subject: str, main_text: str) -> str:
    year = datetime.now().year
    html_content = f"""
<html>
  <body style="font-family: Arial, sans-serif; background-color: #f4f9ff; margin: 0; padding: 0;">
    <table width="100%" style="max-width: 600px; margin: 40px auto; background-color: white; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
      <!-- Header -->
      <tr style="background-color: #007BFF;">
        <td style="padding: 20px;">
          <h2 style="color: white; margin: 0; text-align: left;">Ahmed Khanzada HR System</h2>
        </td>
      </tr>
      <!-- Body -->
      <tr>
        <td style="padding: 30px; color: #333; text-align: left;">
          <p style="font-size: 16px;">Dear User,</p>
          <p style="font-size: 16px; line-height: 1.6;">
            {main_text}
          </p>
          <p style="margin-top: 30px; font-size: 15px;">
            Best Regards,<br>
            <strong>Ahmed Khanzada HR Chatbot Team</strong>
          </p>
        </td>
      </tr>
      <!-- Footer -->
      <tr style="background-color: #f0f8ff;">
        <td style="padding: 15px; color: #777; font-size: 13px; text-align: left;">
          <div style="margin-bottom: 10px;">
            © {year} Ahmed Khanzada HR Chatbot | All Rights Reserved
          </div>
        </td>
      </tr>
    </table>
  </body>
</html>
"""
    return html_content

# ---------------- SEND EMAIL ----------------
async def send_email(
    to_email: str,
    subject: str,
    main_text: str,
    attachment_path: str | None = None
) -> None:
    """
    Send an email asynchronously with optional PDF attachment.
    """
    msg = MIMEMultipart()
    msg['From'] = f"Ahmed Khanzada HR Chatbot <{SENDER_EMAIL}>"
    msg['To'] = to_email
    msg['Subject'] = subject

    # Attach HTML body
    msg.attach(MIMEText(create_email_html(subject, main_text), "html"))

    # Optional attachment
    if attachment_path:
        if os.path.exists(attachment_path):
            try:
                with open(attachment_path, "rb") as f:
                    attach = MIMEApplication(f.read(), _subtype="pdf")
                    attach.add_header(
                        "Content-Disposition",
                        "attachment",
                        filename=os.path.basename(attachment_path)
                    )
                    msg.attach(attach)
            except Exception as e:
                print(f"[ERROR] Failed to attach file '{attachment_path}': {e}")
        else:
            print(f"[WARNING] Attachment path does not exist: {attachment_path}")

    # Send email asynchronously
    try:
        await aiosmtplib.send(
            msg,
            hostname=SMTP_SERVER,
            port=SMTP_PORT,
            start_tls=True,
            username=SENDER_EMAIL,
            password=SENDER_PASSWORD
        )
        print(f"[INFO] Email sent to {to_email} successfully.")
    except Exception as e:
        print(f"[ERROR] Failed to send email to {to_email}: {e}")