from django.core.management.base import BaseCommand, CommandError
from solarDataFetch.fetchers.huaweiFetcher import HuaweiFetcher
from solarDataNewSystem.register.huaweiRegister import auto_register_huawei_systems
import logging

logger = logging.getLogger('management_commands')

class Command(BaseCommand):
    help = 'Auto-register new solar systems from all brands (currently Huawei only)'

    def handle(self, *args, **options):
        logger.info("|SystemAutoRegister|handle| Starting system auto-registration")
        self.stdout.write(self.style.NOTICE('>> Starting system auto-registration...'))
        
        # --- Huawei Auto-Registration ---
        self.stdout.write(self.style.NOTICE('\n>> Processing Huawei systems...'))
        
        try:
            fetcher = HuaweiFetcher()
            token = fetcher.login()
            logger.info("|SystemAutoRegister|handle| Huawei login successful")
            
            # Attempt auto-registration with retry for 305 error
            retry = False
            for attempt in range(2):  # Allow one retry
                try:
                    results = auto_register_huawei_systems(token)
                    break  # Success: exit retry loop
                    
                except RuntimeError as e:
                    # Check if it's a 305 (USER_MUST_RELOGIN) error
                    if hasattr(e, 'args') and len(e.args) > 1 and e.args[1] == 305 and not retry:
                        logger.warning("|SystemAutoRegister|handle| Huawei session expired (305), re-logging in and retrying")
                        self.stdout.write(self.style.WARNING('⚠️  Session expired, re-logging in and retrying...'))
                        token = fetcher.login()
                        retry = True
                    else:
                        # Different error or retry already attempted
                        raise
            
            # Display results
            self.stdout.write(self.style.SUCCESS(f'\n✅ Huawei Auto-Registration Complete:'))
            self.stdout.write(f'   📊 Total Huawei stations: {results["total_huawei_stations"]}')
            self.stdout.write(f'   🆕 New stations found: {results["new_stations_found"]}')
            self.stdout.write(f'   ✅ Projects created: {len(results["projects_created"])}')
            self.stdout.write(f'   🔌 Projects with inverters: {len(results["inverters_registered"])}')
            
            # Show created projects
            if results['projects_created']:
                self.stdout.write(self.style.SUCCESS('\n📝 New projects created:'))
                for proyecto in results['projects_created']:
                    inverter_count = len(results['inverters_registered'].get(proyecto.identificador_planta, []))
                    self.stdout.write(f'   • {proyecto.dealname} ({proyecto.identificador_planta}) - {inverter_count} inverters')
            
            # Show errors if any
            if results['errors']:
                self.stdout.write(self.style.WARNING(f'\n⚠️  Errors encountered: {len(results["errors"])}'))
                for error in results['errors']:
                    self.stdout.write(self.style.ERROR(f'   ❌ {error}'))
            
            logger.info(f"|SystemAutoRegister|handle| Huawei auto-registration completed: {len(results['projects_created'])} projects created")
            
        except Exception as e:
            logger.error(f"|SystemAutoRegister|handle| Huawei auto-registration failed: {e}")
            self.stdout.write(self.style.ERROR(f'\n❌ Huawei auto-registration failed: {e}'))
            raise CommandError(f'Huawei auto-registration failed: {e}')
        
        # --- Future: Solis Auto-Registration ---
        # self.stdout.write(self.style.NOTICE('\n🌞 Processing Solis systems...'))
        # TODO: Add Solis auto-registration here
        
        # --- Future: Hoymiles Auto-Registration ---
        # self.stdout.write(self.style.NOTICE('\n⚡ Processing Hoymiles systems...'))
        # TODO: Add Hoymiles auto-registration here
        
        self.stdout.write(self.style.SUCCESS('\n🎉 System auto-registration completed successfully!'))

