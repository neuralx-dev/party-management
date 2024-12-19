from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site

class Command(BaseCommand):
    help = 'Setup the default site domain'

    def add_arguments(self, parser):
        parser.add_argument('domain', type=str, help='The domain name to set')

    def handle(self, *args, **options):
        domain = options['domain']
        site = Site.objects.get(id=1)
        site.domain = domain
        site.name = domain
        site.save()
        self.stdout.write(self.style.SUCCESS(f'Successfully set site domain to {domain}'))
