from django.core.management.base import BaseCommand, CommandError
from solarDataFetch.fetchers.huaweiFetcher import HuaweiFetcher
from solarDataStore.cruds.huaweiCruds import insert_huawei_generacion_granular_dia
from django.utils import timezone
from datetime import datetime, timedelta
import logging
import traceback
logger = logging.getLogger('management_commands')

class Command(BaseCommand):
    help = 'Fetch and store Huawei MPPT (granular) production data for a specific date.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--date',
            type=str,
            help='Date to collect data for in YYYY-MM-DD format (defaults to yesterday if not provided)'
        )

    def handle(self, *args, **options):
        fetcher = HuaweiFetcher()
        token = fetcher.login()

        # Handle date parameter
        if options['date']:
            try:
                target_date = datetime.strptime(options['date'], '%Y-%m-%d').date()
                logger.info(f"|HuaweiGranularGen|handle| Using provided date: {target_date}")
                self.stdout.write(self.style.NOTICE(f'Using provided date: {target_date}'))
            except ValueError:
                raise CommandError('Invalid date format. Please use YYYY-MM-DD format.')
        else:
            # Default to yesterday
            now = timezone.now()
            yesterday_local = now - timedelta(days=1)
            target_date = yesterday_local.date()
            logger.info(f"|HuaweiGranularGen|handle| No date provided, using yesterday: {target_date}")
            self.stdout.write(self.style.NOTICE(f'No date provided, using yesterday: {target_date}'))

        date_obj = target_date
        collect_time_0 = fetcher.midnight_colombia_timestamp(datetime.combine(date_obj, datetime.min.time()))
        collect_time_1 = fetcher.midnight_colombia_timestamp(datetime.combine(date_obj + timedelta(days=1), datetime.min.time()))

        dev_type_ids = ["1", "38"]
        BATCH_SIZE = 10  # Must match fetcher batch size
        for dev_type_id in dev_type_ids:
            batch_number = 1
            self.stdout.write(self.style.NOTICE(f'Processing dev_type_id {dev_type_id}...'))
            while True:
                retry = False
                for attempt in range(2):  # Allow one retry per batch
                    try:
                        mppt_energy_dict = fetcher.fetch_huawei_generacion_granular_dia(
                            dev_type_id=dev_type_id,
                            batch_number=batch_number,
                            collect_time_0=collect_time_0,
                            collect_time_1=collect_time_1,
                            token=token
                        )
                        break  # Success: exit retry loop
                    except RuntimeError as e:
                        if hasattr(e, 'args') and len(e.args) > 1 and e.args[1] == 305 and not retry:
                            self.stdout.write(self.style.WARNING('Session expired, re-logging in and retrying batch...'))
                            token = fetcher.login()
                            retry = True
                        else:
                            raise
                    except ValueError as ve:
                        if "No devices found for the given dev_type_id and batch number." in str(ve):
                            self.stdout.write(self.style.WARNING(f"No devices found for dev_type_id {dev_type_id} and batch {batch_number}. Ending batch loop."))
                            logger.info(f"|HuaweiGranularGen|handle| No devices found for dev_type_id {dev_type_id} and batch {batch_number}. Ending batch loop.")
                            break  # No more devices to process in this batch
                        else:
                            raise
                num_inverters = len(mppt_energy_dict) if mppt_energy_dict else 0
                logger.info(f"|HuaweiGranularGen|handle| Batch {batch_number} for dev_type_id {dev_type_id}: {num_inverters} inverters processed.")
                self.stdout.write(self.style.SUCCESS(f"Batch {batch_number} for dev_type_id {dev_type_id}: {num_inverters} inverters processed."))
                try:
                    insert_huawei_generacion_granular_dia(mppt_energy_dict, date_obj)
                except Exception as e:
                    print(f"[ERROR] Exception in insert_huawei_generacion_granular_dia: {e}")
                    traceback.print_exc()
                if num_inverters < BATCH_SIZE:
                    self.stdout.write(self.style.NOTICE(f"Last batch for dev_type_id {dev_type_id}. Processed {num_inverters} inverters, which is less than batch size {BATCH_SIZE}. Exiting batch loop."))
                    logger.info(f"|HuaweiGranularGen|handle| Last batch for dev_type_id {dev_type_id}. Processed {num_inverters} inverters, which is less than batch size {BATCH_SIZE}. Exiting batch loop.")
                    break
                batch_number += 1  # Only increment if not breaking

        self.stdout.write(self.style.SUCCESS('All batches processed.')) 