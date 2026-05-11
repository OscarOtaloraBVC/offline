# main.py
from fastapi import FastAPI
from api import users_api, profiles_api, k8s_api
from api import alerts_api  # 👈 
from api import certificates_api  # 👈
from fastapi.middleware.cors import CORSMiddleware
from database.db import DATABASE_URL
import os
from fastapi.staticfiles import StaticFiles
from pathlib import Path # For cleaner path handling
from fastapi.responses import RedirectResponse

app = FastAPI(
    title="Simple CRUD API",
    description="A demonstration of CRUD operations with FastAPI and SQLite.",
    version="0.1.0",
)

origins = [
    "http://localhost:3000",  # React frontend development server
    "http://localhost:3002",
    "http://localhost:8080",
    "http://localhost:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Allows specific origins
    allow_credentials=True, # Allows cookies to be included in requests
    allow_methods=["*"],    # Allows all methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],    # Allows all headers
)

# --- Database Initialization on Startup ---
@app.on_event("startup")
async def startup_event():
    """
    Actions to perform on application startup.
    Checks if the database file exists and initializes it if not.
    """
    print("Application startup: Checking database...")
    if not os.path.exists(DATABASE_URL):
        print(f"****ERROR****: Database file not found at {DATABASE_URL}. Initializing database...")
        print("****SOLUTION****: Inner container execute:  /opt/rbac-manager/backend/bin/install-create-db-sqlite3.sh")
        try:
            init_db_command() # This function creates tables if they don't exist
            print("Database initialized successfully.")
        except Exception as e:
            print(f"Error initializing database: {e}")
            # Optionally, you might want to prevent the app from starting if DB init fails
            # raise RuntimeError(f"Failed to initialize database: {e}")
    else:
        print(f"Database file found at {DATABASE_URL}.")
    print("Application startup complete.")

# --- Include API Routers ---
# These lines import your endpoint definitions from the api/ directory
app.include_router(users_api.router, prefix="/api/v1")
app.include_router(profiles_api.router, prefix="/api/v1")
app.include_router(k8s_api.router, prefix="/api/v1")
app.include_router(alerts_api.router, prefix="/api/v1") # 👈
app.include_router(certificates_api.router, prefix="/api/v1")  # 👈 NUEVO


# Static Frontend Site
EXTERNAL_STATIC_DIR_ABSOLUTE =os.getenv('RBAC_STATIC_FRONTEND_DIR')
if(EXTERNAL_STATIC_DIR_ABSOLUTE!=None and EXTERNAL_STATIC_DIR_ABSOLUTE!=""):
    app.mount(
        "/ui",
        StaticFiles(directory=EXTERNAL_STATIC_DIR_ABSOLUTE, html=True),
        name="external_site"
    )

# --- Root Endpoint ---
@app.get("/", tags=["Root"])
async def read_root():
    # """
    # A simple root endpoint to confirm the API is running.
    # """
    # return {
    #     "message": "Welcome to the Simple CRUD API.",
    #     "documentation_url": "/docs", # Default FastAPI Swagger UI
    #     "redoc_url": "/redoc"        # Default FastAPI ReDoc
    # }
    return RedirectResponse(url="/ui")