from django.core.management.base import BaseCommand, CommandError
from solarDataFetch.fetchers.huaweiFetcher import HuaweiFetcher
from solarDataNewSystem.register.huaweiRegister import auto_register_huawei_systems
from solarDataNewSystem.register.solisRegister import SolisRegister
from solarDataNewSystem.register.hoymilesRegister import auto_register_hoymiles_systems
import logging

logger = logging.getLogger('management_commands')

class Command(BaseCommand):
    help = 'Auto-register new solar systems and inverters from all brands (Huawei, Solis, Hoymiles)'

    def handle(self, *args, **options):
        logger.info("|SystemAutoRegister|handle| Starting system auto-registration for all brands")
        self.stdout.write(self.style.SUCCESS('Starting system auto-registration...'))
        
        total_projects = 0
        total_inverters = 0
        errors = []
        
        # --- Huawei Auto-Registration ---
        self.stdout.write(self.style.NOTICE('\n[1/2] Processing Huawei systems...'))
        logger.info("|SystemAutoRegister|handle| Starting Huawei auto-registration")
        
        try:
            fetcher = HuaweiFetcher()
            token = fetcher.login()
            logger.info("|SystemAutoRegister|handle| Huawei login successful")
            
            results = auto_register_huawei_systems(token)
            
            self.stdout.write(self.style.SUCCESS('  Huawei registration complete:'))
            self.stdout.write(f'    - Total stations in API: {results["total_huawei_stations"]}')
            self.stdout.write(f'    - New stations found: {results["new_stations_found"]}')
            self.stdout.write(f'    - Projects created: {len(results["projects_created"])}')
            self.stdout.write(f'    - Inverters registered: {len(results["inverters_registered"])}')
            
            if results['projects_created']:
                for proyecto in results['projects_created']:
                    inverter_count = len(results['inverters_registered'].get(proyecto.identificador_planta, []))
                    self.stdout.write(f'      + {proyecto.dealname} ({proyecto.identificador_planta}) - {inverter_count} inverters')
            
            if results['errors']:
                self.stdout.write(self.style.WARNING(f'    - Errors: {len(results["errors"])}'))
                errors.extend([f"Huawei: {e}" for e in results['errors']])
            
            total_projects += len(results['projects_created'])
            total_inverters += len(results['inverters_registered'])
            logger.info(f"|SystemAutoRegister|handle| Huawei completed: {len(results['projects_created'])} projects")
            
        except Exception as e:
            error_msg = f'Huawei auto-registration failed: {e}'
            logger.error(f"|SystemAutoRegister|handle| {error_msg}")
            self.stdout.write(self.style.ERROR(f'  {error_msg}'))
            errors.append(error_msg)
        
        # --- Solis Auto-Registration ---
        self.stdout.write(self.style.NOTICE('\n[2/3] Processing Solis systems...'))
        logger.info("|SystemAutoRegister|handle| Starting Solis auto-registration")
        
        try:
            solis_register = SolisRegister()
            logger.info("|SystemAutoRegister|handle| Solis register initialized")
            
            results = solis_register.solis_register_new_project()
            
            self.stdout.write(self.style.SUCCESS('  Solis registration complete:'))
            self.stdout.write(f'    - Batches processed: {results["batches_processed"]}')
            self.stdout.write(f'    - Projects created: {results["projects_created"]}')
            self.stdout.write(f'    - Inverters created: {results["inverters_created"]}')
            
            total_projects += results['projects_created']
            total_inverters += results['inverters_created']
            logger.info(f"|SystemAutoRegister|handle| Solis completed: {results['projects_created']} projects")
            
        except ValueError as e:
            error_msg = f'Solis configuration error: {e} (check SOLIS_API_SECRET)'
            logger.error(f"|SystemAutoRegister|handle| {error_msg}")
            self.stdout.write(self.style.ERROR(f'  {error_msg}'))
            errors.append(error_msg)
            
        except Exception as e:
            error_msg = f'Solis auto-registration failed: {e}'
            logger.error(f"|SystemAutoRegister|handle| {error_msg}")
            self.stdout.write(self.style.ERROR(f'  {error_msg}'))
            errors.append(error_msg)
        
        # --- Hoymiles Auto-Registration ---
        self.stdout.write(self.style.NOTICE('\n[3/3] Processing Hoymiles systems...'))
        logger.info("|SystemAutoRegister|handle| Starting Hoymiles auto-registration")
        
        try:
            results = auto_register_hoymiles_systems()
            
            self.stdout.write(self.style.SUCCESS('  Hoymiles registration complete:'))
            self.stdout.write(f'    - Total plants in API: {results["total_hoymiles_plants"]}')
            self.stdout.write(f'    - New plants found: {results["new_plants_found"]}')
            self.stdout.write(f'    - Projects created: {len(results["projects_created"])}')
            
            if results['projects_created']:
                for proyecto in results['projects_created']:
                    self.stdout.write(f'      + {proyecto.dealname} ({proyecto.identificador_planta})')
            
            if results['errors']:
                self.stdout.write(self.style.WARNING(f'    - Errors: {len(results["errors"])}'))
                errors.extend([f"Hoymiles: {e}" for e in results['errors']])
            
            total_projects += len(results['projects_created'])
            logger.info(f"|SystemAutoRegister|handle| Hoymiles completed: {len(results['projects_created'])} projects")
            
        except ValueError as e:
            error_msg = f'Hoymiles configuration error: {e} (check HOYMILES_API_KEY)'
            logger.error(f"|SystemAutoRegister|handle| {error_msg}")
            self.stdout.write(self.style.ERROR(f'  {error_msg}'))
            errors.append(error_msg)
            
        except Exception as e:
            error_msg = f'Hoymiles auto-registration failed: {e}'
            logger.error(f"|SystemAutoRegister|handle| {error_msg}")
            self.stdout.write(self.style.ERROR(f'  {error_msg}'))
            errors.append(error_msg)
        
        # --- Summary ---
        self.stdout.write(self.style.SUCCESS('\n' + '='*50))
        self.stdout.write(self.style.SUCCESS('SYSTEM AUTO-REGISTRATION SUMMARY:'))
        self.stdout.write(f'  Total projects created: {total_projects}')
        self.stdout.write(f'  Total inverters registered: {total_inverters}')
        
        if errors:
            self.stdout.write(self.style.WARNING(f'\n  Errors encountered: {len(errors)}'))
            for error in errors:
                self.stdout.write(self.style.ERROR(f'    - {error}'))
        else:
            self.stdout.write(self.style.SUCCESS('\n  No errors - all brands processed successfully!'))
        
        self.stdout.write(self.style.SUCCESS('='*50 + '\n'))
        logger.info(f"|SystemAutoRegister|handle| Command completed: {total_projects} projects, {total_inverters} inverters total")
