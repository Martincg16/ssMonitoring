from django.core.management.base import BaseCommand, CommandError
from solarDataFetch.fetchers.solisFetcher import SolisFetcher
from solarDataStore.cruds.solisCruds import insert_solis_generacion_inversor_dia
from solarData.models import Inversor
from datetime import datetime, timedelta
import time

class Command(BaseCommand):
    help = 'Fetch and store Solis inverter production data for yesterday (one inverter at a time).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--pause',
            type=float,
            default=1.0,
            help='Pause time in seconds between inverter requests (default: 1.0)'
        )

    def handle(self, *args, **options):
        fetcher = SolisFetcher()
        pause_time = options['pause']

        # Calculate yesterday's date in YYYY-MM-DD format
        now = datetime.now()
        yesterday = now - timedelta(days=1)
        collect_time = yesterday.strftime("%Y-%m-%d")

        # Get all Solis inverters (marca_inversor_id = 2)
        solis_inverters = Inversor.objects.filter(
            id_proyecto__marca_inversor_id=2
        ).select_related('id_proyecto')

        total_inverters = solis_inverters.count()
        
        if total_inverters == 0:
            self.stdout.write(self.style.WARNING(
                'No Solis inverters found in database. Please run solis registration first.'
            ))
            return

        self.stdout.write(self.style.NOTICE(
            f'Found {total_inverters} Solis inverters to process for date: {collect_time}'
        ))
        self.stdout.write(self.style.NOTICE(
            f'Using pause time: {pause_time} seconds between requests'
        ))

        successful_count = 0
        error_count = 0

        for index, inversor in enumerate(solis_inverters, 1):
            inverter_id = inversor.identificador_inversor
            project_name = inversor.id_proyecto.dealname
            
            self.stdout.write(self.style.NOTICE(
                f'Processing {index}/{total_inverters}: Inverter {inverter_id} ({project_name})'
            ))

            try:
                # Fetch data for this specific inverter
                inverter_data = fetcher.fetch_solis_generacion_un_inversor_dia(
                    inverter_id=inverter_id,
                    collect_time=collect_time
                )

                # Store data in database
                if inverter_data:
                    insert_solis_generacion_inversor_dia(inverter_data)
                    successful_count += 1
                    
                    self.stdout.write(self.style.SUCCESS(
                        f'✅ Inverter {inverter_id}: PVYield = {inverter_data.get("PVYield", "N/A")} kWh'
                    ))
                else:
                    self.stdout.write(self.style.WARNING(
                        f'⚠️ Inverter {inverter_id}: No data returned'
                    ))

            except RuntimeError as e:
                error_count += 1
                self.stdout.write(self.style.ERROR(
                    f'❌ Error processing inverter {inverter_id}: {e}'
                ))
            except Exception as e:
                error_count += 1
                self.stdout.write(self.style.ERROR(
                    f'❌ Unexpected error processing inverter {inverter_id}: {e}'
                ))

            # Add pause between requests (except for the last one)
            if index < total_inverters and pause_time > 0:
                self.stdout.write(self.style.NOTICE(f'Pausing for {pause_time} seconds...'))
                time.sleep(pause_time)

        # Final summary
        self.stdout.write(self.style.SUCCESS(
            f'\n🎯 Solis inverter data collection completed:'
        ))
        self.stdout.write(self.style.SUCCESS(
            f'📊 Total inverters: {total_inverters}'
        ))
        self.stdout.write(self.style.SUCCESS(
            f'✅ Successful: {successful_count}'
        ))
        if error_count > 0:
            self.stdout.write(self.style.ERROR(
                f'❌ Errors: {error_count}'
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                f'❌ Errors: {error_count}'
            )) 