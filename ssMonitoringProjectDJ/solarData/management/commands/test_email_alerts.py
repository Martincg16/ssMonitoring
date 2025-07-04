from django.core.management.base import BaseCommand
from django.conf import settings
import logging

class Command(BaseCommand):
    help = 'Test email alert functionality for ERROR and CRITICAL logs'

    def add_arguments(self, parser):
        parser.add_argument(
            '--level',
            type=str,
            choices=['error', 'critical'],
            default='error',
            help='Test log level (error or critical)'
        )

    def handle(self, *args, **options):
        """Test email alerts by generating test log messages"""
        
        # Check if email is configured
        if not hasattr(settings, 'ALERT_EMAIL_RECIPIENTS') or not settings.ALERT_EMAIL_RECIPIENTS:
            self.stdout.write(
                self.style.ERROR('❌ Email alerts not configured! Please set ALERT_EMAIL_RECIPIENTS in your environment.')
            )
            return
        
        # Test different loggers
        loggers_to_test = [
            ('huawei_fetcher', 'Huawei Data Fetcher'),
            ('solis_fetcher', 'Solis Data Fetcher'),
            ('management_commands', 'Management Commands')
        ]
        
        level = options['level'].upper()
        
        self.stdout.write(f"🧪 Testing {level} level email alerts...")
        self.stdout.write(f"📧 Recipients: {', '.join(settings.ALERT_EMAIL_RECIPIENTS)}")
        self.stdout.write("─" * 60)
        
        for logger_name, logger_description in loggers_to_test:
            logger = logging.getLogger(logger_name)
            
            if level == 'ERROR':
                test_message = f"TEST EMAIL ALERT: {logger_description} encountered a simulated error for testing purposes"
                logger.error(test_message)
                self.stdout.write(f"✅ Sent ERROR test email for: {logger_description}")
            
            elif level == 'CRITICAL':
                test_message = f"TEST EMAIL ALERT: {logger_description} encountered a simulated critical failure for testing purposes"
                logger.critical(test_message)
                self.stdout.write(f"🚨 Sent CRITICAL test email for: {logger_description}")
        
        self.stdout.write("─" * 60)
        self.stdout.write(
            self.style.SUCCESS(f"✅ Test {level} email alerts sent! Check your email inbox.")
        )
        self.stdout.write(
            self.style.WARNING("⚠️ If you don't receive emails, check:")
        )
        self.stdout.write("   1. AWS SES configuration and credentials")
        self.stdout.write("   2. Email addresses in ALERT_EMAIL_RECIPIENTS")
        self.stdout.write("   3. Spam/junk folders")
        self.stdout.write("   4. AWS SES sending limits and verification status") 