import time
from typing import Dict, Optional
import requests
from .config import PROXY_CONFIG

class ProxyManager:
    def __init__(self):
        self.proxy_base_url = PROXY_CONFIG['proxy_base_url']
        self.session_prefix = PROXY_CONFIG['proxy_session_prefix']
        self.username = PROXY_CONFIG['proxy_username']
        self.current_proxy: Optional[Dict[str, str]] = None
        self.rotation_interval = 300  # 5 minutes
        self.last_rotation = 0
        self._stop_rotation = False
        
    def start_rotation(self, interval: int = None):
        """Start proxy rotation with specified interval."""
        if interval:
            self.rotation_interval = interval
        self._stop_rotation = False
        
    def stop_rotation(self):
        """Stop proxy rotation."""
        self._stop_rotation = True
        
    def get_current_proxy(self) -> Dict[str, str]:
        """Get current proxy configuration."""
        current_time = time.time()
        if not self.current_proxy or (current_time - self.last_rotation) >= self.rotation_interval:
            self._rotate_proxy()
        return self.current_proxy
        
    def _rotate_proxy(self):
        """Rotate to a new proxy."""
        try:
            session_id = f"{self.session_prefix}_{int(time.time())}"
            proxy_url = f"{self.proxy_base_url}/{session_id}"
            
            self.current_proxy = {
                'http': f'http://{self.username}:{session_id}@{proxy_url}',
                'https': f'http://{self.username}:{session_id}@{proxy_url}'
            }
            self.last_rotation = time.time()
            
        except Exception as e:
            print(f"[ERROR] Failed to rotate proxy: {str(e)}")
            self.current_proxy = None 