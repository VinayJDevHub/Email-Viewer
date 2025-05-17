📧 Secure Email Document Listing App
A secure web application built with Streamlit + FastAPI + MongoDB that allows users to authenticate using their Gmail account and view a list of received emails with attachments. Attachments can be downloaded directly from the UI.

✅ Features
🔐 Google OAuth2.0-based secure login/logout.

📥 Email listing with:

Sender email

Subject

Received timestamp

Attachment info (if available)

⬇️ Direct download option for attachments.

🔍 (Bonus) Search and filter emails by subject/sender.

🛠️ Tech Stack
Layer	Technology
Frontend	Streamlit
Backend	FastAPI
Database	MongoDB (via Atlas/local)
Email API	Gmail API (OAuth 2.0)

🧑‍💻 Setup Instructions
📦 1. Clone the Repository

git clone https://github.com/your-username/secure-email-docs.git
cd secure-email-docs
🧮 2. Setup Python Environment

python -m venv env
source env/bin/activate  # On Windows: env\Scripts\activate
📥 3. Install Requirements

pip install -r requirements.txt
🔑 4. Google OAuth2 Setup
Go to Google Cloud Console.

Create a project and enable Gmail API.

Create OAuth 2.0 credentials:

Set redirect URI as: http://localhost:8000/auth/callback

Download credentials.json and place it in your project root.

🗃️ 5. MongoDB Setup
Use MongoDB Atlas or local MongoDB.

Set the MONGO_URI in your .env file:


MONGO_URI=mongodb+srv://<username>:<password>@cluster.mongodb.net/mydb
SECRET_KEY=your_secret_key
🚀 6. Run Backend (FastAPI)

uvicorn app.main:app --reload
🌐 7. Run Frontend (Streamlit)

streamlit run app/frontend/main.py
🔗 API Endpoints (FastAPI)
Method	Endpoint	Description
GET	/login	Starts Google login
GET	/auth/callback	Handles Google OAuth2 callback
GET	/emails	Lists emails after authentication
GET	/attachment	Downloads specific attachment

