import os
import configparser
import json
from typing import Dict, Any, List

def load_smtp_config(smtp_file: str) -> List[Dict[str, str]]:
    """Load SMTP configuration from server.txt."""
    smtp_configs = []
    try:
        with open(smtp_file, 'r') as f:
            for line in f:
                if '|' in line:
                    server, port, username, password = line.strip().split('|')
                    smtp_configs.append({
                        'host': server,
                        'port': int(port),
                        'username': username,
                        'password': password
                    })
    except Exception as e:
        print(f"[ERROR] Failed to load SMTP configuration: {str(e)}")
        raise
    return smtp_configs

def load_config():
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        raise Exception(f"Config file not found at {config_path}")
    except json.JSONDecodeError:
        raise Exception(f"Invalid JSON in config file at {config_path}")

def validate_config(config):
    required_smtp = ['host', 'port', 'username', 'password']
    required_email = ['from_name', 'from_email', 'reply_to']
    required_company = ['name', 'domain', 'support_email']

    for field in required_smtp:
        if field not in config.get('smtp', {}):
            raise ValueError(f"Missing required SMTP config field: {field}")

    for field in required_email:
        if field not in config.get('email', {}):
            raise ValueError(f"Missing required email config field: {field}")

    for field in required_company:
        if field not in config.get('company', {}):
            raise ValueError(f"Missing required company info field: {field}")

    return True

def get_proxy_url() -> str:
    """Get proxy URL from configuration."""
    try:
        base_url = PROXY_CONFIG['base_url']
        session_id = PROXY_CONFIG['session_id_prefix']
        username = PROXY_CONFIG['username']
        return f"{base_url}/{session_id}/{username}"
    except Exception as e:
        print(f"[ERROR] Failed to get proxy URL: {str(e)}")
        return ""

# Load configuration
CONFIG = load_config()
validate_config(CONFIG)

# Proxy Configuration
PROXY_CONFIG = CONFIG.get('proxy', {
    'enabled': False,
    'rotation_interval': 300,
    'test_url': 'http://httpbin.org/ip',
    'timeout': 10
})

# SMTP Configuration
SMTP_CONFIGS = CONFIG['smtp']

# Email Configuration
EMAIL_CONFIG = CONFIG['email']

# AI Template Configuration
TEMPLATE_CONFIG = CONFIG.get('template', {
    'cohere_api_key': 'your-cohere-api-key',
    'max_retries': 3,
    'retry_delay': 5,
    'timeout': 30,
    'template_dir': os.path.join(os.path.dirname(__file__), 'templates')
})

# Company Information
COMPANY_INFO = CONFIG['company']

# Email Authentication
AUTH_CONFIG = {
    'spf_record': CONFIG.get('spf_record', ''),
    'dkim_selector': CONFIG.get('dkim_selector', 'default'),
    'dkim_private_key': CONFIG.get('dkim_private_key', '')
}

# Performance settings
PERFORMANCE_CONFIG = {
    'rotation_threshold': int(CONFIG.get('performance', {}).get('rotation_threshold', '1000')),
    'min_open_rate': float(CONFIG.get('performance', {}).get('min_open_rate', '0.2')),
    'min_click_through_rate': float(CONFIG.get('performance', {}).get('min_click_through_rate', '0.1'))
}

def get_proxy_url(session_id: str) -> str:
    """Generate proxy URL for a given session."""
    return f"{PROXY_CONFIG['base_url']}/{PROXY_CONFIG['session_prefix']}{session_id}" 