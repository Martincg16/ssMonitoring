from django.core.management.base import BaseCommand, CommandError
from solarDataFetch.fetchers.hoymilesFetcher import HoymilesFetcher
from solarDataStore.cruds.hoymilesCruds import insert_hoymiles_generacion_sistema_dia
from solarData.models import Proyecto
from django.utils import timezone
from datetime import datetime, timedelta
import logging

logger = logging.getLogger('management_commands')

class Command(BaseCommand):
    help = 'Fetch and store Hoymiles system production data for a specific date.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--date',
            type=str,
            help='Date to collect data for in YYYY-MM-DD format (defaults to yesterday if not provided)'
        )

    def handle(self, *args, **options):
        logger.info("|HoymilesSystemGen|handle| Starting Hoymiles system generation collection")
        
        fetcher = HoymilesFetcher()
        logger.info("|HoymilesSystemGen|handle| Created HoymilesFetcher instance")

        # Handle date parameter
        if options['date']:
            try:
                target_date = datetime.strptime(options['date'], '%Y-%m-%d')
                collect_time = target_date.strftime("%Y-%m-%d")
                logger.info(f"|HoymilesSystemGen|handle| Using provided date: {collect_time}")
                self.stdout.write(self.style.NOTICE(f'Using provided date: {collect_time}'))
            except ValueError:
                raise CommandError('Invalid date format. Please use YYYY-MM-DD format.')
        else:
            # Default to yesterday
            now = timezone.now()
            yesterday = now - timedelta(days=1)
            collect_time = yesterday.strftime("%Y-%m-%d")
            logger.info(f"|HoymilesSystemGen|handle| No date provided, using yesterday: {collect_time}")
            self.stdout.write(self.style.NOTICE(f'No date provided, using yesterday: {collect_time}'))

        logger.info(f"|HoymilesSystemGen|handle| Processing data for date: {collect_time}")

        # Get all Hoymiles projects from the database
        try:
            hoymiles_projects = Proyecto.objects.filter(marca_inversor__marca='Hoymiles')
            total_projects = hoymiles_projects.count()
            logger.info(f"|HoymilesSystemGen|handle| Found {total_projects} Hoymiles projects to process")
            
            if total_projects == 0:
                logger.warning("|HoymilesSystemGen|handle| No Hoymiles projects found in database")
                self.stdout.write(self.style.WARNING('No Hoymiles projects found in database.'))
                return
                
        except Exception as e:
            logger.error(f"|HoymilesSystemGen|handle| Error fetching Hoymiles projects: {e}")
            raise CommandError(f'Error fetching Hoymiles projects: {e}')

        successful_projects = 0
        failed_projects = 0
        all_system_data = []

        # Process each project individually
        for project in hoymiles_projects:
            station_id = project.identificador_planta
            logger.info(f"|HoymilesSystemGen|handle| Processing project {project.dealname} (Station ID: {station_id})")
            
            try:
                # Fetch data for this specific station
                system_data = fetcher.fetch_hoymiles_generacion_sistema_dia(station_id, collect_time)
                
                # Always process the data - even if PVYield is None, we want to record it
                if system_data:
                    all_system_data.extend(system_data)
                    successful_projects += 1
                    
                    # Check if data contains null values
                    has_null_data = any(entry.get('PVYield') is None for entry in system_data)
                    if has_null_data:
                        logger.info(f"|HoymilesSystemGen|handle| Successfully fetched data for station {station_id}: {len(system_data)} entries (with null values)")
                        self.stdout.write(self.style.WARNING(f'⚠ {project.dealname}: {len(system_data)} entries (null data recorded)'))
                    else:
                        logger.info(f"|HoymilesSystemGen|handle| Successfully fetched data for station {station_id}: {len(system_data)} entries")
                        self.stdout.write(self.style.SUCCESS(f'✓ {project.dealname}: {len(system_data)} entries'))
                else:
                    # This should not happen anymore since fetcher always returns data
                    failed_projects += 1
                    logger.warning(f"|HoymilesSystemGen|handle| No data returned for station {station_id}")
                    self.stdout.write(self.style.ERROR(f'✗ {project.dealname}: No data returned'))
                    
            except RuntimeError as e:
                failed_projects += 1
                logger.error(f"|HoymilesSystemGen|handle| Error fetching data for station {station_id}: {e}")
                self.stdout.write(self.style.ERROR(f'✗ {project.dealname}: {e}'))
                continue

        # Insert all collected data into database
        if all_system_data:
            try:
                logger.info(f"|HoymilesSystemGen|handle| Inserting {len(all_system_data)} total system entries into database")
                insert_hoymiles_generacion_sistema_dia(all_system_data)
                logger.info("|HoymilesSystemGen|handle| All system data inserted successfully")
                self.stdout.write(self.style.SUCCESS(f'Database insertion completed: {len(all_system_data)} total entries'))
            except Exception as e:
                logger.error(f"|HoymilesSystemGen|handle| Error inserting system data: {e}")
                raise CommandError(f'Error inserting system data: {e}')
        else:
            logger.warning("|HoymilesSystemGen|handle| No system data to insert")
            self.stdout.write(self.style.WARNING('No system data to insert.'))

        # Summary
        logger.info(f"|HoymilesSystemGen|handle| Hoymiles system generation collection completed. Successful: {successful_projects}, Failed: {failed_projects}, Total: {total_projects}")
        self.stdout.write(self.style.SUCCESS(
            f'Hoymiles system generation data collection completed.\n'
            f'Successful projects: {successful_projects}/{total_projects}\n'
            f'Failed projects: {failed_projects}\n'
            f'Total entries processed: {len(all_system_data)}'
        ))
