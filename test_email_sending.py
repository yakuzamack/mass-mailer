import os
import sys
import json
from src.ai.email_orchestrator import EmailOrchestrator
from src.config import CONFIG

def setup_test_config():
    # Create a copy of the config
    test_config = {
        'smtp': [{
            'host': 'smtp.diamantextanques.com.br',
            'port': 587,
            'username': 'engenharia@diamantextanques.com.br',
            'password': 'mUy#3g0!tOAD',
            'use_tls': True,
            'timeout': 30
        }],
        'email': {
            'from_name': 'Engenharia',
            'from_email': 'engenharia@diamantextanques.com.br',
            'reply_to': 'engenharia@diamantextanques.com.br',
            'max_retries': 3,
            'retry_delay': 5
        },
        'template': {
            'cohere_api_key': os.getenv('COHERE_API_KEY', 'test-key'),
            'max_retries': 3,
            'retry_delay': 5,
            'timeout': 30,
            'template_dir': os.path.join(os.path.dirname(__file__), 'test_templates')
        },
        'company': {
            'name': 'Diamante Tanques',
            'domain': 'diamantextanques.com.br',
            'support_email': 'engenharia@diamantextanques.com.br'
        },
        'proxy': {
            'enabled': False,
            'rotation_interval': 300,
            'test_url': 'http://httpbin.org/ip',
            'timeout': 10
        },
        'auth': {
            'spf_record': '',
            'dkim_selector': 'default',
            'dkim_private_key': ''
        }
    }
    
    # Create test templates directory if it doesn't exist
    os.makedirs(test_config['template']['template_dir'], exist_ok=True)
    
    return test_config

def test_email_sending():
    # Setup test configuration
    test_config = setup_test_config()
    
    # Initialize orchestrator with test config
    orchestrator = EmailOrchestrator(config=test_config)
    
    # Initialize the orchestrator with company info
    orchestrator.initialize()
    
    # Test recipient
    test_recipient = {
        'email': 'xyakuzapro@gmail.com',
        'name': 'Engenharia',
        'company': 'Diamante Tanques',
        'role': 'Engineering'
    }
    
    try:
        # Generate and send test email
        success_count = 0
        failure_count = 0
        
        result = orchestrator.send_email(test_recipient)
        
        if result:
            success_count += 1
            print(f"Successfully sent test email to {test_recipient['email']}")
        else:
            failure_count += 1
            print(f"Failed to send test email to {test_recipient['email']}")
            
        # Print results
        print("\nTest Results:")
        print(f"Successful sends: {success_count}")
        print(f"Failed sends: {failure_count}")
        
    except Exception as e:
        print(f"Error during test: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    test_email_sending() 