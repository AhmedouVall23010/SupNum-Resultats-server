from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import auth, students
from app.db.mongo import test_connection
from app.core.config import settings

app = FastAPI(
    title="User Authentication API",
    description="API for user authentication with JWT",
    version="1.0.0"
)

# CORS Middleware - Required for HttpOnly cookies to work with frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.FRONTEND_URL,
        settings.FRONTEND_VITE_URL,
        "http://localhost:5173",  # Vite default port
        "http://localhost:3000",  # React default port
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,  # Required for cookies
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(students.router)

# Test MongoDB connection on startup
@app.on_event("startup")
async def startup_event():
    test_connection()


@app.get("/")
async def root():
    return {"message": "User Authentication API", "status": "running"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}

