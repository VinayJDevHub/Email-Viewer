# In your FastAPI router file

from fastapi import APIRouter, HTTPException, Request, Depends, Query
from fastapi.responses import RedirectResponse, FileResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from datetime import datetime, timedelta
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request as GoogleRequest
from googleapiclient.discovery import build
from db import users_collection
from typing import Optional
from fastapi import Header  
import os
import tempfile
import base64

router = APIRouter()
SECRET_KEY = os.getenv("JWT_SECRET", "secret")
ALGORITHM = "HS256"
security = HTTPBearer()

# Environment configs
CLIENT_ID = os.getenv(
    "GOOGLE_CLIENT_ID", "1096448022631-i3arbmvm40iem4j1ta1tq7e9i631cv7m.apps.googleusercontent.com")
CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET",
                          "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")
REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI",
                         "http://localhost:8000/auth/google/callback")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:8501")

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/userinfo.email",
    "openid"
]

GOOGLE_CREDS_DICT = {
    "web": {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uris": [REDIRECT_URI],
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token"
    }
}


def create_token(email: str):
    payload = {
        "sub": email,
        "exp": datetime.utcnow() + timedelta(hours=6)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(
    token: Optional[str] = Query(None),
    authorization: Optional[str] = Header(None)
):
    jwt_token = None

    if authorization and authorization.startswith("Bearer "):
        jwt_token = authorization.split(" ")[1]
    elif token:
        jwt_token = token
    else:
        raise HTTPException(status_code=403, detail="Token missing")

    try:
        payload = jwt.decode(jwt_token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=403, detail="Invalid or expired token")


@router.get("/auth/google")
def google_auth_redirect():
    flow = Flow.from_client_config(
        GOOGLE_CREDS_DICT, scopes=SCOPES, redirect_uri=REDIRECT_URI)
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        prompt="consent",
        include_granted_scopes="true"
    )
    return RedirectResponse(auth_url)


@router.get("/auth/google/callback")
def google_auth_callback(request: Request):
    code = request.query_params.get("code")
    if not code:
        raise HTTPException(
            status_code=400, detail="Missing authorization code")

    flow = Flow.from_client_config(
        GOOGLE_CREDS_DICT, scopes=SCOPES, redirect_uri=REDIRECT_URI)
    flow.fetch_token(code=code)
    creds = flow.credentials

    user_info_service = build("oauth2", "v2", credentials=creds)
    user_info = user_info_service.userinfo().get().execute()

    user_email = user_info.get("email")
    if not user_email:
        raise HTTPException(status_code=400, detail="Email not found")

    users_collection.update_one(
        {"email": user_email},
        {"$set": {
            "google_tokens": {
                "token": creds.token,
                "refresh_token": creds.refresh_token,
                "token_uri": creds.token_uri,
                "client_id": creds.client_id,
                "client_secret": creds.client_secret,
                "scopes": list(creds.scopes)
            }
        }},
        upsert=True
    )

    jwt_token = create_token(user_email)
    return RedirectResponse(f"{FRONTEND_URL}?token={jwt_token}&email={user_email}")


def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")  # email stored as 'sub'
    except JWTError:
        raise HTTPException(status_code=403, detail="Not authenticated")


@router.get("/emails")
def get_emails(current_email: str = Depends(get_current_user)):
    # Your existing logic unchanged
    user = users_collection.find_one({"email": current_email})
    if not user or "google_tokens" not in user:
        raise HTTPException(status_code=403, detail="Google not linked")

    token_data = user["google_tokens"]
    creds = Credentials(
        token=token_data["token"],
        refresh_token=token_data["refresh_token"],
        token_uri=token_data["token_uri"],
        client_id=token_data["client_id"],
        client_secret=token_data["client_secret"],
        scopes=token_data["scopes"]
    )

    if creds.expired and creds.refresh_token:
        creds.refresh(GoogleRequest())
        users_collection.update_one(
            {"email": current_email},
            {"$set": {"google_tokens.token": creds.token}}
        )

    service = build("gmail", "v1", credentials=creds)
    messages = service.users().messages().list(
        userId="me", maxResults=10).execute().get("messages", [])

    email_list = []
    for msg in messages:
        msg_data = service.users().messages().get(
            userId="me", id=msg["id"]).execute()
        headers = msg_data.get("payload", {}).get("headers", [])
        subject = next((h["value"]
                        for h in headers if h["name"] == "Subject"), "No Subject")
        sender = next((h["value"] for h in headers if h["name"]
                       == "From"), "Unknown Sender")
        date = next((h["value"]
                     for h in headers if h["name"] == "Date"), "Unknown Date")

        attachments = []
        parts = msg_data.get("payload", {}).get("parts", [])
        for part in parts:
            if part.get("filename") and "attachmentId" in part.get("body", {}):
                attachments.append({
                    "filename": part["filename"],
                    "attachmentId": part["body"]["attachmentId"],
                    "messageId": msg["id"]
                })

        email_list.append({
            "subject": subject,
            "from": sender,
            "date": date,
            "attachments": attachments
        })

    return email_list


@router.get("/attachment")
def download_attachment(
    message_id: str,
    attachment_id: str,
    filename: str,
    current_email: str = Depends(get_current_user)
):
    # 🔐 1. User & Token Check
    user = users_collection.find_one({"email": current_email})
    if not user or "google_tokens" not in user:
        raise HTTPException(status_code=403, detail="Google not linked")

    token_data = user["google_tokens"]
    creds = Credentials(
        token=token_data["token"],
        refresh_token=token_data["refresh_token"],
        token_uri=token_data["token_uri"],
        client_id=token_data["client_id"],
        client_secret=token_data["client_secret"],
        scopes=token_data["scopes"]
    )

    # 🔄 2. Refresh Token if Expired
    if creds.expired and creds.refresh_token:
        creds.refresh(GoogleRequest())
        users_collection.update_one(
            {"email": current_email},
            {"$set": {"google_tokens.token": creds.token}}
        )

    # 📥 3. Gmail API Fetch
    service = build("gmail", "v1", credentials=creds)
    attachment = service.users().messages().attachments().get(
        userId="me", messageId=message_id, id=attachment_id
    ).execute()

    data = base64.urlsafe_b64decode(attachment["data"].encode("UTF-8"))

    # 💾 4. Save to Temp Path
    temp_dir = tempfile.gettempdir()
    path = os.path.join(temp_dir, filename)

    with open(path, "wb") as f:
        f.write(data)

    # 📦 5. Send File As Download
    return FileResponse(
        path,
        filename=filename,
        media_type='application/octet-stream',
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )
