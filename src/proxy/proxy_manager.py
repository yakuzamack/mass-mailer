import os
import time
import threading
import requests
from typing import Dict, Any, Optional
from src.config import PROXY_CONFIG

class ProxyManager:
    def __init__(self, config=None):
        self.config = config or {}
        self.proxy_config = self.config.get('proxy', PROXY_CONFIG)
        self.current_proxy = None
        self.rotation_thread = None
        self.should_stop_rotation = False
        
    def start_rotation(self):
        """Start proxy rotation in a separate thread."""
        if not self.proxy_config['enabled']:
            print("Proxy rotation is disabled")
            return
            
        if self.rotation_thread and self.rotation_thread.is_alive():
            print("Proxy rotation is already running")
            return
            
        self.should_stop_rotation = False
        self.rotation_thread = threading.Thread(target=self._rotation_loop)
        self.rotation_thread.daemon = True
        self.rotation_thread.start()
        
    def stop_rotation_thread(self):
        """Stop proxy rotation."""
        self.should_stop_rotation = True
        if self.rotation_thread:
            self.rotation_thread.join()
            
    def _rotation_loop(self):
        """Main proxy rotation loop."""
        while not self.should_stop_rotation:
            try:
                self.rotate_proxy()
                time.sleep(self.proxy_config['rotation_interval'])
            except Exception as e:
                print(f"Error in proxy rotation: {str(e)}")
                time.sleep(60)  # Wait before retrying
                
    def rotate_proxy(self):
        """Rotate to a new proxy."""
        try:
            # Get new proxy URL (implementation depends on your proxy provider's API)
            new_proxy_url = self._get_new_proxy()
            
            # Test the proxy
            if self._test_proxy(new_proxy_url):
                self.current_proxy = {
                    'http': new_proxy_url,
                    'https': new_proxy_url
                }
                print(f"Successfully rotated to new proxy: {new_proxy_url}")
            else:
                print(f"Failed to validate new proxy: {new_proxy_url}")
                
        except Exception as e:
            print(f"Error rotating proxy: {str(e)}")
            
    def _get_new_proxy(self) -> str:
        """Get a new proxy URL from the provider."""
        # This is a placeholder - implement according to your proxy provider's API
        return "http://proxy.example.com:8080"
        
    def _test_proxy(self, proxy_url: str) -> bool:
        """Test if a proxy is working."""
        try:
            response = requests.get(
                self.proxy_config['test_url'],
                proxies={'http': proxy_url, 'https': proxy_url},
                timeout=self.proxy_config['timeout']
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Proxy test failed: {str(e)}")
            return False
            
    def get_current_proxy(self) -> Optional[Dict[str, str]]:
        """Get the current proxy configuration."""
        return self.current_proxy if self.proxy_config['enabled'] else None 