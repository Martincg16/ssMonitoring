"""
Master command to collect all yesterday's solar data from all systems.
This command orchestrates all individual data collection commands.
"""

from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.utils import timezone
import logging

# Use the management commands logger for orchestration logging
logger = logging.getLogger('management_commands')


class Command(BaseCommand):
    help = 'Collect all yesterday data from Solis and Huawei systems'

    def add_arguments(self, parser):
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
        
        # Define all data collection commands in logical order
        commands = [
            # Solis commands
            ('solis_system_gen_yesterday', 'Solis System Generation'),
            ('solis_inverter_gen_yesterday', 'Solis Inverter Generation'),
            
            # Huawei commands
            ('huawei_system_gen_yesterday', 'Huawei System Generation'),
            ('huawei_inverter_gen_yesterday', 'Huawei Inverter Generation'),
            ('huawei_granular_gen_yesterday', 'Huawei Granular Generation'),
        ]
        
        logger.info(f"Starting collection of all yesterday data at {timezone.now()}")
        self.stdout.write(
            self.style.SUCCESS(
                f'🚀 Starting collection of all yesterday data at {timezone.now()}'
            )
        )
        
        success_count = 0
        error_count = 0
        results = []
        
        for command_name, description in commands:
            logger.info(f"Running command: {command_name} ({description})")
            self.stdout.write(f'\n📊 Running: {description}...')
            
            try:
                if verbose:
                    # Show command output
                    call_command(command_name, verbosity=2)
                else:
                    # Run silently
                    call_command(command_name, verbosity=0)
                
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
                f'📈 COLLECTION SUMMARY - Completed at {timezone.now()}'
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
                self.style.SUCCESS('\n🎉 All data collection completed successfully!')
            )
        elif success_count > 0:
            self.stdout.write(
                self.style.WARNING(
                    f'\n⚠️  Partial success: {success_count} succeeded, {error_count} failed'
                )
            )
        else:
            self.stdout.write(
                self.style.ERROR('\n💥 All data collection commands failed!')
            )
            raise Exception(f'All {len(commands)} data collection commands failed') 