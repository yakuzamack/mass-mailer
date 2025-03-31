import os
import configparser
from typing import Dict, Any

def load_config(config_path: str = 'dummy.config') -> Dict[str, Any]:
    """Load configuration from the specified file."""
    config = configparser.ConfigParser()
    config.read(config_path)
    
    if 'madcatmailer' not in config:
        raise ValueError(f"Invalid config file: {config_path}")
        
    return dict(config['madcatmailer'])

# Load configuration
CONFIG = load_config()

# Proxy Configuration
PROXY_CONFIG = {
    'base_url': CONFIG.get('proxy_base_url', 'http://proxy.toolip.io:31114'),
    'session_id_prefix': CONFIG.get('proxy_session_prefix', 'tl-68c57bf261954ad1a04f8eec66f5ebc882ef9d19dbe383047345ed2abf882b9c'),
    'username': CONFIG.get('proxy_username', 'lbmx41ijbgm6'),
    'rotation_interval': int(CONFIG.get('proxy_rotation_interval', '60'))
}

# SMTP Configuration
SMTP_CONFIG = {
    'host': CONFIG.get('smtp_host', 'smtp.gmail.com'),
    'port': int(CONFIG.get('smtp_port', '587')),
    'username': CONFIG.get('smtp_username'),
    'password': CONFIG.get('smtp_password'),
    'use_tls': CONFIG.get('smtp_use_tls', 'true').lower() == 'true',
    'timeout': int(CONFIG.get('smtp_timeout', '10'))
}

# Email Configuration
EMAIL_CONFIG = {
    'default_from': CONFIG.get('mail_from', 'noreply@example.com'),
    'max_retries': int(CONFIG.get('max_retries', '3')),
    'retry_delay': int(CONFIG.get('retry_delay', '5')),
    'add_read_receipts': CONFIG.get('add_read_receipts', 'false').lower() == 'true'
}

# AI Template Configuration
TEMPLATE_CONFIG = {
    'cohere_api_key': CONFIG.get('cohere_api_key'),
    'max_retries': int(CONFIG.get('template_max_retries', '3')),
    'retry_delay': int(CONFIG.get('template_retry_delay', '2')),
    'rotation_threshold': int(CONFIG.get('template_rotation_threshold', '50'))
}

# Company Information
COMPANY_INFO = {
    'name': CONFIG.get('company_name', 'Company'),
    'industry': CONFIG.get('company_industry', 'Technology')
}

# Email Authentication
AUTH_CONFIG = {
    'spf_record': CONFIG.get('spf_record'),
    'dkim_selector': CONFIG.get('dkim_selector', 'default'),
    'dkim_private_key': CONFIG.get('dkim_private_key')
}

def get_proxy_url(session_id: str) -> Dict[str, str]:
    """Generate proxy URLs with the given session ID."""
    proxy_url = f"{PROXY_CONFIG['base_url']}/{PROXY_CONFIG['session_id_prefix']}-country-XX-session-{session_id}:{PROXY_CONFIG['username']}"
    return {
        'http': proxy_url,
        'https': proxy_url
    }

def validate_config() -> bool:
    """Validate the configuration settings."""
    required_settings = [
        'smtp_username',
        'smtp_password',
        'cohere_api_key'
    ]
    
    missing_settings = [setting for setting in required_settings if not CONFIG.get(setting)]
    
    if missing_settings:
        print(f"Missing required settings: {', '.join(missing_settings)}")
        return False
        
    return True 