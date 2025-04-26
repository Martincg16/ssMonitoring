from django.core.management.base import BaseCommand, CommandError
from solarDataFetch.fetchers.huaweiFetcher import HuaweiFetcher
from solarDataStore.cruds.huaweiCruds import insert_huawei_generacion_inversor_dia
from datetime import datetime, timedelta

class Command(BaseCommand):
    help = 'Fetch and store Huawei inverter production data for yesterday (devTypeId=1, <100 entries).'

    def handle(self, *args, **options):
        fetcher = HuaweiFetcher()
        token = fetcher.login()

        now = datetime.now()
        yesterday_local = now - timedelta(days=1)
        collect_time = fetcher.midnight_gmt5_timestamp(yesterday_local)
        for dev_type_id in ["1", "38"]:
            batch_number = 1
            self.stdout.write(self.style.NOTICE(f'Processing dev_type_id {dev_type_id}...'))
            while True:
                retry = False
                for attempt in range(2):  # Allow one retry per batch
                    try:
                        inverter_data = fetcher.fetch_huawei_generacion_inversor_dia(
                            dev_type_id=dev_type_id,
                            batch_number=batch_number,
                            collect_time=collect_time,
                            token=token
                        )
                        break  # Success: exit retry loop
                    except RuntimeError as e:
                        if hasattr(e, 'args') and len(e.args) > 1 and e.args[1] == 305 and not retry:
                            self.stdout.write(self.style.WARNING('Session expired, re-logging in and retrying batch...'))
                            token = fetcher.login()
                            retry = True
                            continue
                        else:
                            raise CommandError(f'Error fetching inverter data (dev_type_id {dev_type_id}, batch {batch_number}): {e}')
                else:
                    raise CommandError(f'Failed after retrying batch {batch_number} for dev_type_id {dev_type_id} due to repeated session expiration.')

                # Insert always happens once per batch
                insert_huawei_generacion_inversor_dia(inverter_data)
                self.stdout.write(self.style.SUCCESS(
                    f'dev_type_id {dev_type_id} - Batch {batch_number}: {len(inverter_data)} inverters processed.'
                ))
                if len(inverter_data) < 100:
                    break
                batch_number += 1
