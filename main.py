from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from auth import router as auth_router

# ✅ Load environment variables first
load_dotenv()

app = FastAPI()

# ✅ Add CORS middleware (adjust allow_origins if needed)
app.add_middleware(
    CORSMiddleware,
    # You can replace "*" with specific frontend URL for better security
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Include your authentication routes
app.include_router(auth_router)
