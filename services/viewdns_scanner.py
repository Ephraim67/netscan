import requests
import logging
from typing import Optional, Dict, Any
from config import VIEWDNS_API_KEY

logger = logging.getLogger(__name__)

class NetScanner:
    BASE_URL = "https://api.viewdns.info/portscan/"
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or VIEWDNS_API_KEY
        if not self.api_key:
            raise ValueError("API key must be provided for ViewDNS scanning.")
        
    def scan_host(self, host: str) -> Dict[str, Any]:
        """Scan a single host using viewdns.info API."""
        if not host or not host.strip():
            return {
                "status": "error",
                "error": "Host cannot be empty",
                "ip": host,
                "ports": []
            }
            
        params = {
            "host": host.strip(),
            "apikey": self.api_key,
            "output": "json"
        }
        
        try:
            logger.info(f"Scanning host: {host}")
            response = requests.get(
                self.BASE_URL, 
                params=params, 
                timeout=30,
                headers={'User-Agent': 'PortScanner/1.0'}
            )
            response.raise_for_status()
            
            try:
                data = response.json()
            except ValueError as e:
                logger.error(f"Invalid JSON response for {host}: {e}")
                return {
                    "status": "error",
                    "error": "Invalid JSON response from API",
                    "ip": host,
                    "ports": []
                }

            logger.debug(f"ViewDNS Response for {host}: {data}")
            
            # Handle different response structures
            if "response" not in data:
                return {
                    "status": "error",
                    "error": f"Unexpected API response structure: {data}",
                    "ip": host,
                    "ports": []
                }
            
            response_data = data["response"]
            
            # Check for API errors
            if "error" in response_data:
                return {
                    "status": "error",
                    "error": response_data["error"],
                    "ip": host,
                    "ports": []
                }
            
            # Handle case where no ports are returned
            if "port" not in response_data or response_data["port"] is None:
                message = response_data.get("message", "No port information available")
                return {
                    "status": "down",
                    "error": None,
                    "ip": host,
                    "ports": [],
                    "message": message
                }
            
            # Process port information
            ports = []
            port_list = response_data["port"]
            
            # Handle both single port and multiple ports
            if not isinstance(port_list, list):
                port_list = [port_list]
            
            for port_info in port_list:
                try:
                    port_data = {
                        "port": int(port_info.get("number", 0)),
                        "status": port_info.get("status", "unknown").lower(),
                        "banner": port_info.get("banner"),
                        "service": port_info.get("service", "Unknown")
                    }
                    
                    # Include ALL ports (even closed)
                    ports.append(port_data)
                        
                except (ValueError, TypeError) as e:
                    logger.warning(f"Error processing port data for {host}: {e}")
                    continue

            return {
                "status": "up" if ports else "down",
                "ip": host,
                "ports": ports,
                "error": None,
                "scan_time": response_data.get("scan_time"),
                "total_ports_scanned": len(port_list)
            }
        
        except requests.exceptions.Timeout:
            logger.error(f"Timeout scanning {host}")
            return {
                "status": "error",
                "error": "Request timeout - scan took too long",
                "ip": host,
                "ports": []
            }
        except requests.exceptions.ConnectionError:
            logger.error(f"Connection error scanning {host}")
            return {
                "status": "error",
                "error": "Connection error - unable to reach API",
                "ip": host,
                "ports": []
            }
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error scanning {host}: {e}")
            return {
                "status": "error",
                "error": f"HTTP error: {e.response.status_code}",
                "ip": host,
                "ports": []
            }
        except Exception as e:
            logger.error(f"Unexpected error scanning {host}: {e}")
            return {
                "status": "error",
                "error": f"Unexpected error: {str(e)}",
                "ip": host,
                "ports": []
            }
