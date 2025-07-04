from fastapi import APIRouter, HTTPException, Depends, Body
from sqlalchemy.orm import Session
from services.viewdns_scanner import NetScanner
from schemas.scan import ScanRequest, ScanResult
from models.database import get_db, ScanTarget, ScanHistory, SessionLocal  # Import your DB models and SessionLocal
import logging
import json
from typing import List
from pydantic import BaseModel
from datetime import datetime
# from fastapi import BackgroundTasks
from scheduller import start_scheduler

logger = logging.getLogger(__name__)

router = APIRouter()

class ScheduleRequest(BaseModel):
    targets: List[str]

def get_scanner() -> NetScanner:
    """Dependency injection for NetScanner."""
    return NetScanner()

def parse_json(result_str):
    if not result_str:
        return None
    try:
        return json.loads(result_str)
    except json.JSONDecodeError:
        return None

@router.get("/scans/health")
async def scanner_health():
    """Scanner service health check."""
    return {
        "status": "healthy",
        "service": "scanner",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

@router.post("/scans/single", response_model=ScanResult)
async def scan_single(
    request: ScanRequest,
    scanner: NetScanner = Depends(get_scanner),
    db: Session = Depends(get_db) 
):
    """Perform a single port scan."""
    start_time = datetime.utcnow()
    
    try:
        # Check if target already exists in scan_targets
        existing_target = db.query(ScanTarget).filter(ScanTarget.target == request.target).first()
        
        if not existing_target:
            # Create new scan target
            scan_target = ScanTarget(
                target=request.target,
                status="scanning"
            )
            db.add(scan_target)
            db.commit()
            db.refresh(scan_target)
        else:
            # Update existing target status
            existing_target.status = "scanning"
            existing_target.updated_at = datetime.utcnow()
            db.commit()
            scan_target = existing_target

        # Perform the scan
        result_dict = scanner.scan_host(request.target)
        scan_result = ScanResult(**result_dict)
        
        # Calculate scan duration
        end_time = datetime.utcnow()
        scan_duration = int((end_time - start_time).total_seconds())
        
        # Update scan target with results
        scan_target.status = "completed"
        scan_target.result = json.dumps(result_dict)
        scan_target.updated_at = end_time
        
        # Create scan history record
        scan_history = ScanHistory(
            target=request.target,
            status="completed",
            ports=result_dict.get("ports", {}),  # Adjust based on your result structure
            scan_time=end_time,
            scan_duration=scan_duration
        )
        
        db.add(scan_history)
        db.commit()
        
        return scan_result

    except Exception as e:
        # Update target status to failed if it exists
        if 'scan_target' in locals():
            scan_target.status = "failed"
            scan_target.updated_at = datetime.utcnow()
            
            # Create failed scan history record
            end_time = datetime.utcnow()
            scan_duration = int((end_time - start_time).total_seconds())
            
            scan_history = ScanHistory(
                target=request.target,
                status="failed",
                ports={},
                error_message=str(e),
                scan_time=end_time,
                scan_duration=scan_duration
            )
            
            db.add(scan_history)
            db.commit()
        
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error during scan operation"
        )



@router.get("/scans/history")
async def get_scan_history(
    limit: int = 10,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Get scan history with pagination."""
    history = db.query(ScanHistory)\
                .order_by(ScanHistory.scan_time.desc())\
                .offset(offset)\
                .limit(limit)\
                .all()
    
    return {
        "history": [
            {
                "id": h.id,
                "target": h.target,
                "status": h.status,
                "ports": h.ports,
                "error_message": h.error_message,
                "scan_time": h.scan_time,
                "scan_duration": h.scan_duration
            }
            for h in history
        ],
        "total": db.query(ScanHistory).count()
    }

@router.get("/scans/targets")
async def get_scan_targets(db: Session = Depends(get_db)):
    """Get all scan targets."""
    targets = db.query(ScanTarget).all()
    
    return {
        "targets": [
            {
                "id": t.id,
                "target": t.target,
                "status": t.status,
                "created_at": t.created_at.isoformat() if t.created_at else None,
                "updated_at": t.updated_at.isoformat() if t.updated_at else None,
                # "result": json.loads(t.result) if t.result else None
                "result": parse_json(t.result)
            }
            for t in targets
        ]
    }

# @router.post("/scans/schedule-once")
# async def schedule_scan_once(
#     background_tasks: BackgroundTasks,
#     scanner: NetScanner = Depends(get_scanner),
#     db: Session = Depends(get_db)
# ):
#     """Trigger background scan for all saved targets."""

#     def run_scan():
#         session = SessionLocal()
#         try:
#             targets = session.query(ScanTarget).all()
#             for target in targets:
#                 try:
#                     result = scanner.scan_host(target.target)

#                     history = ScanHistory(
#                         target=target.target,
#                         status=result.get("status", "completed"),
#                         ports=result.get("ports", []),
#                         error_message=result.get("error"),
#                         scan_time=datetime.utcnow()
#                     )

#                     session.add(history)

#                     target.status = result.get("status", "completed")
#                     target.result = json.dumps(result)
#                     target.updated_at = datetime.utcnow()

#                     session.commit()

#                 except Exception as e:
#                     logger.error(f"Error scanning {target.target}: {e}")

#                     history = ScanHistory(
#                         target=target.target,
#                         status="failed",
#                         ports=[],
#                         error_message=str(e),
#                         scan_time=datetime.utcnow()
#                     )

#                     session.add(history)
#                     session.commit()

#         finally:
#             session.close()

#     background_tasks.add_task(run_scan)
#     return {"message": "Scan scheduled for all saved targets."}


@router.post("/scans/schedule-once")
async def schedule_scan_once(payload: ScheduleRequest):
    start_scheduler(selected_targets=payload.targets)
    return {
        "message": f"Scheduler started. Scans will run every 10 minutes for {len(payload.targets)} targets."
    }