import os
from typing import Dict, Any, Optional
from datetime import datetime
import random
import string
from src.config import TEMPLATE_CONFIG, COMPANY_INFO

class TemplateRenderer:
    def __init__(self, config=None):
        self.config = config or {}
        self.template_config = self.config.get('template', TEMPLATE_CONFIG)
        self.company_info = config.get('company', COMPANY_INFO) if config else COMPANY_INFO
        
    def _generate_random_string(self, length: int = 32) -> str:
        """Generate a random string for tracking pixels and other unique identifiers."""
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))
        
    def render_email(self, template: Dict[str, str], recipient: Dict[str, Any], company_info: Dict[str, Any] = None) -> Dict[str, str]:
        """Render email content from template."""
        try:
            # Update company info if provided
            if company_info:
                self.company_info = company_info
            
            # Load HTML template
            html_content = self._load_html_template(template, recipient)
            
            # Create plain text version
            text_content = self._create_plain_text(template, recipient)
            
            # Validate content
            self._validate_content(html_content, text_content)
            
            return {
                'subject': template['subject_line'],
                'html': html_content,
                'plain_text': text_content
            }
            
        except Exception as e:
            print(f"Error rendering email: {str(e)}")
            raise
            
    def _load_html_template(self, template: Dict[str, str], recipient: Dict[str, Any]) -> str:
        """Load and populate HTML template."""
        try:
            # Read template file
            template_path = os.path.join(os.path.dirname(__file__), 'template.html')
            with open(template_path, 'r') as f:
                html_template = f.read()
                
            # Create replacements dictionary
            replacements = {
                '{{subject_line}}': template['subject_line'],
                '{{greeting}}': template['greeting'],
                '{{main_body}}': template['main_body'],
                '{{cta}}': template['cta'],
                '{{closing}}': template['closing'],
                '{{recipient_name}}': recipient['name'],
                '{{company_name}}': self.company_info['name'],
                '{{company_domain}}': self.company_info['domain'],
                '{{support_email}}': self.company_info['support_email'],
                '{{tracking_pixel}}': f"https://{self.company_info['domain']}/track/{self._generate_random_string(32)}.png"
            }
            
            # Apply replacements
            for key, value in replacements.items():
                html_template = html_template.replace(key, value)
                
            # Check for any remaining unreplaced variables
            if '{{' in html_template and '}}' in html_template:
                print("Warning: Some template variables were not replaced")
                
            return html_template
            
        except Exception as e:
            print(f"Error loading HTML template: {str(e)}")
            raise
            
    def _create_plain_text(self, template: Dict[str, str], recipient: Dict[str, Any]) -> str:
        """Create plain text version of the email."""
        try:
            text_content = f"""
{template['subject_line']}

{template['greeting']}

{template['main_body']}

{template['cta']}

{template['closing']}

Best regards,
{self.company_info['name']}
{self.company_info['domain']}

For support: {self.company_info['support_email']}
            """
            return text_content.strip()
            
        except Exception as e:
            print(f"Error creating plain text content: {str(e)}")
            raise
            
    def _validate_content(self, html_content: str, text_content: str) -> None:
        """Validate email content."""
        if not html_content or len(html_content) < 50:
            raise ValueError("HTML content is too short or empty")
            
        if not text_content or len(text_content) < 50:
            raise ValueError("Text content is too short or empty")
            
        # Check for any remaining template variables
        if '{{' in html_content and '}}' in html_content:
            raise ValueError("Some template variables were not replaced in HTML content") 