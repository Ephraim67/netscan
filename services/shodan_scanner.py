import requests
import shodan
from config import SHODAN_API_KEY
import logging

logger = logging.getLogger(__name__)

class ShodanScanner:
    BASE_URL = ""