import streamlit as st
import requests
import webbrowser

st.set_page_config(page_title="📬 Gmail Inbox Viewer", layout="wide")
BASE_URL = "http://127.0.0.1:8000"

if "token" not in st.session_state:
    st.session_state.token = None
if "email" not in st.session_state:
    st.session_state.email = ""

query_params = st.query_params
if st.session_state.token is None and "token" in query_params:
    st.session_state.token = query_params["token"]
    st.session_state.email = query_params.get("email", "")
    st.rerun()


def login_with_google():
    try:
        auth_url = f"{BASE_URL}/auth/google"
        webbrowser.open_new_tab(auth_url)
        st.info("🔄 Redirecting to Google Login...")
    except Exception as e:
        st.error(f"⚠️ Could not open login page: {e}")


def logout():
    st.session_state.token = None
    st.session_state.email = ""
    st.success("✅ Logged out.")
    st.rerun()


if st.session_state.token is None:
    st.title("🔐 Login to Gmail Inbox Viewer")
    st.button("Login with Google", on_click=login_with_google)
else:
    st.title(f"📬 Inbox - {st.session_state.email}")
    if st.button("Logout"):
        logout()

    headers = {"Authorization": f"Bearer {st.session_state.token}"}

    with st.spinner("Fetching your Gmail messages..."):
        try:
            response = requests.get(f"{BASE_URL}/emails", headers=headers)
            response.raise_for_status()
            emails = response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"❌ Failed to fetch emails: {e}")
            emails = []

    if emails:
        search = st.text_input(
            "🔍 Search (by subject or sender)").lower().strip()
        filtered = [
            email for email in emails
            if search in email["subject"].lower() or search in email["from"].lower()
        ] if search else emails

        for email in filtered:
            with st.expander(f"📨 {email['subject']}"):
                st.write(f"**From**: {email['from']}")
                st.write(f"**Date**: {email['date']}")
                if email.get("attachments"):
                    st.markdown("📎 **Attachments:**")
                    for attach in email["attachments"]:
                        # Add token as query param here for authentication
                        url = (
                            f"{BASE_URL}/attachment"
                            f"?message_id={attach['messageId']}"
                            f"&attachment_id={attach['attachmentId']}"
                            f"&filename={attach['filename']}"
                            f"&token={st.session_state.token}"
                        )
                        st.markdown(
                            f"[📥 {attach['filename']}]({url})", unsafe_allow_html=True)
    else:
        st.info("📭 No emails found.")
