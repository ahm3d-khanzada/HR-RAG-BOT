import streamlit as st
import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime
import time
import os
from dotenv import load_dotenv

load_dotenv()

API_BASE = os.getenv("API_BASE")
AVATAR_USER = os.getenv("AVATAR_USER")
AVATAR_AI   = os.getenv("AVATAR_AI")


if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = None
if "auth_credentials" not in st.session_state:
    st.session_state.auth_credentials = None
if "role" not in st.session_state:
    st.session_state.role = None
if "messages" not in st.session_state:
    st.session_state.messages = []

if "persistent_session" not in st.session_state:
    st.session_state.persistent_session = False

# HELPER FUNCTIONS
def get_first_param(value):
    if isinstance(value, list):
        return value[0] if value else None
    return value if value is not None else None

def display_message(role, content, ts=None):
    avatar = AVATAR_USER if role == "user" else AVATAR_AI
    with st.chat_message(role, avatar=avatar):
        st.markdown(content)
        if ts:
            st.caption(ts.strftime("%H:%M"))

# AUTHENTICATION PAGES
def verify_email(token: str):
    try:
        r = requests.get(f"{API_BASE}/auth/verify-email?token={token}")
        r.raise_for_status()
        st.success(r.json().get("message", "Email verified successfully"))
        st.query_params.clear()
        st.rerun()
    except Exception as e:
        st.error(f"Email verification failed: {str(e)}")

def reset_password_page(token: str):
    st.header("Reset Your Password")
    with st.form("reset_form"):
        npw = st.text_input("New Password", type="password", key="reset_new")
        cpw = st.text_input("Confirm Password", type="password", key="reset_confirm")
        if st.form_submit_button("Reset Password"):
            if npw != cpw:
                st.error("Passwords do not match")
            else:
                try:
                    r = requests.post(f"{API_BASE}/auth/reset-password", json={
                        "token": token,
                        "new_password": npw,
                        "confirm_password": cpw
                    })
                    r.raise_for_status()
                    st.success("Password reset successful. Please login.")
                    st.query_params.clear()
                    st.rerun()
                except Exception as e:
                    st.error(f"Reset failed: {str(e)}")

def signup():
    st.header("Create HR System Account")
    with st.form("signup_form"):
        full_name = st.text_input("Full Name", key="su_full")
        email     = st.text_input("Email", key="su_email")
        username  = st.text_input("Username", key="su_user")
        password  = st.text_input("Password", type="password", key="su_pass")
        role      = st.selectbox("Your Role", ["Employee", "Team Lead", "HR Executive", "HR Manager"], key="su_role")

        team_lead_username = None
        if role == "Employee":
            team_lead_username = st.text_input("Team Lead Username (required)", key="su_teamlead")
            st.info("An employee must be assigned under a Team Lead.")

        if st.form_submit_button("Sign Up"):
            if not all([full_name, email, username, password, role]):
                st.error("Please fill all fields")
                return

            data = {
                "full_name": full_name,
                "email": email,
                "username": username,
                "password": password,
                "role": role
            }

            if role == "Employee":
                if not team_lead_username:
                    st.error("For Employee, Team Lead username is mandatory")
                    return
                data["team_lead_username"] = team_lead_username

            try:
                r = requests.post(f"{API_BASE}/auth/signup", json=data)
                r.raise_for_status()
                st.success("Account created. Please check your email to verify.")
            except Exception as e:
                st.error(f"Sign up failed: {str(e)}")

def login():
    st.header("HR System Login")
    with st.form("login_form"):
        username = st.text_input("Username", key="li_user")
        password = st.text_input("Password", type="password", key="li_pass")
        if st.form_submit_button("Login"):
            try:
                r = requests.post(f"{API_BASE}/auth/login", json={"username": username, "password": password})
                r.raise_for_status()
                data = r.json()
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.auth_credentials = (username, password)
                st.session_state.role = data["role"]
                st.session_state.messages = []
                st.session_state.persistent_session = True
                st.rerun()
            except Exception as e:
                st.error(f"Login failed: {str(e)}")

def forgot_password():
    st.header("Forgot Password")
    with st.form("forgot_form"):
        email = st.text_input("Email", key="fp_email")
        if st.form_submit_button("Send Reset Link"):
            try:
                r = requests.post(f"{API_BASE}/auth/forgot-password", json={"email": email})
                r.raise_for_status()
                st.success("If the email exists, a reset link has been sent.")
            except Exception as e:
                st.error(str(e))

# MAIN APP

