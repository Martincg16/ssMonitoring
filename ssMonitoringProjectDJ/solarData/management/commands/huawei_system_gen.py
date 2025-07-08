from django.core.management.base import BaseCommand, CommandError
from solarDataFetch.fetchers.huaweiFetcher import HuaweiFetcher
from solarDataStore.cruds.huaweiCruds import insert_huawei_generacion_sistema_dia
from django.utils import timezone
from datetime import datetime, timedelta
import logging

logger = logging.getLogger('management_commands')

class Command(BaseCommand):
    help = 'Fetch and store Huawei system production data for a specific date (single batch, <100 systems).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--date',
            type=str,
            help='Date to collect data for in YYYY-MM-DD format (defaults to yesterday if not provided)'
        )

    def handle(self, *args, **options):
        logger.info("|HuaweiSystemGen|handle| Starting Huawei system generation collection")
        
        fetcher = HuaweiFetcher()
        logger.info("|HuaweiSystemGen|handle| Created HuaweiFetcher instance")
        
        token = fetcher.login()
        logger.info("|HuaweiSystemGen|handle| Successfully obtained authentication token")

        # Handle date parameter
        if options['date']:
            try:
                target_date = datetime.strptime(options['date'], '%Y-%m-%d')
                logger.info(f"|HuaweiSystemGen|handle| Using provided date: {target_date.date()}")
                self.stdout.write(self.style.NOTICE(f'Using provided date: {target_date.date()}'))
            except ValueError:
                raise CommandError('Invalid date format. Please use YYYY-MM-DD format.')
        else:
            # Default to yesterday
            now = timezone.now()
            target_date = now - timedelta(days=1)
            logger.info(f"|HuaweiSystemGen|handle| No date provided, using yesterday: {target_date.date()}")
            self.stdout.write(self.style.NOTICE(f'No date provided, using yesterday: {target_date.date()}'))

        # Calculate collect_time for the target date in Colombian timezone
        collect_time = fetcher.midnight_colombia_timestamp(target_date)
        logger.info(f"|HuaweiSystemGen|handle| Processing data for date: {target_date.date()}")

        batch_number = 1
        while True:
            logger.info(f"|HuaweiSystemGen|handle| Processing batch {batch_number}")
            self.stdout.write(self.style.NOTICE(f'Processing batch {batch_number}...'))
            retry = False
            for attempt in range(2):  # Allow one retry per batch
                try:
                    system_data = fetcher.fetch_huawei_generacion_sistema_dia(
                        batch_number=batch_number,
                        collect_time=collect_time,
                        token=token
                    )
                    logger.info(f"|HuaweiSystemGen|handle| Batch {batch_number} fetched successfully: {len(system_data)} systems")
                    break  # Success: exit retry loop
                except RuntimeError as e:
                    if hasattr(e, 'args') and len(e.args) > 1 and e.args[1] == 305 and not retry:
                        logger.warning(f"|HuaweiSystemGen|handle| Session expired on batch {batch_number}, re-authenticating")
                        self.stdout.write(self.style.WARNING('Session expired, re-logging in and retrying batch...'))
                        token = fetcher.login()
                        logger.info("|HuaweiSystemGen|handle| Re-authentication successful, retrying batch")
                        retry = True
                        continue
                    else:
                        logger.error(f"|HuaweiSystemGen|handle| Error fetching batch {batch_number}: {e}")
                        raise CommandError(f'Error fetching system data (batch {batch_number}): {e}')
            else:
                logger.error(f"|HuaweiSystemGen|handle| Failed after retrying batch {batch_number} due to repeated session expiration")
                raise CommandError(f'Failed after retrying batch {batch_number} due to repeated session expiration.')

            # Insert always happens once per batch
            try:
                insert_huawei_generacion_sistema_dia(system_data)
                logger.info(f"|HuaweiSystemGen|handle| Batch {batch_number} data inserted successfully")
            except Exception as e:
                logger.error(f"|HuaweiSystemGen|handle| Error inserting batch {batch_number} data: {e}")
                raise
                
            self.stdout.write(self.style.SUCCESS(
                f'Batch {batch_number}: {len(system_data)} systems processed.'
            ))
            if len(system_data) < 100:
                logger.info(f"|HuaweiSystemGen|handle| Last batch processed. Total batches: {batch_number}")
                break
            batch_number += 1
            
        logger.info("|HuaweiSystemGen|handle| Huawei system generation collection completed successfully") 