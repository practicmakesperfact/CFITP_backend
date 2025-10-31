from django.core.management.base import BaseCommand
from importlib import import_module

class Command(BaseCommand):
    help = 'Seed database by calling the top-level seed.seed() function'

    def handle(self, *args, **options):
        try:
            seed_mod = import_module('seed')  # uses seed.py at project root
            if not hasattr(seed_mod, 'seed'):
                self.stderr.write(self.style.ERROR("seed.py does not define a seed() function"))
                return
            seed_mod.seed()
            self.stdout.write(self.style.SUCCESS('Seeding completed.'))
        except Exception as exc:
            self.stderr.write(self.style.ERROR(f'Seeding failed: {exc}'))
            raise