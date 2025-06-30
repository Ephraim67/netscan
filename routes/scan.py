from fastapi import APIRouter, HTTPException, Depends
from services.viewdns_scanner import NetScanner
from schemas.scan import ScanRequest, ScanResult
import logging

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
        "timestamp": "2025-06-30T00:00:00Z"
    }

@router.post("/scans/single", response_model=ScanResult)
async def scan_single(
    request: ScanRequest,
    scanner: NetScanner = Depends(get_scanner)
):
    """Perform a single port scan."""
    try:
        result_dict = scanner.scan_host(request.target)
        scan_result = ScanResult(**result_dict)
        return scan_result

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error during scan operation"
        )
