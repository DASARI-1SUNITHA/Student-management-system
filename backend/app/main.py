import logging
import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Import your routers (adjust imports to match your project folder structure)
from app.api.routes import admin, auth, courses, departments, faculty, student

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("sms")

app = FastAPI(
    title="Student Management System API",
    version="1.0.0",
    description="Role-based API for Admin, Faculty, and Student users.",
    docs_url="/api/docs",          # Swagger UI available at /api/docs
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# Configure CORS dynamically from environment variables or allow your Vercel domains
origins = os.getenv("CORS_ORIGINS", "*").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(Exception)
async def unhandled(request: Request, exc: Exception):
    log.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})

@app.get("/api/health", tags=["Health"])
def health():
    return {"status": "ok", "docs": "/api/docs"}

# Include all application routers under the /api prefix
app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])
app.include_router(faculty.router, prefix="/api/faculty", tags=["Faculty"])
app.include_router(student.router, prefix="/api/student", tags=["Student"])
app.include_router(departments.router, prefix="/api/departments", tags=["Departments"])
app.include_router(courses.router, prefix="/api/courses", tags=["Courses"])
