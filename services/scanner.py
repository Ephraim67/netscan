import logging
from typing import Dict, List, Optional
from nmap import PortScanner, PortScannerError
import ipaddress


class NetScanner:
    """
    A class to handle Netscan scanning operations with error handling and logging.
    """
    
    def __init__(self, timeout: int = 30):
        
        self.timeout = timeout
        self.logger = logging.getLogger(__name__)
        
    def _validate_target(self, target: str) -> bool:
        
        try:
            # Try to parse as IP address
            ipaddress.ip_address(target)
            return True
        except ValueError:
            # If not IP, assume it's a hostname (basic validation)
            if target and len(target.strip()) > 0:
                return True
            return False
    
    def run_scan(self, target: str, arguments: str = '-T4') -> Dict:
        
        # Validate input
        if not target or not isinstance(target, str):
            self.logger.error("Invalid target provided")
            return self._create_error_result(target, "Invalid target")
        
        target = target.strip()
        
        if not self._validate_target(target):
            self.logger.error(f"Invalid target format: {target}")
            return self._create_error_result(target, "Invalid target format")
        
        try:
            # Initialize scanner
            scanner = PortScanner()
            self.logger.info(f"Starting scan for target: {target}")
            
            # Perform the scan
            scanner.scan(hosts=target, arguments=arguments)
            
            # Check if target is reachable
            if target not in scanner.all_hosts():
                self.logger.warning(f"Target {target} appears to be down or unreachable")
                return {
                    "status": "down",
                    "ip": target,
                    "open_ports": [],
                    "error": None
                }
            
            # Extract open ports information
            open_ports = self._extract_port_info(scanner, target)
            
            result = {
                "status": "up",
                "ip": target,
                "open_ports": open_ports,
                "error": None
            }
            
            self.logger.info(f"Scan completed for {target}. Found {len(open_ports)} open ports")
            return result
            
        except PortScannerError as e:
            error_msg = f"Netscan scanner error: {str(e)}"
            self.logger.error(error_msg)
            return self._create_error_result(target, error_msg)
            
        except FileNotFoundError as e:
            error_msg = "Netscan not found. Please ensure netscan is installed and in PATH"
            self.logger.error(error_msg)
            return self._create_error_result(target, error_msg)
            
        except PermissionError as e:
            error_msg = f"Permission denied: {str(e)}. Some scans may require elevated privileges"
            self.logger.error(error_msg)
            return self._create_error_result(target, error_msg)
            
        except Exception as e:
            error_msg = f"Unexpected error during scan: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return self._create_error_result(target, error_msg)
    
    def _extract_port_info(self, scanner: PortScanner, target: str) -> List[Dict]:
        
        open_ports = []
        
        try:
            for proto in scanner[target].all_protocols():
                ports = scanner[target][proto].keys()
                for port in ports:
                    port_info = scanner[target][proto][port]
                    open_ports.append({
                        "port": port,
                        "protocol": proto,
                        "state": port_info.get('state', 'unknown'),
                        "service": port_info.get('name', 'unknown'),
                        "version": port_info.get('version', ''),
                        "product": port_info.get('product', '')
                    })
        except KeyError as e:
            self.logger.warning(f"Error extracting port info for {target}: {str(e)}")
        
        return open_ports
    
    def _create_error_result(self, target: str, error_message: str) -> Dict:
        
        return {
            "status": "error",
            "ip": target or "unknown",
            "open_ports": [],
            "error": error_message
        }
    
    def scan_multiple_targets(self, targets: List[str], arguments: str = '-T4') -> List[Dict]:
       
        if not targets or not isinstance(targets, list):
            self.logger.error("Invalid targets list provided")
            return []
        
        results = []
        for target in targets:
            result = self.run_scan(target, arguments)
            results.append(result)
        
        return results


