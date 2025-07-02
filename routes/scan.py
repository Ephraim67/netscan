from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from services.viewdns_scanner import NetScanner
from schemas.scan import ScanRequest, ScanResult
from models.database import get_db, ScanTarget, ScanHistory  # Import your DB models
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter()

def get_scanner() -> NetScanner:
    """Dependency injection for NetScanner."""
    return NetScanner()

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
    db: Session = Depends(get_db)  # Add database dependency
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

# Add these additional endpoints to interact with your database

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
                "created_at": t.created_at,
                "updated_at": t.updated_at,
                "result": json.loads(t.result) if t.result else None
            }
            for t in targets
        ]
    }

@router.get("/scans/target/{target_id}")
async def get_scan_target(target_id: int, db: Session = Depends(get_db)):
    """Get a specific scan target by ID."""
    target = db.query(ScanTarget).filter(ScanTarget.id == target_id).first()
    
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")
    
    return {
        "id": target.id,
        "target": target.target,
        "status": target.status,
        "created_at": target.created_at,
        "updated_at": target.updated_at,
        "result": json.loads(target.result) if target.result else None
    }