from django.core.management.base import BaseCommand, CommandError
from solarDataFetch.fetchers.hoymilesFetcher import HoymilesFetcher
from solarDataStore.cruds.hoymilesCruds import insert_hoymiles_generacion_inversor_granular_dia
from solarData.models import Inversor
from django.utils import timezone
from datetime import datetime, timedelta
import logging

logger = logging.getLogger('management_commands')

class Command(BaseCommand):
    help = 'Fetch and store Hoymiles inverter and granular production data for a specific date.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--date',
            type=str,
            help='Date to collect data for in YYYY-MM-DD format (defaults to yesterday if not provided)'
        )

    def handle(self, *args, **options):
        logger.info("|HoymilesInverterGranularGen|handle| Starting Hoymiles inverter and granular generation collection")
        
        fetcher = HoymilesFetcher()
        logger.info("|HoymilesInverterGranularGen|handle| Created HoymilesFetcher instance")

        # Handle date parameter
        if options['date']:
            try:
                target_date = datetime.strptime(options['date'], '%Y-%m-%d')
                collect_time = target_date.strftime("%Y-%m-%d")
                logger.info(f"|HoymilesInverterGranularGen|handle| Using provided date: {collect_time}")
                self.stdout.write(self.style.NOTICE(f'Using provided date: {collect_time}'))
            except ValueError:
                raise CommandError('Invalid date format. Please use YYYY-MM-DD format.')
        else:
            # Default to yesterday
            now = timezone.now()
            yesterday = now - timedelta(days=1)
            collect_time = yesterday.strftime("%Y-%m-%d")
            logger.info(f"|HoymilesInverterGranularGen|handle| No date provided, using yesterday: {collect_time}")
            self.stdout.write(self.style.NOTICE(f'No date provided, using yesterday: {collect_time}'))

        logger.info(f"|HoymilesInverterGranularGen|handle| Processing data for date: {collect_time}")

        # Get all Hoymiles inverters from the database
        try:
            hoymiles_inverters = Inversor.objects.filter(
                id_proyecto__marca_inversor__marca='Hoymiles'
            ).select_related('id_proyecto')
            
            total_inverters = hoymiles_inverters.count()
            logger.info(f"|HoymilesInverterGranularGen|handle| Found {total_inverters} Hoymiles inverters to process")
            
            if total_inverters == 0:
                logger.warning("|HoymilesInverterGranularGen|handle| No Hoymiles inverters found in database")
                self.stdout.write(self.style.WARNING('No Hoymiles inverters found in database.'))
                return
                
        except Exception as e:
            logger.error(f"|HoymilesInverterGranularGen|handle| Error fetching Hoymiles inverters: {e}")
            raise CommandError(f'Error fetching Hoymiles inverters: {e}')

        self.stdout.write(self.style.NOTICE(
            f'Found {total_inverters} Hoymiles inverters to process for date: {collect_time}'
        ))

        successful_inverters = 0
        failed_inverters = 0

        # Process each inverter individually
        for inverter in hoymiles_inverters:
            plant_id = inverter.id_proyecto.identificador_planta
            inverter_sn = inverter.identificador_inversor
            project_name = inverter.id_proyecto.dealname
            
            logger.info(f"|HoymilesInverterGranularGen|handle| Processing inverter {inverter_sn} from project {project_name} (Plant ID: {plant_id})")
            
            try:
                # Fetch inverter and granular data
                inverter_data = fetcher.fetch_hoymiles_generacion_inversor_granular_dia(
                    plant_id, inverter_sn, collect_time
                )
                
                if inverter_data:
                    # Insert data into database
                    insert_hoymiles_generacion_inversor_granular_dia(inverter_data, collect_time)
                    
                    successful_inverters += 1
                    logger.info(f"|HoymilesInverterGranularGen|handle| Successfully processed inverter {inverter_sn}")
                    self.stdout.write(self.style.SUCCESS(f'✓ {project_name} - {inverter_sn}: Data processed successfully'))
                else:
                    failed_inverters += 1
                    logger.warning(f"|HoymilesInverterGranularGen|handle| No data returned for inverter {inverter_sn}")
                    self.stdout.write(self.style.WARNING(f'⚠ {project_name} - {inverter_sn}: No data returned'))
                    
            except RuntimeError as e:
                failed_inverters += 1
                logger.error(f"|HoymilesInverterGranularGen|handle| Error fetching data for inverter {inverter_sn}: {e}")
                self.stdout.write(self.style.ERROR(f'✗ {project_name} - {inverter_sn}: {e}'))
                continue
            except Exception as e:
                failed_inverters += 1
                logger.error(f"|HoymilesInverterGranularGen|handle| Unexpected error processing inverter {inverter_sn}: {e}")
                self.stdout.write(self.style.ERROR(f'✗ {project_name} - {inverter_sn}: Unexpected error: {e}'))
                continue

        # Summary
        logger.info(f"|HoymilesInverterGranularGen|handle| Hoymiles inverter and granular collection completed. Successful: {successful_inverters}, Failed: {failed_inverters}, Total: {total_inverters}")
        self.stdout.write(self.style.SUCCESS(
            f'Hoymiles inverter and granular data collection completed.\n'
            f'Successful inverters: {successful_inverters}/{total_inverters}\n'
            f'Failed inverters: {failed_inverters}'
        ))
