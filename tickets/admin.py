from django.contrib import admin
from .models import User, Ticket, TicketType

class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'first_name', 'family_name', 'field', 'id_number', 'user_type')
    list_filter = ('user_type',)
    fieldsets = (
        ('Additional Info', {'fields': ('family_name', 'field', 'id_number', 'user_type')}),
    )
    add_fieldsets = (
        ('Additional Info', {'fields': ('family_name', 'field', 'id_number', 'user_type')}),
    )

@admin.register(TicketType)
class TicketTypeAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('title',)

class TicketAdmin(admin.ModelAdmin):
    list_display = ('ticket_type', 'user', 'created_at', 'status')
    list_filter = ('status', 'ticket_type')
    search_fields = ('user__username', 'ticket_type__title')

admin.site.register(User, CustomUserAdmin)
admin.site.register(Ticket, TicketAdmin)
