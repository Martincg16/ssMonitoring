from django.core.management.base import BaseCommand, CommandError
from solarDataFetch.fetchers.huaweiFetcher import HuaweiFetcher
from solarDataStore.cruds.huaweiCruds import insert_huawei_generacion_inversor_dia
from django.utils import timezone
from datetime import datetime, timedelta
import logging

logger = logging.getLogger('management_commands')

class Command(BaseCommand):
    help = 'Fetch and store Huawei inverter production data for a specific date (devTypeId=1, <100 entries).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--date',
            type=str,
            help='Date to collect data for in YYYY-MM-DD format (defaults to yesterday if not provided)'
        )

    def handle(self, *args, **options):
        logger.info("|HuaweiInverterGen|handle| Starting Huawei inverter generation collection")
        
        fetcher = HuaweiFetcher()
        logger.info("|HuaweiInverterGen|handle| Created HuaweiFetcher instance")
        
        token = fetcher.login()
        logger.info("|HuaweiInverterGen|handle| Successfully obtained authentication token")

        # Handle date parameter
        if options['date']:
            try:
                target_date = datetime.strptime(options['date'], '%Y-%m-%d')
                logger.info(f"|HuaweiInverterGen|handle| Using provided date: {target_date.date()}")
                self.stdout.write(self.style.NOTICE(f'Using provided date: {target_date.date()}'))
            except ValueError:
                raise CommandError('Invalid date format. Please use YYYY-MM-DD format.')
        else:
            # Default to yesterday
            now = timezone.now()
            target_date = now - timedelta(days=1)
            logger.info(f"|HuaweiInverterGen|handle| No date provided, using yesterday: {target_date.date()}")
            self.stdout.write(self.style.NOTICE(f'No date provided, using yesterday: {target_date.date()}'))

        collect_time = fetcher.midnight_colombia_timestamp(target_date)
        logger.info(f"|HuaweiInverterGen|handle| Processing data for date: {target_date.date()}")
        
        for dev_type_id in ["1", "38"]:
            logger.info(f"|HuaweiInverterGen|handle| Starting processing for dev_type_id {dev_type_id}")
            batch_number = 1
            self.stdout.write(self.style.NOTICE(f'Processing dev_type_id {dev_type_id}...'))
            while True:
                logger.info(f"|HuaweiInverterGen|handle| Processing dev_type_id {dev_type_id}, batch {batch_number}")
                retry = False
                for attempt in range(2):  # Allow one retry per batch
                    try:
                        inverter_data = fetcher.fetch_huawei_generacion_inversor_dia(
                            dev_type_id=dev_type_id,
                            batch_number=batch_number,
                            collect_time=collect_time,
                            token=token
                        )
                        logger.info(f"|HuaweiInverterGen|handle| Batch {batch_number} for dev_type_id {dev_type_id} fetched successfully: {len(inverter_data)} inverters")
                        break  # Success: exit retry loop
                    except RuntimeError as e:
                        if hasattr(e, 'args') and len(e.args) > 1 and e.args[1] == 305 and not retry:
                            logger.warning(f"|HuaweiInverterGen|handle| Session expired on dev_type_id {dev_type_id}, batch {batch_number}, re-authenticating")
                            self.stdout.write(self.style.WARNING('Session expired, re-logging in and retrying batch...'))
                            token = fetcher.login()
                            logger.info("|HuaweiInverterGen|handle| Re-authentication successful, retrying batch")
                            retry = True
                            continue
                        else:
                            logger.error(f"|HuaweiInverterGen|handle| Error fetching inverter data (dev_type_id {dev_type_id}, batch {batch_number}): {e}")
                            raise CommandError(f'Error fetching inverter data (dev_type_id {dev_type_id}, batch {batch_number}): {e}')
                else:
                    logger.error(f"|HuaweiInverterGen|handle| Failed after retrying batch {batch_number} for dev_type_id {dev_type_id} due to repeated session expiration")
                    raise CommandError(f'Failed after retrying batch {batch_number} for dev_type_id {dev_type_id} due to repeated session expiration.')
                self.stdout.write(self.style.NOTICE(f'{inverter_data}'))
                # Insert always happens once per batch
                try:
                    insert_huawei_generacion_inversor_dia(inverter_data)
                    logger.info(f"|HuaweiInverterGen|handle| Batch {batch_number} for dev_type_id {dev_type_id} data inserted successfully")
                except Exception as e:
                    logger.error(f"|HuaweiInverterGen|handle| Error inserting inverter data (dev_type_id {dev_type_id}, batch {batch_number}): {e}")
                    self.stdout.write(self.style.ERROR(f'Error inserting inverter data (dev_type_id {dev_type_id}, batch {batch_number}): {e}'))
                    raise
                    
                self.stdout.write(self.style.SUCCESS(
                    f'dev_type_id {dev_type_id} - Batch {batch_number}: {len(inverter_data)} inverters processed.'
                ))
                if len(inverter_data) < 100:
                    logger.info(f"|HuaweiInverterGen|handle| Last batch for dev_type_id {dev_type_id}. Total batches: {batch_number}")
                    break
                batch_number += 1
            logger.info(f"|HuaweiInverterGen|handle| Completed processing for dev_type_id {dev_type_id}")
        
        logger.info("|HuaweiInverterGen|handle| Huawei inverter generation collection completed successfully") 