from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'tickets', views.TicketViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
    path('api/verify-ticket/', views.verify_ticket, name='verify-ticket'),
    path('api/user-tickets/', views.get_user_tickets, name='get-user-tickets'),
    path('api/use-ticket/', views.use_ticket, name='use-ticket'),
    path('moderator/', views.moderator_dashboard, name='moderator-dashboard'),
    path('moderator/guests/', views.guest_list, name='guest-list'),
    path('moderator/add-guest/', views.add_guest, name='add-guest'),
    path('moderator/user/<int:user_id>/', views.user_detail, name='user-detail'),
    path('moderator/user/<int:user_id>/delete/', views.delete_user, name='delete-user'),
    path('moderator/ticket-types/', views.manage_ticket_types, name='manage-ticket-types'),
    path('moderator/ticket/<int:ticket_id>/status/', views.ticket_status, name='ticket-status'),
]
