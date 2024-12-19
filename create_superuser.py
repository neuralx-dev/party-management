import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'check_be.settings')
django.setup()

from tickets.models import User

# Create superuser
User.objects.create_superuser(
    username='admin',
    email='admin@example.com',
    password='admin123',
    family_name='Admin',
    field='Administration',
    id_number='ADMIN001',
    user_type='moderator'
)
