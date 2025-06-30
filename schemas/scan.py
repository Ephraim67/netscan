from typing import List, Optional
from pydantic import BaseModel

class PortInfo(BaseModel):
    port: int
    status: str
    banner: Optional[str] = None
    service: str

class ScanResult(BaseModel):
    status: str
    ip: str
    ports: List[PortInfo]
    error: Optional[str] = None
    scan_time: Optional[str] = None
    total_ports_scanned: Optional[int] = None
    message: Optional[str] = None

class ScanRequest(BaseModel):
    target: str
