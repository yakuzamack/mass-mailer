from typing import Dict, Any
from datetime import datetime

class Analytics:
    def __init__(self):
        self.send_success_count = 0
        self.send_failure_count = 0
        self.open_count = 0
        self.click_count = 0
        
    def track_send_success(self, email: str):
        """Track successful email send."""
        self.send_success_count += 1
        print(f"Successfully sent email to {email}")
        
    def track_send_failure(self, email: str):
        """Track failed email send."""
        self.send_failure_count += 1
        print(f"Failed to send email to {email}")
        
    def track_email_open(self, email: str):
        """Track email open."""
        self.open_count += 1
        print(f"Email opened by {email}")
        
    def track_link_click(self, email: str):
        """Track link click in email."""
        self.click_count += 1
        print(f"Link clicked by {email}")
        
    def get_stats(self):
        """Get current analytics stats."""
        return {
            'send_success_count': self.send_success_count,
            'send_failure_count': self.send_failure_count,
            'open_count': self.open_count,
            'click_count': self.click_count,
            'open_rate': self.open_count / self.send_success_count if self.send_success_count > 0 else 0,
            'click_rate': self.click_count / self.open_count if self.open_count > 0 else 0
        }

    def get_metrics(self, start_time: str, end_time: str) -> Dict[str, float]:
        """Get metrics for the specified time period."""
        return self.get_stats()
        
    def update_metrics(self, new_metrics: Dict[str, float]) -> None:
        """Update the current metrics."""
        self.metrics.update(new_metrics) 