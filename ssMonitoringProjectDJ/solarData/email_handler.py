import logging
from django.core.mail import send_mail
from django.conf import settings
from datetime import datetime
import traceback

class EmailAlertHandler(logging.Handler):
    """
    Custom email handler that sends alerts for ERROR and CRITICAL logs only.
    Integrates with AWS SES through Django's email backend.
    """
    
    def emit(self, record):
        """Send email alert for ERROR and CRITICAL logs"""
        try:
            # Only send emails for ERROR (40) and CRITICAL (50) levels
            if record.levelno < logging.ERROR:
                return
                
            # Skip if email settings are not configured
            if not hasattr(settings, 'ALERT_EMAIL_RECIPIENTS') or not settings.ALERT_EMAIL_RECIPIENTS:
                return
                
            # Format the log message
            log_entry = self.format(record)
            
            # Determine email subject based on log level
            level = record.levelname
            if level == 'CRITICAL':
                emoji = '🚨'
                priority = 'URGENT'
            else:  # ERROR
                emoji = '❌'
                priority = 'HIGH'
                
            subject = f"{emoji} Solar Monitoring Alert - {priority}: {level}"
            
            # Extract component information from logger name
            component = self._get_component_name(record.name)
            
            # Create detailed email body
            message = self._create_email_body(record, log_entry, level, component)
            
            # Send email to all recipients
            recipients = [email.strip() for email in settings.ALERT_EMAIL_RECIPIENTS if email.strip()]
            
            if recipients:
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=recipients,
                    fail_silently=True  # Don't crash the app if email fails
                )
                
        except Exception as e:
            # Don't crash the application if email sending fails
            # Could log this to a file, but avoid infinite loops
            pass
    
    def _get_component_name(self, logger_name):
        """Extract human-readable component name from logger name"""
        component_map = {
            'huawei_fetcher': 'Huawei Data Fetcher',
            'solis_fetcher': 'Solis Data Fetcher',
            'huawei_store': 'Huawei Data Storage',
            'solis_store': 'Solis Data Storage',
            'huawei_newsystem': 'Huawei System Registration',
            'solis_newsystem': 'Solis System Registration',
            'management_commands': 'Management Commands'
        }
        return component_map.get(logger_name, logger_name.title())
    
    def _create_email_body(self, record, log_entry, level, component):
        """Create detailed email body with context information"""
        return f"""
🔴 Solar Monitoring System Alert

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (Colombian Time)
🔖 Level: {level}
🏗️ Component: {component}
📍 Logger: {record.name}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📝 Message:
{record.getMessage()}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔍 Technical Details:
File: {record.pathname}
Function: {record.funcName}
Line: {record.lineno}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 Full Log Entry:
{log_entry}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🛠️ Next Steps:
1. Check the application logs for more context
2. Verify API connectivity and credentials
3. Check system resources (disk space, memory)
4. Review recent deployments or configuration changes

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

This is an automated alert from the Solar Monitoring System.
Please do not reply to this email.
""" 