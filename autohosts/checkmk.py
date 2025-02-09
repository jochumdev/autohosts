import logging

import requests
from urllib3.exceptions import InsecureRequestWarning

logger = logging.getLogger(__name__)

# Suppress only the single warning from urllib3 needed.
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

class CheckmkException(Exception):
    pass

class CheckmkFolderAlreadyExists(CheckmkException):
    pass

class CheckmkAPI:
    def __init__(self, server: str, site: str, username: str, password: str):
        self.base_url = f"http://{server}/{site}/check_mk"
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.session.verify = False  # Disable SSL verification - use with caution
        self.headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }
        self.auth = (username, password)

    def has_folder(self, folder_path: str) -> bool:
        url = f"{self.base_url}/api/1.0/objects/folder_config/{folder_path}"

        response = self.session.get(
            url,
            auth=self.auth,
            headers=self.headers
        )

        return response.status_code == 200

    def create_folder_recursive(self, folder_path: str) -> bool:
        """Create folders in CheckMK recursively."""
        folders = folder_path.split('~')
        current_folder = ''
        
        for folder in folders[1:]:
            current_folder = f"{current_folder}~{folder}"
            return self.create_folder(current_folder)
            
    def create_folder(self, folder_path: str) -> bool:
        """Create a new folder in CheckMK."""
        if self.has_folder(folder_path):
            logger.debug(f"Folder {folder_path} already exists")
            return False

        url = f"{self.base_url}/api/1.0/domain-types/folder_config/collections/all"
        
        payload = {
            "name": folder_path.split('~')[-1],  # Get the last part of the path as name
            "title": folder_path.split('~')[-1],
            "parent": '~'.join(folder_path.split('~')[:-1]) or '~',
            "attributes": {}
        }

        logger.info(f"Creating folder {folder_path}")
        
        response = self.session.post(
            url,
            auth=self.auth,
            headers=self.headers,
            json=payload
        )
        
        if response.status_code == 400 and "already exists" in response.text:
            return False
        
        if response.status_code not in (200, 201):
            raise CheckmkException(f"Failed to create folder: {response.text}")
        
        return True

    def has_host(self, hostname: str) -> bool:
        """Check if a host exists in CheckMK."""
        url = f"{self.base_url}/api/1.0/objects/host_config/{hostname}"
        
        response = self.session.get(
            url,
            auth=self.auth,
            headers=self.headers
        )
        
        return response.status_code == 200

    def create_host(self, hostname: str, ip_address: str, folder: str = "~") -> bool:
        """Create a new host in CheckMK."""
        logger.info(f"Creating host {hostname} with IP {ip_address} in folder {folder}")

        url = f"{self.base_url}/api/1.0/domain-types/host_config/collections/all"
        
        payload = {
            "folder": folder,
            "host_name": hostname,
            "attributes": {
                "ipaddress": ip_address,
            }
        }
        
        response = self.session.post(
            url,
            auth=self.auth,
            headers=self.headers,
            json=payload
        )
        
        if response.status_code not in (200, 201):
            raise CheckmkException(f"Failed to create host: {response.text}")
        
        return True

    def discover_services(self, hostname: str) -> dict:
        """Discover services for a host."""
        url = f"{self.base_url}/api/1.0/objects/host/{hostname}/actions/discover_services/invoke"
        
        payload = {
            "mode": "new",  # Only discover new services
        }
        
        # Get current state for ETag
        response = self.session.get(
            f"{self.base_url}/api/1.0/objects/host/{hostname}",
            auth=self.auth,
            headers=self.headers
        )
        
        if response.status_code != 200:
            raise CheckmkException(f"Failed to get host state: {response.text}")
            
        etag = response.headers.get('ETag')
        if not etag:
            raise CheckmkException("No ETag found in response")
            
        # Now discover services with the ETag
        headers = self.headers.copy()
        headers['If-Match'] = etag
        
        response = self.session.post(
            url,
            auth=self.auth,
            headers=headers,
            json=payload
        )
        
        if response.status_code != 200:
            raise CheckmkException(f"Failed to discover services: {response.text}")
        
        return response.json()

    def activate_changes(self) -> None:
        """Activate pending changes."""

        # First, get the current activation state
        state_url = f"{self.base_url}/api/1.0/domain-types/activation_run/actions/activate-changes/invoke"
        
        response = self.session.get(
            state_url,
            auth=self.auth,
            headers=self.headers
        )
        
        if response.status_code != 200:
            raise CheckmkException(f"Failed to get activation state: {response.text}")
            
        etag = response.headers.get('ETag')
        if not etag:
            raise CheckmkException("No ETag found in response")
            
        # Now activate with the ETag
        url = f"{self.base_url}/api/1.0/domain-types/activation_run/actions/activate-changes/invoke"
        
        headers = self.headers.copy()
        headers['If-Match'] = etag
        
        payload = {
            "force_foreign_changes": False,
            "sites": ["cmk"]  # You might need to adjust this based on your setup
        }
        
        response = self.session.post(
            url,
            auth=self.auth,
            headers=headers,
            json=payload
        )
        
        if response.status_code != 200:
            raise CheckmkException(f"Failed to activate changes: {response.text}")