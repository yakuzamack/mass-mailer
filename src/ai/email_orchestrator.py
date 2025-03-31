import os
from typing import Dict, List, Any, Optional
from datetime import datetime
from src.ai.template_generator import TemplateGenerator
from src.ai.template_manager import TemplateManager
from src.ai.template_renderer import TemplateRenderer
from src.email_sender import EmailSender
from src.analytics import Analytics
from src.config import TEMPLATE_CONFIG, COMPANY_INFO, CONFIG

class EmailOrchestrator:
    def __init__(self, config=None):
        self.config = config or CONFIG
        self.template_generator = TemplateGenerator(self.config)
        self.template_manager = TemplateManager()
        self.template_renderer = TemplateRenderer(self.config)
        self.email_sender = EmailSender(self.config)
        self.analytics = Analytics()
        self.current_template: Optional[Dict[str, str]] = None
        
    def initialize(self, company_info: Dict[str, str] = None) -> None:
        """Initialize the email system with company information."""
        if company_info is None:
            company_info = self.config.get('company', COMPANY_INFO)
        self.template_manager.initialize_templates(company_info)
        self._ensure_template_available()
        
    def _ensure_template_available(self) -> bool:
        """Ensure a valid template is available before sending emails."""
        try:
            if not self.current_template:
                print("[INFO] No template available, generating new template...")
                self.current_template = self.template_manager.get_current_template()
                
            if not self.current_template:
                print("[INFO] Generating new template...")
                self.current_template = self.template_generator.generate_template(
                    self.config.get('company', {}),
                    None  # No performance metrics available yet
                )
                
            if not self.current_template:
                print("[ERROR] Failed to generate email template")
                return False
                
            # Validate template components
            required_components = ['subject_line', 'greeting', 'main_body', 'cta', 'closing']
            for component in required_components:
                if not self.current_template.get(component):
                    print(f"[ERROR] Missing required template component: {component}")
                    return False
                    
            # Validate content length
            for component, content in self.current_template.items():
                if len(content.strip()) < 10:  # Minimum length check
                    print(f"[ERROR] Template component {component} is too short")
                    return False
                    
            print("[INFO] Template validated successfully")
            return True
            
        except Exception as e:
            print(f"[ERROR] Template validation failed: {str(e)}")
            return False
            
    def _generate_new_template(self, company_info: Dict[str, str], performance_metrics: Optional[Dict[str, float]] = None) -> bool:
        """Generate a new template based on performance metrics."""
        try:
            print("[INFO] Generating new template based on performance metrics...")
            new_template = self.template_generator.generate_template(
                company_info,
                performance_metrics
            )
            
            if not new_template:
                print("[ERROR] Failed to generate new template")
                return False
                
            # Validate new template
            if not self._validate_template(new_template):
                print("[ERROR] New template validation failed")
                return False
                
            self.current_template = new_template
            self.template_manager._save_template(new_template, "primary")
            print("[INFO] New template generated and saved successfully")
            return True
            
        except Exception as e:
            print(f"[ERROR] Template generation failed: {str(e)}")
            return False
            
    def _validate_template(self, template: Dict[str, str]) -> bool:
        """Validate template components and content."""
        try:
            required_components = ['subject_line', 'greeting', 'main_body', 'cta', 'closing']
            
            # Check required components
            for component in required_components:
                if not template.get(component):
                    print(f"[ERROR] Missing required component: {component}")
                    return False
                    
            # Validate content length
            for component, content in template.items():
                if len(content.strip()) < 10:
                    print(f"[ERROR] Component {component} is too short")
                    return False
                    
            # Test template rendering
            test_data = {
                'name': 'Test User',
                'email': 'test@example.com',
                'company': COMPANY_INFO
            }
            
            rendered = self.template_renderer.render_email(template, test_data, COMPANY_INFO)
            if not rendered or not rendered.get('html') or not rendered.get('plain_text'):
                print("[ERROR] Template rendering test failed")
                return False
                
            return True
            
        except Exception as e:
            print(f"[ERROR] Template validation failed: {str(e)}")
            return False
        
    def send_batch(self, 
                  recipients: List[Dict[str, Any]],
                  company_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send a batch of emails using AI-generated templates.
        
        Args:
            recipients: List of recipient data dictionaries
            company_data: Dictionary containing company-specific data
            
        Returns:
            Dictionary containing batch statistics
        """
        # Ensure template is available and valid before starting
        if not self._ensure_template_available():
            return {
                'total_sent': 0,
                'successful': 0,
                'failed': 0,
                'error': 'Template generation failed'
            }
            
        batch_stats = {
            'total_sent': 0,
            'successful': 0,
            'failed': 0,
            'start_time': datetime.now().isoformat()
        }
        
        for recipient in recipients:
            try:
                # Render email with current template
                email_content = self.template_renderer.render_email(
                    self.current_template,
                    recipient,
                    company_data
                )
                
                # Validate rendered content
                if not email_content or not email_content.get('html') or not email_content.get('plain_text'):
                    print(f"[ERROR] Empty content generated for {recipient['email']}")
                    batch_stats['failed'] += 1
                    batch_stats['total_sent'] += 1
                    continue
                    
                # Validate content length
                if len(email_content['html'].strip()) < 100:
                    print(f"[ERROR] HTML content too short for {recipient['email']}")
                    batch_stats['failed'] += 1
                    batch_stats['total_sent'] += 1
                    continue
                    
                if len(email_content['plain_text'].strip()) < 50:
                    print(f"[ERROR] Plain text content too short for {recipient['email']}")
                    batch_stats['failed'] += 1
                    batch_stats['total_sent'] += 1
                    continue
                    
                # Send email
                success = self.email_sender.send_email(
                    to_email=recipient['email'],
                    subject=email_content['subject'],
                    html_content=email_content['html'],
                    plain_text_content=email_content['plain_text']
                )
                
                if success:
                    batch_stats['successful'] += 1
                else:
                    batch_stats['failed'] += 1
                    
                batch_stats['total_sent'] += 1
                
            except Exception as e:
                print(f"[ERROR] Error sending email to {recipient['email']}: {str(e)}")
                batch_stats['failed'] += 1
                batch_stats['total_sent'] += 1
                
        # Update performance metrics and check if template rotation is needed
        self._update_performance_metrics(batch_stats)
        
        return batch_stats
    
    def _update_performance_metrics(self, batch_stats: Dict[str, Any]) -> None:
        """Update performance metrics and trigger template rotation if needed."""
        # Get analytics data
        metrics = self.analytics.get_metrics(
            start_time=batch_stats['start_time'],
            end_time=datetime.now().isoformat()
        )
        
        # Update template manager with new metrics
        self.template_manager.update_performance_metrics(metrics)
        
        # Check if we need to generate a new template
        if self.template_manager.emails_sent_with_current >= self.template_manager.rotation_threshold:
            print("[INFO] Template rotation threshold reached, generating new template...")
            self._generate_new_template(COMPANY_INFO, metrics)
            
    def get_template_stats(self) -> Dict[str, Any]:
        """Get statistics about the current template performance."""
        return {
            'current_version': self.template_manager.current_template_version,
            'emails_sent': self.template_manager.emails_sent_with_current,
            'performance_history': self.template_manager.performance_history,
            'template_available': bool(self.current_template)
        }

    def send_email(self, recipient: Dict[str, str]) -> bool:
        """Send an email to a recipient."""
        try:
            # Ensure template is available
            if not self._ensure_template_available():
                print("[ERROR] No valid template available")
                return False
                
            # Get company info from config
            company_info = self.config.get('company', {})
            
            # Render email content
            email_content = self.template_renderer.render_email(
                self.current_template,
                recipient,
                company_info
            )
            
            if not email_content:
                print("[ERROR] Failed to render email content")
                return False
                
            # Send email
            success = self.email_sender.send_email(
                to_email=recipient['email'],
                to_name=recipient['name'],
                subject=email_content['subject'],
                html_content=email_content['html'],
                text_content=email_content['plain_text']
            )
            
            if success:
                print(f"Successfully sent email to {recipient['email']}")
            else:
                print(f"Failed to send email to {recipient['email']}")
                
            return success
            
        except Exception as e:
            print(f"Error sending email: {str(e)}")
            return False 