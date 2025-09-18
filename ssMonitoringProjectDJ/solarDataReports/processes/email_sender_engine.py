"""
Email Sender Engine for Solar Data Reports
Handles sending PDF reports via email with attachments
"""

import logging
import os
from datetime import datetime
from django.core.mail import EmailMessage
from django.conf import settings

# Initialize logger
logger = logging.getLogger('solarDataReports.email_sender')

class SolarDataEmailSender:
    """
    Handles sending PDF reports via email using Django's email backend
    """
    
    def __init__(self):
        """Initialize email sender with default settings"""
        self.from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', '')
        self.default_recipients = getattr(settings, 'ALERT_EMAIL_RECIPIENTS', [])
    
    def send_pdf_report(self, pdf_path=None, pdf_content=None, recipients=None, 
                       subject=None, body=None, report_date=None):
        """
        Send PDF report via email with attachment
        
        Args:
            pdf_path (str, optional): Path to PDF file to attach
            pdf_content (BytesIO, optional): PDF content in memory
            recipients (list, optional): List of email recipients
            subject (str, optional): Email subject line
            body (str, optional): Email body content
            report_date (str, optional): Date for the report (used in filename/subject)
            
        Returns:
            dict: Result of email sending operation with success status and details
        """
        logger.info("Preparing to send PDF report via email")
        
        try:
            # Validate email configuration
            if not self.from_email:
                logger.error("No FROM email configured in settings")
                return {
                    'success': False,
                    'error': 'Email FROM address not configured in settings',
                    'details': 'Check DEFAULT_FROM_EMAIL setting'
                }
            
            # Determine recipients
            if recipients is None:
                recipients = ['martin@rocasol.com.co']  # Default as requested
            elif isinstance(recipients, str):
                recipients = [recipients]
            
            if not recipients:
                logger.error("No email recipients specified")
                return {
                    'success': False,
                    'error': 'No email recipients specified',
                    'details': 'Provide recipients list or configure ALERT_EMAIL_RECIPIENTS'
                }
            
            # Set default subject if not provided
            if subject is None:
                date_str = report_date or "Latest"
                subject = f"📊 Solar Production Report - {date_str}"
            
            # Set default body if not provided
            if body is None:
                body = """
Hello,

Please find attached the solar production analysis report.

This automated report includes:
• Zero production analysis
• Production deviation analysis  
• Quality standards compliance

Best regards,
Solar Monitoring System
                """.strip()
            
            # Validate PDF attachment
            if pdf_path is None and pdf_content is None:
                logger.error("No PDF attachment provided")
                return {
                    'success': False,
                    'error': 'No PDF attachment provided',
                    'details': 'Provide either pdf_path or pdf_content'
                }
            
            # Create email message
            email = EmailMessage(
                subject=subject,
                body=body,
                from_email=self.from_email,
                to=recipients
            )
            
            # Attach PDF
            if pdf_path:
                # Attach from file path
                if not os.path.exists(pdf_path):
                    logger.error(f"PDF file not found: {pdf_path}")
                    return {
                        'success': False,
                        'error': f'PDF file not found: {pdf_path}',
                        'details': 'Verify PDF was generated successfully'
                    }
                
                # Generate filename for attachment
                filename = self._generate_attachment_filename(report_date)
                email.attach_file(pdf_path, mimetype='application/pdf')
                logger.debug(f"Attached PDF file: {pdf_path}")
                
            elif pdf_content:
                # Attach from memory content
                filename = self._generate_attachment_filename(report_date)
                pdf_data = pdf_content.getvalue()
                email.attach(filename, pdf_data, 'application/pdf')
                logger.debug(f"Attached PDF from memory ({len(pdf_data)} bytes)")
            
            # Send email
            logger.info(f"Sending email to {len(recipients)} recipients: {', '.join(recipients)}")
            
            try:
                sent_count = email.send()
                
                if sent_count > 0:
                    logger.info(f"Email sent successfully to {len(recipients)} recipients")
                    return {
                        'success': True,
                        'recipients': recipients,
                        'subject': subject,
                        'attachment_method': 'file' if pdf_path else 'memory',
                        'sent_count': sent_count
                    }
                else:
                    logger.warning("Email send returned 0 - may indicate delivery issues")
                    return {
                        'success': False,
                        'error': 'Email send returned 0',
                        'details': 'Email may not have been delivered'
                    }
                    
            except Exception as send_error:
                logger.error(f"Failed to send email: {str(send_error)}")
                return {
                    'success': False,
                    'error': f'Email sending failed: {str(send_error)}',
                    'details': 'Check email configuration and network connectivity'
                }
                
        except Exception as e:
            logger.error(f"Error preparing email: {str(e)}")
            return {
                'success': False,
                'error': f'Email preparation failed: {str(e)}',
                'details': 'Check email configuration and parameters'
            }
    
    def _generate_attachment_filename(self, report_date=None):
        """
        Generate a descriptive filename for the PDF attachment
        
        Args:
            report_date (str, optional): Date for the report
            
        Returns:
            str: Generated filename
        """
        if report_date:
            return f"solar_production_report_{report_date}.pdf"
        else:
            from datetime import datetime
            today = datetime.now().strftime('%Y-%m-%d')
            return f"solar_production_report_{today}.pdf"
    
    def send_test_email(self, recipients=None):
        """
        Send a test email to verify email configuration
        
        Args:
            recipients (list, optional): Test email recipients
            
        Returns:
            dict: Result of test email operation
        """
        logger.info("Sending test email")
        
        try:
            if recipients is None:
                recipients = ['martin@rocasol.com.co']
            
            # Create simple test email
            email = EmailMessage(
                subject="🧪 Solar Monitoring - Email Test",
                body="""
This is a test email from the Solar Monitoring System.

If you received this email, the email configuration is working correctly.

Configuration details:
• Email backend: Django SMTP
• From address: """ + str(self.from_email) + """
• Test sent at: """ + str(datetime.now()) + """

Best regards,
Solar Monitoring System
                """.strip(),
                from_email=self.from_email,
                to=recipients
            )
            
            sent_count = email.send()
            
            if sent_count > 0:
                logger.info(f"Test email sent successfully to {recipients}")
                return {
                    'success': True,
                    'message': f'Test email sent to {recipients}',
                    'sent_count': sent_count
                }
            else:
                return {
                    'success': False,
                    'error': 'Test email send returned 0'
                }
                
        except Exception as e:
            logger.error(f"Test email failed: {str(e)}")
            return {
                'success': False,
                'error': f'Test email failed: {str(e)}'
            }
    
    def validate_email_configuration(self):
        """
        Validate that email settings are properly configured
        
        Returns:
            dict: Validation results with configuration status
        """
        logger.debug("Validating email configuration")
        
        validation_results = {
            'valid': True,
            'issues': [],
            'configuration': {}
        }
        
        # Check FROM email
        if not self.from_email:
            validation_results['valid'] = False
            validation_results['issues'].append('DEFAULT_FROM_EMAIL not configured')
        else:
            validation_results['configuration']['from_email'] = self.from_email
        
        # Check email backend
        email_backend = getattr(settings, 'EMAIL_BACKEND', None)
        if email_backend:
            validation_results['configuration']['email_backend'] = email_backend
        else:
            validation_results['issues'].append('EMAIL_BACKEND not configured')
        
        # Check SMTP settings if using SMTP backend
        if email_backend == 'django.core.mail.backends.smtp.EmailBackend':
            smtp_settings = {
                'EMAIL_HOST': getattr(settings, 'EMAIL_HOST', None),
                'EMAIL_PORT': getattr(settings, 'EMAIL_PORT', None),
                'EMAIL_USE_TLS': getattr(settings, 'EMAIL_USE_TLS', None),
                'EMAIL_HOST_USER': getattr(settings, 'EMAIL_HOST_USER', None),
                'EMAIL_HOST_PASSWORD': getattr(settings, 'EMAIL_HOST_PASSWORD', None)
            }
            
            for setting, value in smtp_settings.items():
                if value is None or (isinstance(value, str) and not value.strip()):
                    validation_results['issues'].append(f'{setting} not configured')
                else:
                    # Don't log password in plain text
                    if 'PASSWORD' in setting:
                        validation_results['configuration'][setting] = '***configured***'
                    else:
                        validation_results['configuration'][setting] = value
        
        # Check default recipients
        if self.default_recipients:
            validation_results['configuration']['default_recipients'] = len(self.default_recipients)
        
        if validation_results['issues']:
            validation_results['valid'] = False
            logger.warning(f"Email configuration issues found: {validation_results['issues']}")
        else:
            logger.info("Email configuration validation passed")
        
        return validation_results