def main_app():
    if not st.session_state.get("logged_in", False):
        st.info("Session ended. Redirecting to login...")
        time.sleep(0.6)
        st.rerun()

    username = st.session_state.get("username", "User")
    role = st.session_state.get("role", "—")

    st.title("HR Document & Query System")
    st.caption(f"Welcome, **{username}**   |   Role: **{role.upper()}**")

    with st.sidebar:
        st.header("HR Controls")
        if st.button("Clear Chat History"):
            st.session_state.messages = []
            st.rerun()

        if st.button("Logout", type="primary"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.session_state.logged_in = False
            st.session_state.persistent_session = False
            st.rerun()

    tab_chat, tab_docs, tab_manage = st.tabs(["💬 Ask HR Questions", "📄 HR Document Center", "👥 Manage Users"])

    with tab_chat:
        chat_container = st.container()
        with chat_container:
            if not st.session_state.messages:
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"Hello {username}! I'm your HR assistant. You can ask about leave policies, holidays, attendance, onboarding, or anything in the HR documents you have access to.",
                    "timestamp": datetime.now()
                })

            for msg in st.session_state.messages:
                display_message(msg["role"], msg["content"], msg.get("timestamp"))

        if prompt := st.chat_input("Ask about leave, holidays, attendance, onboarding, policies..."):
            ts = datetime.now()
            st.session_state.messages.append({"role": "user", "content": prompt, "timestamp": ts})
            with chat_container:
                display_message("user", prompt, ts)

            with chat_container:
                with st.chat_message("assistant", avatar=AVATAR_AI):
                    placeholder = st.empty()
                    placeholder.markdown("**Processing your query...**")

                    try:
                        auth = HTTPBasicAuth(*st.session_state.auth_credentials)
                        r = requests.post(
                            f"{API_BASE}/chat/chat",
                            data={"message": prompt},
                            auth=auth,
                            timeout=120
                        )
                        r.raise_for_status()
                        data = r.json()

                        answer = data.get("answer", "No information available in your accessible documents.")
                        sources = data.get("sources", [])

                        response_text = answer
                        if sources:
                            response_text += "\n\n**From Documents:**\n" + "\n".join(f"• {s}" for s in sources)

                        typed = ""
                        for char in response_text:
                            typed += char
                            placeholder.markdown(typed + "▌")
                            time.sleep(0.012)

                        placeholder.markdown(response_text)

                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": response_text,
                            "timestamp": datetime.now()
                        })

                    except Exception as e:
                        placeholder.error(f"Error: {str(e)}")

    with tab_docs:
        st.subheader("Upload HR Documents")
        if role != "HR Manager":
            st.info("Only **HR Manager** can upload new HR documents.")
        else:
            st.markdown("**Upload new HR policies, forms, or guidelines**")
            files = st.file_uploader("Choose files (PDF recommended)", type=["pdf", "docx", "txt"], accept_multiple_files=True, key="hr_doc_upload")

            access_role = st.selectbox(
                "Who should have access to these documents?",
                ["Employee", "Team Lead", "HR Executive", "HR Manager"]
            )

            if files and st.button("Upload HR Documents"):
                with st.spinner("Uploading and indexing documents..."):
                    progress_bar = st.progress(0)
                    status_text = st.empty()

                    form_data = {"access_role": access_role}
                    upload_files = [("files", (f.name, f.getvalue(), f.type)) for f in files]

                    try:
                        auth = HTTPBasicAuth(*st.session_state.auth_credentials)

                        for i in range(1, 101):
                            time.sleep(0.03)
                            progress_bar.progress(i)
                            if i < 30:
                                status_text.text("Preparing files...")
                            elif i < 70:
                                status_text.text("Uploading to server...")
                            else:
                                status_text.text("Indexing in knowledge base...")

                        r = requests.post(
                            f"{API_BASE}/docs/upload_doc",
                            data=form_data,
                            files=upload_files,
                            auth=auth,
                            timeout=300
                        )
                        r.raise_for_status()

                        progress_bar.progress(100)
                        status_text.success("Upload complete!")
                        st.success("HR documents uploaded and indexed successfully!")
                        st.json(r.json())

                    except Exception as e:
                        progress_bar.progress(0)
                        status_text.error(f"Upload failed: {str(e)}")

            if role in ["HR Executive", "HR Manager"]:
                with st.expander("Delete Document Group"):
                    doc_id_del = st.text_input("Enter doc_id to delete")
                    if st.button("Delete Document Group") and doc_id_del:
                        try:
                            auth = HTTPBasicAuth(*st.session_state.auth_credentials)
                            r = requests.delete(f"{API_BASE}/docs/documents/{doc_id_del}", auth=auth)
                            r.raise_for_status()
                            st.success(r.json()["message"])
                        except Exception as e:
                            st.error(f"Delete failed: {str(e)}")

    with tab_manage:
        st.subheader("Manage Users")
        if role == "HR Executive":
            del_user = st.text_input("Username to delete")
            if st.button("Delete User") and del_user:
                try:
                    auth = HTTPBasicAuth(*st.session_state.auth_credentials)
                    r = requests.delete(f"{API_BASE}/auth/users/{del_user}", auth=auth)
                    r.raise_for_status()
                    st.success(r.json()["message"])
                except Exception as e:
                    st.error(f"Delete failed: {str(e)}")
        else:
            st.info("Only HR Executive can manage/delete users.")

# ROUTING LOGIC – Persistent Session Check

st.set_page_config(page_title="HR Document & Query System", layout="wide")

q = st.query_params.to_dict()
action = get_first_param(q.get("action"))
token = get_first_param(q.get("token"))

if action == "verify-email" and token:
    verify_email(token)
elif action == "reset-password" and token:
    reset_password_page(token)
else:
    if st.session_state.get("persistent_session", False) and st.session_state.get("logged_in", False):
        main_app()
    else:
        tab_login, tab_signup, tab_forgot = st.tabs(["Login", "Sign Up", "Forgot Password"])
        with tab_login:
            login()
        with tab_signup:
            signup()
        with tab_forgot:
            forgot_password()