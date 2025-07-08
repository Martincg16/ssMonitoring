from django.core.management.base import BaseCommand, CommandError
from solarDataFetch.fetchers.solisFetcher import SolisFetcher
from solarDataStore.cruds.solisCruds import insert_solis_generacion_sistema_dia
from django.utils import timezone
from datetime import datetime, timedelta
import logging

logger = logging.getLogger('management_commands')

class Command(BaseCommand):
    help = 'Fetch and store Solis system production data for a specific date (with batch processing for >100 systems).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--date',
            type=str,
            help='Date to collect data for in YYYY-MM-DD format (defaults to yesterday if not provided)'
        )

    def handle(self, *args, **options):
        logger.info("|SolisSystemGen|handle| Starting Solis system generation collection")
        
        fetcher = SolisFetcher()
        logger.info("|SolisSystemGen|handle| Created SolisFetcher instance")

        # Handle date parameter
        if options['date']:
            try:
                target_date = datetime.strptime(options['date'], '%Y-%m-%d')
                collect_time = target_date.strftime("%Y-%m-%d")
                logger.info(f"|SolisSystemGen|handle| Using provided date: {collect_time}")
                self.stdout.write(self.style.NOTICE(f'Using provided date: {collect_time}'))
            except ValueError:
                raise CommandError('Invalid date format. Please use YYYY-MM-DD format.')
        else:
            # Default to yesterday
            now = timezone.now()
            yesterday = now - timedelta(days=1)
            collect_time = yesterday.strftime("%Y-%m-%d")
            logger.info(f"|SolisSystemGen|handle| No date provided, using yesterday: {collect_time}")
            self.stdout.write(self.style.NOTICE(f'No date provided, using yesterday: {collect_time}'))

        logger.info(f"|SolisSystemGen|handle| Processing data for date: {collect_time}")

        batch_number = 1
        total_systems = 0
        
        while True:
            logger.info(f"|SolisSystemGen|handle| Processing batch {batch_number}")
            self.stdout.write(self.style.NOTICE(f'Processing batch {batch_number}...'))
            
            try:
                system_data = fetcher.fetch_solis_generacion_sistema_dia(
                    batch_number=batch_number,
                    collect_time=collect_time
                )
                logger.info(f"|SolisSystemGen|handle| Batch {batch_number} fetched successfully: {len(system_data) if system_data else 0} systems")
            except RuntimeError as e:
                logger.error(f"|SolisSystemGen|handle| Error fetching system data (batch {batch_number}): {e}")
                raise CommandError(f'Error fetching system data (batch {batch_number}): {e}')

            # Insert data into database
            if system_data:
                try:
                    insert_solis_generacion_sistema_dia(system_data)
                    logger.info(f"|SolisSystemGen|handle| Batch {batch_number} data inserted successfully")
                except Exception as e:
                    logger.error(f"|SolisSystemGen|handle| Error inserting batch {batch_number} data: {e}")
                    raise
                    
                systems_in_batch = len(system_data)
                total_systems += systems_in_batch
                
                self.stdout.write(self.style.SUCCESS(
                    f'Batch {batch_number}: {systems_in_batch} systems processed.'
                ))
                
                # If we got less than 100 systems, this is the last batch
                if systems_in_batch < 100:
                    logger.info(f"|SolisSystemGen|handle| Last batch completed. Total batches: {batch_number}, Total systems: {total_systems}")
                    self.stdout.write(self.style.SUCCESS(
                        f'Last batch completed. Total systems processed: {total_systems}'
                    ))
                    break
            else:
                logger.warning(f"|SolisSystemGen|handle| Batch {batch_number}: No data returned. Stopping.")
                self.stdout.write(self.style.WARNING(
                    f'Batch {batch_number}: No data returned. Stopping.'
                ))
                break
            
            batch_number += 1
            
        logger.info(f"|SolisSystemGen|handle| Solis system generation collection completed successfully. Total batches: {batch_number}, Total systems: {total_systems}")
        self.stdout.write(self.style.SUCCESS(
            f'Solis system generation data collection completed successfully. '
            f'Total batches: {batch_number}, Total systems: {total_systems}'
        )) 