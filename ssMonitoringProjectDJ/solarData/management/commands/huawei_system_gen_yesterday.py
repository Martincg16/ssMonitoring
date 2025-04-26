from django.core.management.base import BaseCommand, CommandError
from solarDataFetch.fetchers.huaweiFetcher import HuaweiFetcher
from solarDataStore.cruds.huaweiCruds import insert_huawei_generacion_sistema_dia
from datetime import datetime, timedelta

class Command(BaseCommand):
    help = 'Fetch and store Huawei system production data for yesterday (single batch, <100 systems).'

    def handle(self, *args, **options):
        fetcher = HuaweiFetcher()
        token = fetcher.login()

        # Calculate yesterday's date in local time
        now = datetime.now()
        yesterday_local = now - timedelta(days=1)
        collect_time = fetcher.midnight_gmt5_timestamp(yesterday_local)

        batch_number = 1
        while True:
            retry = False
            for attempt in range(2):  # Allow one retry per batch
                try:
                    system_data = fetcher.fetch_huawei_generacion_sistema_dia(
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
                        raise CommandError(f'Error fetching system data (batch {batch_number}): {e}')
            else:
                raise CommandError(f'Failed after retrying batch {batch_number} due to repeated session expiration.')

            # Insert always happens once per batch
            insert_huawei_generacion_sistema_dia(system_data)
            self.stdout.write(self.style.SUCCESS(
                f'Batch {batch_number}: {len(system_data)} systems processed.'
            ))
            if len(system_data) < 100:
                break
            batch_number += 1
