from django.core.management.base import BaseCommand, CommandError
from solarDataFetch.fetchers.solisFetcher import SolisFetcher
from solarDataStore.cruds.solisCruds import insert_solis_generacion_inversor_dia
from solarData.models import Inversor
from django.utils import timezone
from datetime import datetime, timedelta
import time
import logging

logger = logging.getLogger('management_commands')

class Command(BaseCommand):
    help = 'Fetch and store Solis inverter production data for a specific date (one inverter at a time).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--date',
            type=str,
            help='Date to collect data for in YYYY-MM-DD format (defaults to yesterday if not provided)'
        )
        parser.add_argument(
            '--pause',
            type=float,
            default=1.0,
            help='Pause time in seconds between inverter requests (default: 1.0)'
        )

    def handle(self, *args, **options):
        logger.info("|SolisInverterGen|handle| Starting Solis inverter generation collection")
        
        fetcher = SolisFetcher()
        logger.info("|SolisInverterGen|handle| Created SolisFetcher instance")
        
        pause_time = options['pause']
        logger.info(f"|SolisInverterGen|handle| Using pause time: {pause_time} seconds between requests")

        # Handle date parameter
        if options['date']:
            try:
                target_date = datetime.strptime(options['date'], '%Y-%m-%d')
                collect_time = target_date.strftime("%Y-%m-%d")
                logger.info(f"|SolisInverterGen|handle| Using provided date: {collect_time}")
                self.stdout.write(self.style.NOTICE(f'Using provided date: {collect_time}'))
            except ValueError:
                raise CommandError('Invalid date format. Please use YYYY-MM-DD format.')
        else:
            # Default to yesterday
            now = timezone.now()
            yesterday = now - timedelta(days=1)
            collect_time = yesterday.strftime("%Y-%m-%d")
            logger.info(f"|SolisInverterGen|handle| No date provided, using yesterday: {collect_time}")
            self.stdout.write(self.style.NOTICE(f'No date provided, using yesterday: {collect_time}'))

        logger.info(f"|SolisInverterGen|handle| Processing data for date: {collect_time}")

        # Get all Solis inverters (marca_inversor_id = 2)
        solis_inverters = Inversor.objects.filter(
            id_proyecto__marca_inversor_id=2
        ).select_related('id_proyecto')

        total_inverters = solis_inverters.count()
        logger.info(f"|SolisInverterGen|handle| Found {total_inverters} Solis inverters in database")
        
        if total_inverters == 0:
            logger.warning("|SolisInverterGen|handle| No Solis inverters found in database")
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
            
            logger.info(f"|SolisInverterGen|handle| Processing inverter {index}/{total_inverters}: {inverter_id} ({project_name})")
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
                    try:
                        insert_solis_generacion_inversor_dia(inverter_data)
                        successful_count += 1
                        logger.info(f"|SolisInverterGen|handle| Inverter {inverter_id} processed successfully: PVYield = {inverter_data.get('PVYield', 'N/A')} kWh")
                        
                        self.stdout.write(self.style.SUCCESS(
                            f'✅ Inverter {inverter_id}: PVYield = {inverter_data.get("PVYield", "N/A")} kWh'
                        ))
                    except Exception as e:
                        error_count += 1
                        logger.error(f"|SolisInverterGen|handle| Error inserting data for inverter {inverter_id}: {e}")
                        self.stdout.write(self.style.ERROR(
                            f'❌ Error inserting data for inverter {inverter_id}: {e}'
                        ))
                else:
                    logger.warning(f"|SolisInverterGen|handle| Inverter {inverter_id}: No data returned")
                    self.stdout.write(self.style.WARNING(
                        f'⚠️ Inverter {inverter_id}: No data returned'
                    ))

            except RuntimeError as e:
                error_count += 1
                logger.error(f"|SolisInverterGen|handle| RuntimeError processing inverter {inverter_id}: {e}")
                self.stdout.write(self.style.ERROR(
                    f'❌ Error processing inverter {inverter_id}: {e}'
                ))
            except Exception as e:
                error_count += 1
                logger.error(f"|SolisInverterGen|handle| Unexpected error processing inverter {inverter_id}: {e}")
                self.stdout.write(self.style.ERROR(
                    f'❌ Unexpected error processing inverter {inverter_id}: {e}'
                ))

            # Add pause between requests (except for the last one)
            if index < total_inverters and pause_time > 0:
                self.stdout.write(self.style.NOTICE(f'Pausing for {pause_time} seconds...'))
                time.sleep(pause_time)

        # Final summary
        logger.info(f"|SolisInverterGen|handle| Solis inverter generation collection completed. Total: {total_inverters}, Successful: {successful_count}, Errors: {error_count}")
        
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