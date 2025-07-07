from django.core.management.base import BaseCommand, CommandError
from solarDataFetch.fetchers.huaweiFetcher import HuaweiFetcher
from solarDataStore.cruds.huaweiCruds import insert_huawei_generacion_inversor_dia
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger('management_commands')

class Command(BaseCommand):
    help = 'Fetch and store Huawei inverter production data for yesterday (devTypeId=1, <100 entries).'

    def handle(self, *args, **options):
        logger.info("|HuaweiInverterGenYesterday|handle| Starting Huawei inverter generation collection for yesterday")
        
        fetcher = HuaweiFetcher()
        logger.info("|HuaweiInverterGenYesterday|handle| Created HuaweiFetcher instance")
        
        token = fetcher.login()
        logger.info("|HuaweiInverterGenYesterday|handle| Successfully obtained authentication token")

        now = timezone.now()
        yesterday_local = now - timedelta(days=1)
        collect_time = fetcher.midnight_colombia_timestamp(yesterday_local)
        logger.info(f"|HuaweiInverterGenYesterday|handle| Processing data for date: {yesterday_local.date()}")
        
        for dev_type_id in ["1", "38"]:
            logger.info(f"|HuaweiInverterGenYesterday|handle| Starting processing for dev_type_id {dev_type_id}")
            batch_number = 1
            self.stdout.write(self.style.NOTICE(f'Processing dev_type_id {dev_type_id}...'))
            while True:
                logger.info(f"|HuaweiInverterGenYesterday|handle| Processing dev_type_id {dev_type_id}, batch {batch_number}")
                retry = False
                for attempt in range(2):  # Allow one retry per batch
                    try:
                        inverter_data = fetcher.fetch_huawei_generacion_inversor_dia(
                            dev_type_id=dev_type_id,
                            batch_number=batch_number,
                            collect_time=collect_time,
                            token=token
                        )
                        logger.info(f"|HuaweiInverterGenYesterday|handle| Batch {batch_number} for dev_type_id {dev_type_id} fetched successfully: {len(inverter_data)} inverters")
                        break  # Success: exit retry loop
                    except RuntimeError as e:
                        if hasattr(e, 'args') and len(e.args) > 1 and e.args[1] == 305 and not retry:
                            logger.warning(f"|HuaweiInverterGenYesterday|handle| Session expired on dev_type_id {dev_type_id}, batch {batch_number}, re-authenticating")
                            self.stdout.write(self.style.WARNING('Session expired, re-logging in and retrying batch...'))
                            token = fetcher.login()
                            logger.info("|HuaweiInverterGenYesterday|handle| Re-authentication successful, retrying batch")
                            retry = True
                            continue
                        else:
                            logger.error(f"|HuaweiInverterGenYesterday|handle| Error fetching inverter data (dev_type_id {dev_type_id}, batch {batch_number}): {e}")
                            raise CommandError(f'Error fetching inverter data (dev_type_id {dev_type_id}, batch {batch_number}): {e}')
                else:
                    logger.error(f"|HuaweiInverterGenYesterday|handle| Failed after retrying batch {batch_number} for dev_type_id {dev_type_id} due to repeated session expiration")
                    raise CommandError(f'Failed after retrying batch {batch_number} for dev_type_id {dev_type_id} due to repeated session expiration.')
                self.stdout.write(self.style.NOTICE(f'{inverter_data}'))
                # Insert always happens once per batch
                try:
                    insert_huawei_generacion_inversor_dia(inverter_data)
                    logger.info(f"|HuaweiInverterGenYesterday|handle| Batch {batch_number} for dev_type_id {dev_type_id} data inserted successfully")
                except Exception as e:
                    logger.error(f"|HuaweiInverterGenYesterday|handle| Error inserting inverter data (dev_type_id {dev_type_id}, batch {batch_number}): {e}")
                    self.stdout.write(self.style.ERROR(f'Error inserting inverter data (dev_type_id {dev_type_id}, batch {batch_number}): {e}'))
                    raise
                    
                self.stdout.write(self.style.SUCCESS(
                    f'dev_type_id {dev_type_id} - Batch {batch_number}: {len(inverter_data)} inverters processed.'
                ))
                if len(inverter_data) < 100:
                    logger.info(f"|HuaweiInverterGenYesterday|handle| Last batch for dev_type_id {dev_type_id}. Total batches: {batch_number}")
                    break
                batch_number += 1
            logger.info(f"|HuaweiInverterGenYesterday|handle| Completed processing for dev_type_id {dev_type_id}")
        
        logger.info("|HuaweiInverterGenYesterday|handle| Huawei inverter generation collection completed successfully")
