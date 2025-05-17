📄 Project Report: Secure Email Document Listing App
🔐 Objective
To build a secure and feature-rich web application that allows users to authenticate themselves and view a list of received emails along with their attachments. Users can also download attachments directly through the app.

🏗️ Tech Stack
Layer	Technology Used
Frontend	Streamlit (for simplicity & fast prototyping)
Backend	FastAPI
Database	MongoDB (preferred for user/token data)
Email Access	Gmail API (for secure access to emails and attachments)
Auth Tokens	OAuth 2.0 using Gmail’s API

🧩 System Workflow
1. User Authentication Flow
Login initiated from Streamlit interface.

Backend redirects to Google OAuth consent screen.

Upon approval, backend receives token and saves it securely in MongoDB.

Token is used to access Gmail API on behalf of the user.

2. Email Fetching Flow
Once logged in, the app fetches recent emails from the Gmail API.

For each email, the following is extracted:

Sender’s email

Subject

Timestamp

Attachment metadata (if any)

3. Attachment Handling
Each email with attachments provides a download button.

Clicking the button triggers a FastAPI route that:

Fetches the attachment from Gmail

Decodes it

Serves it as a downloadable file with correct filename and media type

🗃️ Database Schema (MongoDB)
json
Copy
Edit
{
  "email": "user@example.com",
  "google_tokens": {
    "token": "access_token",
    "refresh_token": "refresh_token",
    "token_uri": "https://oauth2.googleapis.com/token",
    "client_id": "CLIENT_ID",
    "client_secret": "CLIENT_SECRET",
    "scopes": ["https://www.googleapis.com/auth/gmail.readonly"]
  }
}
🔐 Security Measures Implemented
OAuth 2.0 Authorization: Ensures secure and scoped access to Gmail data.

Token Refreshing: Automatically refreshes expired tokens using the refresh token.

Dependency Injection: FastAPI uses Depends() to ensure secure route access.

No Token Leakage: Tokens are stored securely in the backend, not exposed to frontend.

Sanitized File Download: Prevents path injection or unwanted exposure.

Session Management: Session is cleared upon logout in Streamlit to prevent reuse.

🚀 Bonus Features (Planned / Optional)
🔍 Search & filter emails by sender or subject.

📡 API endpoint to fetch emails (for automation).

🧪 Pytest-based test suite for core API logic.

🧠 Future Improvements
Use Redis or encrypted storage for token caching.

Add multi-user support with JWT or OAuth2 tokens.

Build a React frontend for better UI control and responsiveness.