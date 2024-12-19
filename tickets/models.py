from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator

# Create your models here.

class User(AbstractUser):
    USER_TYPE_CHOICES = (
        ('moderator', 'Moderator'),
        ('guest', 'Guest'),
    )
    
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='guest')
    family_name = models.CharField(max_length=100)
    field = models.CharField(max_length=100)
    id_number = models.CharField(max_length=20, unique=True, validators=[
        RegexValidator(regex=r'^\S+$', message='ID number cannot contain spaces')
    ])

    # Fix for reverse accessor clash
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='ticket_user_set',
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='ticket_user_set',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )

    def __str__(self):
        return f"{self.username} ({self.get_user_type_display()})"

class TicketType(models.Model):
    title = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-created_at']

class Ticket(models.Model):
    STATUS_CHOICES = (
        ('valid', 'Valid'),
        ('used', 'Used'),
    )
    
    ticket_type = models.ForeignKey(TicketType, on_delete=models.CASCADE, related_name='tickets', null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tickets')
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='valid')
    qr_code = models.ImageField(upload_to='qr_codes/', blank=True, null=True)

    def __str__(self):
        return f"{self.ticket_type.title if self.ticket_type else 'Unknown'} - {self.user.username}"

    class Meta:
        ordering = ['-created_at']
