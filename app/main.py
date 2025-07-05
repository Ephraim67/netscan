import json
import os
import logging
from datetime import datetime

from fastapi import FastAPI, Request, Depends, Form, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from sqlalchemy.orm import Session
from sqlalchemy import text

from models.database import Base, ScanTarget, engine, SessionLocal, ScanHistory, get_db
from routes import scan
from schemas.scan import ScanRequest

# Optional: Import Netscan if it's a class used in scan.get_scanner
# from scanner.netscan import Netscan

# Create FastAPI app
app = FastAPI(
    title="NetScan Port Scanner API",
    # description="Easy-to-use network port scanner",
    version="1.0.0"
)

# Mount static and template folders
# app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Logging config
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create DB tables at startup
@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)

# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation Error",
            "detail": exc.errors(),
            "message": "Please check your request parameters"
        }
    )

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "HTTP Error",
            "status_code": exc.status_code,
            "detail": exc.detail
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal Server Error", "detail": str(exc)}
    )

# Include the router
app.include_router(scan.router, prefix="/api/v1", tags=["scanning"])

# Root route
@app.get("/")
async def root():
    return {
        "message": "Port Scanner API",
        "version": "1.0.0",
        "documentation": {
            "swagger": "/docs",
            "redoc": "/redoc"
        },
        "endpoints": {
            "health": "/health",
            "scanner_health": "/api/v1/scans/health",
            "scan_single": "/api/v1/scans/single"
        }
    }

@app.get("/health")
async def app_health():
    return {
        "status": "healthy",
        "application": "port-scanner-api",
        "version": "1.0.0"
    }

@app.get("/scan", response_class=HTMLResponse)
async def scan_interface(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse("scan_interface.html", {"request": request})


@app.get("/results", response_class=HTMLResponse)
async def scan_interface(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse("results.html", {"request": request})

@app.get("/schedulescan")
async def schedule_scan(request: Request):
    response = templates.TemplateResponse(
        "schedule_scan.html",
        {"request": request}
    )
    response.headers["Content-Type"] = "text/html; charset=utf-8"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


# @app.get("/results", response_class=HTMLResponse)
# async def view_results(request: Request, db: Session = Depends(get_db)):
#     recent_scans = db.query(ScanHistory)\
#                     .order_by(ScanHistory.scan_time.desc())\
#                     .limit(20)\
#                     .all()
#     return templates.TemplateResponse("results.html", {
#         "request": request,
#         "scans": recent_scans
#     })

@app.get("/test-db")
def test_db_connection(db: Session = Depends(get_db)):
    try:
        result = db.execute(text("SELECT 1")).fetchone()
        return {"db_connected": True, "result": result[0]}
    except Exception as e:
        return {"db_connected": False, "error": str(e)}

# @app.post("/scan-form")
# async def scan_form(
#     request: Request,
#     target: str = Form(...),
#     scanner = Depends(scan.get_scanner),  # Netscan type optional
#     db: Session = Depends(get_db)
# ):
#     try:
#         scan_request = ScanRequest(target=target)
#         start_time = datetime.utcnow()

#         existing_target = db.query(ScanTarget).filter(ScanTarget.target == target).first()

#         if not existing_target:
#             scan_target = ScanTarget(target=target, status="scanning")
#             db.add(scan_target)
#             db.commit()
#             db.refresh(scan_target)
#         else:
#             existing_target.status = "scanning"
#             existing_target.updated_at = datetime.utcnow()
#             db.commit()
#             scan_target = existing_target

#         result_dic = scanner.scan_host(target)

#         end_time = datetime.utcnow()
#         scan_duration = int((end_time - start_time).total_seconds())

#         scan_target.status = "completed"
#         scan_target.result = json.dumps(result_dic)
#         scan_target.updated_at = end_time

#         scan_history = ScanHistory(
#             target=target,
#             status="completed",
#             ports=result_dic.get("ports", {}),
#             scan_time=end_time,
#             scan_duration=scan_duration
#         )

#         db.add(scan_history)
#         db.commit()

#         return templates.TemplateResponse("scan_result.html", {
#             "request": request,
#             "target": target,
#             "result": result_dic,
#             "duration": scan_duration,
#             "success": True
#         })

#     except Exception as e:
#         logger.error(f"Form scan error: {e}")
#         return templates.TemplateResponse("scan_result.html", {
#             "request": request,
#             "target": target,
#             "error": str(e),
#             "success": False
#         })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=int(os.gotenv("PORT", 8000)),
        reload=True
    )
