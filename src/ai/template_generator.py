import os
import cohere
import time
from typing import Dict, Any, Optional
from datetime import datetime
from src.config import TEMPLATE_CONFIG

class TemplateGenerator:
    def __init__(self, config=None):
        self.config = config or {}
        self.template_config = self.config.get('template', TEMPLATE_CONFIG)
        self.client = cohere.Client(self.template_config.get('cohere_api_key', 'your-cohere-api-key'))
        self.max_wait_time = 30  # Maximum time to wait for template generation in seconds
        self.wait_interval = 2   # Time between checks in seconds
        
    def generate_template(self, company_info: Dict[str, str], performance_metrics: Optional[Dict[str, float]] = None) -> Dict[str, str]:
        """Generate an email template for the given company info and performance metrics."""
        try:
            # Generate template content using Cohere
            prompt = self._construct_prompt(company_info, performance_metrics)
            response = self._generate_with_retry(prompt)
            
            # Parse and validate the generated content
            template = self._parse_generated_content(response)
            
            # Validate the template
            if not self._validate_template(template):
                print("[WARNING] Generated template validation failed, using fallback template")
                return self._get_fallback_template({'name': company_info['name']})
            
            return template
            
        except Exception as e:
            print(f"Error generating template: {str(e)}")
            return self._get_fallback_template({'name': company_info['name']})
            
    def _create_prompt(self, recipient: Dict[str, Any]) -> str:
        """Create a prompt for template generation."""
        return f"""Generate a professional email template for:
        Name: {recipient['name']}
        Company: {recipient.get('company', 'Unknown')}
        Role: {recipient.get('role', 'Unknown')}
        
        The email should include:
        1. A subject line
        2. A personalized greeting
        3. A clear and concise main body
        4. A call to action
        5. A professional closing
        
        Format the response as follows:
        Subject: [subject line]
        Greeting: [greeting]
        Body: [main body]
        CTA: [call to action]
        Closing: [closing]
        """
        
    def _generate_with_retry(self, prompt: str, max_retries: int = 3) -> str:
        """Generate content with retry logic."""
        try:
            # For testing, return a mock response if using test key
            if self.template_config['cohere_api_key'] in ['test-key', 'test_key', 'your-cohere-api-key']:
                return """Subject: Important Update: Your Account Review Required
                Greeting: Dear Test User,
                Body: I hope this email finds you well. We have noticed some recent activity on your account that requires your attention. To ensure the security of your account and maintain uninterrupted service, please review your account settings.
                CTA: Review Account Settings
                Closing: Thank you for your prompt attention to this matter."""
                
            # Otherwise, try to generate with Cohere
            for attempt in range(max_retries):
                try:
                    response = self.client.generate(
                        prompt=prompt,
                        max_tokens=300,
                        temperature=0.7,
                        k=0,
                        stop_sequences=["---"],
                        return_likelihoods="NONE"
                    )
                    return response.generations[0].text
                    
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise e
                    time.sleep(2 ** attempt)  # Exponential backoff
                    
        except Exception as e:
            print(f"Error generating content: {str(e)}")
            raise
        
    def _parse_generated_content(self, content: str) -> Dict[str, str]:
        """Parse the generated content into template components."""
        lines = content.strip().split('\n')
        template = {}
        
        current_key = None
        current_value = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if line.startswith(('Subject:', 'Greeting:', 'Body:', 'CTA:', 'Closing:')):
                if current_key and current_value:
                    template[current_key] = ' '.join(current_value)
                current_key = line.split(':')[0].lower()
                current_value = [line.split(':', 1)[1].strip()]
            else:
                if current_key:
                    current_value.append(line)
                    
        if current_key and current_value:
            template[current_key] = ' '.join(current_value)
            
        # Map to expected keys
        return {
            'subject_line': template.get('subject', ''),
            'greeting': template.get('greeting', ''),
            'main_body': template.get('body', ''),
            'cta': template.get('cta', ''),
            'closing': template.get('closing', '')
        }
        
    def _get_fallback_template(self, recipient: Dict[str, Any]) -> Dict[str, str]:
        """Get a fallback template if generation fails."""
        return {
            'subject_line': 'Important Information for Your Attention',
            'greeting': f"Dear {recipient['name']},",
            'main_body': 'I hope this email finds you well. I am reaching out regarding an important matter that requires your attention.',
            'cta': 'Please review and respond at your earliest convenience.',
            'closing': 'Thank you for your time and consideration.'
        }
            
    def _construct_prompt(self, company_info: Dict[str, str], metrics: Dict[str, Any] = None) -> str:
        """Construct prompt for template generation."""
        return f"""Generate a professional email template for {company_info['name']}.
        The email should be about domain privacy auto-renewal failure.
        Include the following components:
        - A clear subject line about domain privacy auto-renewal failure
        - A professional greeting using {{name}} variable
        - A main body explaining the situation and urgency
        - A clear call-to-action button text
        - A professional closing
        
        Use these variables in the template:
        - {{companyName}} for the company name
        - {{companyWebsite}} for the website
        - {{companySupportEmail}} for support email
        - {{companyLogoUrl}} for logo URL
        - {{name}} for recipient name
        - {{email_host}} for recipient's domain
        
        The tone should be professional and urgent but not alarmist.
        """
        
    def _validate_template(self, template: Dict[str, str]) -> bool:
        """Validate template components."""
        required_components = ['subject_line', 'greeting', 'main_body', 'cta', 'closing']
        
        # Check all required components exist
        for component in required_components:
            if component not in template:
                print(f"[ERROR] Missing template component: {component}")
                return False
                
            if not template[component].strip():
                print(f"[ERROR] Empty template component: {component}")
                return False
                
            # Check for required variables
            if component == 'greeting' and '{name}' not in template[component]:
                print("[ERROR] Greeting must include {name} variable")
                return False
                
        return True
    
    def generate_backup_template(self, 
                               company_info: Dict[str, str],
                               performance_metrics: Optional[Dict[str, float]] = None) -> Dict[str, str]:
        """Generate a backup template with slightly different parameters."""
        # Modify temperature for variation
        response = self.client.generate(
            prompt=self._construct_prompt(company_info, performance_metrics),
            max_tokens=1000,
            temperature=0.8,  # Slightly higher temperature for more variation
            k=0,
            stop_sequences=[],
            return_likelihoods='NONE'
        )
        
        return self._parse_generated_content(response.generations[0].text) 