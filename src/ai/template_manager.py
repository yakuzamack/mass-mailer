import os
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
from .template_generator import TemplateGenerator
from src.config import TEMPLATE_CONFIG

class TemplateManager:
    def __init__(self, config=None):
        self.config = config or {}
        self.template_config = self.config.get('template', TEMPLATE_CONFIG)
        self.template_generator = TemplateGenerator(self.config)
        self.current_template = None
        self.current_template_version = 0
        self.performance_history = []
        self.emails_sent_with_current = 0
        self.rotation_threshold = 50  # Number of emails before rotation
        
        # Create template directory if it doesn't exist
        template_dir = self.template_config.get('template_dir', os.path.join(os.path.dirname(__file__), 'templates'))
        os.makedirs(template_dir, exist_ok=True)
        
    def generate_template(self, recipient: Dict[str, Any]) -> Dict[str, str]:
        """Generate a new template for the given recipient."""
        try:
            self.current_template = self.template_generator.generate_template(recipient)
            return self.current_template
        except Exception as e:
            print(f"Error generating template: {str(e)}")
            return None
            
    def get_current_template(self) -> Optional[Dict[str, str]]:
        """Get the current template."""
        return self.current_template
        
    def initialize_templates(self, company_info: Dict[str, str]) -> bool:
        """Generate initial set of templates."""
        try:
            # Generate primary template
            primary_template = self.template_generator.generate_template(company_info)
            if not primary_template:
                print("[ERROR] Failed to generate primary template")
                return False
                
            # Generate backup template
            backup_template = self.template_generator.generate_template(company_info)
            if not backup_template:
                print("[ERROR] Failed to generate backup template")
                return False
                
            # Save both templates
            self._save_template(primary_template, "primary")
            self._save_template(backup_template, "backup")
            
            print("[INFO] Templates initialized successfully")
            return True
            
        except Exception as e:
            print(f"[ERROR] Template initialization failed: {str(e)}")
            return False
        
    def update_performance_metrics(self, metrics: Dict[str, float]) -> None:
        """Update performance metrics and check if rotation is needed."""
        self.performance_history.append({
            'timestamp': datetime.now().isoformat(),
            'metrics': metrics
        })
        
        self.emails_sent_with_current += 1
        
        if self.emails_sent_with_current >= self.rotation_threshold:
            self._rotate_templates()
            
    def _rotate_templates(self) -> bool:
        """Rotate templates and generate new ones based on performance."""
        try:
            # Load current performance metrics
            latest_metrics = self.performance_history[-1]['metrics']
            
            # Generate new templates based on performance
            company_info = self._load_company_info()
            new_primary = self.template_generator.generate_template(
                company_info,
                performance_metrics=latest_metrics
            )
            if not new_primary:
                print("[ERROR] Failed to generate new primary template")
                return False
                
            new_backup = self.template_generator.generate_backup_template(
                company_info,
                performance_metrics=latest_metrics
            )
            if not new_backup:
                print("[ERROR] Failed to generate new backup template")
                return False
                
            # Save new templates
            self._save_template(new_primary, "primary")
            self._save_template(new_backup, "backup")
            
            # Reset counter
            self.emails_sent_with_current = 0
            self.current_template_version += 1
            
            print("[INFO] Templates rotated successfully")
            return True
            
        except Exception as e:
            print(f"[ERROR] Template rotation failed: {str(e)}")
            return False
        
    def _save_template(self, template: Dict[str, str], template_type: str) -> bool:
        """Save template to file."""
        try:
            template_path = os.path.join(
                self.template_config['template_dir'],
                f"{template_type}_template_v{self.current_template_version}.json"
            )
            with open(template_path, 'w') as f:
                json.dump(template, f, indent=2)
            return True
        except Exception as e:
            print(f"[ERROR] Failed to save template: {str(e)}")
            return False
            
    def _load_template(self, template_type: str) -> Optional[Dict[str, str]]:
        """Load template from file."""
        try:
            template_path = os.path.join(
                self.template_config['template_dir'],
                f"{template_type}_template_v{self.current_template_version}.json"
            )
            if not os.path.exists(template_path):
                print(f"[ERROR] Template file not found: {template_path}")
                return None
                
            with open(template_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"[ERROR] Failed to load template: {str(e)}")
            return None
            
    def _load_company_info(self) -> Dict[str, str]:
        """Load company information from configuration."""
        # This should be implemented based on your configuration management
        # For now, returning a placeholder
        return {
            'name': os.getenv('COMPANY_NAME', 'Company'),
            'industry': os.getenv('COMPANY_INDUSTRY', 'Technology')
        } 