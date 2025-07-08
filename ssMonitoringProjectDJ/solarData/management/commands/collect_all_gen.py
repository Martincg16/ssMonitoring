"""
Master command to collect all solar data from all systems for a specific date.
This command orchestrates all individual data collection commands.
"""

from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.utils import timezone
from datetime import datetime, timedelta
import logging

# Use the management commands logger for orchestration logging
logger = logging.getLogger('management_commands')


class Command(BaseCommand):
    help = 'Collect all data from Solis and Huawei systems for a specific date'

    def add_arguments(self, parser):
        parser.add_argument(
            '--date',
            type=str,
            help='Date to collect data for in YYYY-MM-DD format (defaults to yesterday if not provided)'
        )
        parser.add_argument(
            '--skip-errors',
            action='store_true',
            help='Continue execution even if individual commands fail',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed output from each command',
        )

    def handle(self, *args, **options):
        skip_errors = options['skip_errors']
        verbose = options['verbose']
        target_date = options['date']
        
        # Handle date parameter
        if target_date:
            try:
                # Validate date format
                datetime.strptime(target_date, '%Y-%m-%d')
                logger.info(f"Using provided date: {target_date}")
                self.stdout.write(self.style.NOTICE(f'Using provided date: {target_date}'))
            except ValueError:
                self.stdout.write(self.style.ERROR('Invalid date format. Please use YYYY-MM-DD format.'))
                return
        else:
            # Default to yesterday
            now = timezone.now()
            yesterday = now - timedelta(days=1)
            target_date = yesterday.strftime("%Y-%m-%d")
            logger.info(f"No date provided, using yesterday: {target_date}")
            self.stdout.write(self.style.NOTICE(f'No date provided, using yesterday: {target_date}'))
        
        # Define all data collection commands in logical order
        commands = [
            # Solis commands
            ('solis_system_gen', 'Solis System Generation'),
            ('solis_inverter_gen', 'Solis Inverter Generation'),
            
            # Huawei commands
            ('huawei_system_gen', 'Huawei System Generation'),
            ('huawei_inverter_gen', 'Huawei Inverter Generation'),
            ('huawei_granular_gen', 'Huawei Granular Generation'),
        ]
        
        logger.info(f"Starting collection of all data for {target_date} at {timezone.now()}")
        self.stdout.write(
            self.style.SUCCESS(
                f'🚀 Starting collection of all data for {target_date} at {timezone.now()}'
            )
        )
        
        success_count = 0
        error_count = 0
        results = []
        
        for command_name, description in commands:
            logger.info(f"Running command: {command_name} ({description}) for date {target_date}")
            self.stdout.write(f'\n📊 Running: {description} for {target_date}...')
            
            try:
                if verbose:
                    # Show command output with date parameter
                    call_command(command_name, verbosity=2, date=target_date)
                else:
                    # Run silently with date parameter
                    call_command(command_name, verbosity=0, date=target_date)
                
                logger.info(f"Command {command_name} completed successfully")
                self.stdout.write(
                    self.style.SUCCESS(f'✅ {description} - SUCCESS')
                )
                success_count += 1
                results.append((command_name, 'SUCCESS', None))
                
            except Exception as e:
                error_msg = str(e)
                logger.error(f"Command {command_name} failed: {error_msg}")
                self.stdout.write(
                    self.style.ERROR(f'❌ {description} - FAILED: {error_msg}')
                )
                error_count += 1
                results.append((command_name, 'FAILED', error_msg))
                
                if not skip_errors:
                    self.stdout.write(
                        self.style.ERROR(
                            f'\n💥 Stopping execution due to error in {command_name}. '
                            f'Use --skip-errors to continue despite failures.'
                        )
                    )
                    break
        
        # Summary report
        self.stdout.write('\n' + '='*60)
        self.stdout.write(
            self.style.SUCCESS(
                f'📈 COLLECTION SUMMARY for {target_date} - Completed at {timezone.now()}'
            )
        )
        self.stdout.write(f'✅ Successful: {success_count}')
        self.stdout.write(f'❌ Failed: {error_count}')
        
        if verbose or error_count > 0:
            self.stdout.write('\n📋 DETAILED RESULTS:')
            for command_name, status, error in results:
                if status == 'SUCCESS':
                    self.stdout.write(f'  ✅ {command_name}')
                else:
                    self.stdout.write(f'  ❌ {command_name}: {error}')
        
        # Final status
        if error_count == 0:
            self.stdout.write(
                self.style.SUCCESS(f'\n🎉 All data collection for {target_date} completed successfully!')
            )
        elif success_count > 0:
            self.stdout.write(
                self.style.WARNING(
                    f'\n⚠️  Partial success for {target_date}: {success_count} succeeded, {error_count} failed'
                )
            )
        else:
            self.stdout.write(
                self.style.ERROR(f'\n💥 All data collection commands for {target_date} failed!')
            )
            raise Exception(f'All {len(commands)} data collection commands failed for {target_date}') 