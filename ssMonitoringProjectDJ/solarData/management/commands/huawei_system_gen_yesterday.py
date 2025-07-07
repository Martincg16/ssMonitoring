from django.core.management.base import BaseCommand, CommandError
from solarDataFetch.fetchers.huaweiFetcher import HuaweiFetcher
from solarDataStore.cruds.huaweiCruds import insert_huawei_generacion_sistema_dia
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger('management_commands')

class Command(BaseCommand):
    help = 'Fetch and store Huawei system production data for yesterday (single batch, <100 systems).'

    def handle(self, *args, **options):
        logger.info("|HuaweiSystemGenYesterday|handle| Starting Huawei system generation collection for yesterday")
        
        fetcher = HuaweiFetcher()
        logger.info("|HuaweiSystemGenYesterday|handle| Created HuaweiFetcher instance")
        
        token = fetcher.login()
        logger.info("|HuaweiSystemGenYesterday|handle| Successfully obtained authentication token")

        # Calculate yesterday's date in Colombian timezone
        now = timezone.now()
        yesterday_local = now - timedelta(days=1)
        collect_time = fetcher.midnight_colombia_timestamp(yesterday_local)
        logger.info(f"|HuaweiSystemGenYesterday|handle| Processing data for date: {yesterday_local.date()}")

        batch_number = 1
        while True:
            logger.info(f"|HuaweiSystemGenYesterday|handle| Processing batch {batch_number}")
            self.stdout.write(self.style.NOTICE(f'Processing batch {batch_number}...'))
            retry = False
            for attempt in range(2):  # Allow one retry per batch
                try:
                    system_data = fetcher.fetch_huawei_generacion_sistema_dia(
                        batch_number=batch_number,
                        collect_time=collect_time,
                        token=token
                    )
                    logger.info(f"|HuaweiSystemGenYesterday|handle| Batch {batch_number} fetched successfully: {len(system_data)} systems")
                    break  # Success: exit retry loop
                except RuntimeError as e:
                    if hasattr(e, 'args') and len(e.args) > 1 and e.args[1] == 305 and not retry:
                        logger.warning(f"|HuaweiSystemGenYesterday|handle| Session expired on batch {batch_number}, re-authenticating")
                        self.stdout.write(self.style.WARNING('Session expired, re-logging in and retrying batch...'))
                        token = fetcher.login()
                        logger.info("|HuaweiSystemGenYesterday|handle| Re-authentication successful, retrying batch")
                        retry = True
                        continue
                    else:
                        logger.error(f"|HuaweiSystemGenYesterday|handle| Error fetching batch {batch_number}: {e}")
                        raise CommandError(f'Error fetching system data (batch {batch_number}): {e}')
            else:
                logger.error(f"|HuaweiSystemGenYesterday|handle| Failed after retrying batch {batch_number} due to repeated session expiration")
                raise CommandError(f'Failed after retrying batch {batch_number} due to repeated session expiration.')

            # Insert always happens once per batch
            try:
                insert_huawei_generacion_sistema_dia(system_data)
                logger.info(f"|HuaweiSystemGenYesterday|handle| Batch {batch_number} data inserted successfully")
            except Exception as e:
                logger.error(f"|HuaweiSystemGenYesterday|handle| Error inserting batch {batch_number} data: {e}")
                raise
                
            self.stdout.write(self.style.SUCCESS(
                f'Batch {batch_number}: {len(system_data)} systems processed.'
            ))
            if len(system_data) < 100:
                logger.info(f"|HuaweiSystemGenYesterday|handle| Last batch processed. Total batches: {batch_number}")
                break
            batch_number += 1
            
        logger.info("|HuaweiSystemGenYesterday|handle| Huawei system generation collection completed successfully")
