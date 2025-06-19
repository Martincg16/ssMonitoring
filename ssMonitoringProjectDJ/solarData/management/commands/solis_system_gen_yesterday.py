from django.core.management.base import BaseCommand, CommandError
from solarDataFetch.fetchers.solisFetcher import SolisFetcher
from solarDataStore.cruds.solisCruds import insert_solis_generacion_sistema_dia
from datetime import datetime, timedelta

class Command(BaseCommand):
    help = 'Fetch and store Solis system production data for yesterday (with batch processing for >100 systems).'

    def handle(self, *args, **options):
        fetcher = SolisFetcher()

        # Calculate yesterday's date in YYYY-MM-DD format
        now = datetime.now()
        yesterday = now - timedelta(days=1)
        collect_time = yesterday.strftime("%Y-%m-%d")

        batch_number = 1
        total_systems = 0
        
        while True:
            self.stdout.write(self.style.NOTICE(f'Processing batch {batch_number}...'))
            
            try:
                system_data = fetcher.fetch_solis_generacion_sistema_dia(
                    batch_number=batch_number,
                    collect_time=collect_time
                )
            except RuntimeError as e:
                raise CommandError(f'Error fetching system data (batch {batch_number}): {e}')

            # Insert data into database
            if system_data:
                insert_solis_generacion_sistema_dia(system_data)
                systems_in_batch = len(system_data)
                total_systems += systems_in_batch
                
                self.stdout.write(self.style.SUCCESS(
                    f'Batch {batch_number}: {systems_in_batch} systems processed.'
                ))
                
                # If we got less than 100 systems, this is the last batch
                if systems_in_batch < 100:
                    self.stdout.write(self.style.SUCCESS(
                        f'Last batch completed. Total systems processed: {total_systems}'
                    ))
                    break
            else:
                self.stdout.write(self.style.WARNING(
                    f'Batch {batch_number}: No data returned. Stopping.'
                ))
                break
            
            batch_number += 1
            
        self.stdout.write(self.style.SUCCESS(
            f'Solis system generation data collection completed successfully. '
            f'Total batches: {batch_number}, Total systems: {total_systems}'
        )) 