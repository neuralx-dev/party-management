from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.contrib import messages
from rest_framework import viewsets, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
import qrcode
from io import BytesIO
from django.core.files import File
from .models import User, Ticket, TicketType
from .serializers import UserSerializer, TicketSerializer, UserTicketsSerializer
from django.db.models import Q
from django.contrib.sites.models import Site

def is_moderator(user):
    return user.user_type == 'moderator'

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.user_type == 'moderator':
            return User.objects.all()
        return User.objects.filter(id=self.request.user.id)

class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        ticket = serializer.save()
        self.generate_qr_code(ticket)

    def get_queryset(self):
        if self.request.user.user_type == 'moderator':
            return Ticket.objects.all()
        return Ticket.objects.filter(user=self.request.user)

    def generate_qr_code(self, ticket):
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        
        # Get the current request from the context if available
        request = self.context.get('request') if hasattr(self, 'context') else None
        
        if request:
            # Use the current request's host
            domain = request.get_host()
        else:
            # Fallback to the site's domain
            current_site = Site.objects.get_current()
            domain = current_site.domain
        
        # Use HTTP or HTTPS based on the request
        protocol = 'https' if request and request.is_secure() else 'http'
        ticket_url = f'{protocol}://{domain}/moderator/ticket/{ticket.id}/status/'
        
        qr.add_data(ticket_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        blob = BytesIO()
        img.save(blob, 'PNG')
        ticket.qr_code.save(f'ticket_{ticket.id}.png', File(blob), save=True)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def verify_ticket(request):
    ticket_id = request.data.get('ticket_id')
    if not ticket_id:
        return Response({'error': 'Ticket ID is required'}, status=400)
    
    ticket = get_object_or_404(Ticket, id=ticket_id)
    return Response({
        'is_valid': ticket.is_valid,
        'ticket': TicketSerializer(ticket).data
    })

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def get_user_tickets(request):
    id_number = request.data.get('id_number')
    if not id_number:
        return Response({'error': 'ID number is required'}, status=400)
    
    try:
        user = User.objects.get(id_number=id_number)
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=404)
    
    serializer = UserTicketsSerializer(user, context={'request': request})
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def use_ticket(request):
    ticket_id = request.data.get('ticket_id')
    if not ticket_id:
        return Response({'error': 'Ticket ID is required'}, status=400)
    
    try:
        ticket = Ticket.objects.get(id=ticket_id)
        if ticket.status == 'used':
            return Response({'error': 'Ticket has already been used'}, status=400)
        
        ticket.status = 'used'
        ticket.save()
        
        serializer = TicketSerializer(ticket, context={'request': request})
        return Response(serializer.data)
    except Ticket.DoesNotExist:
        return Response({'error': 'Ticket not found'}, status=404)

# Moderator Panel Views
@login_required
@user_passes_test(is_moderator)
def moderator_dashboard(request):
    guests = User.objects.filter(user_type='guest')
    tickets = Ticket.objects.all()
    ticket_types = TicketType.objects.filter(is_active=True)
    
    context = {
        'guests': guests,
        'tickets': tickets,
        'ticket_types': ticket_types,
        'total_guests': guests.count(),
        'valid_tickets': tickets.filter(status='valid').count(),
        'used_tickets': tickets.filter(status='used').count(),
    }
    
    return render(request, 'tickets/moderator_dashboard.html', context)

@login_required
@user_passes_test(is_moderator)
def add_guest(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        field = request.POST.get('field')
        id_number = request.POST.get('id_number')
        
        try:
            # Generate username from first and last name
            base_username = f"{first_name.lower()}.{last_name.lower()}"
            username = base_username
            counter = 1
            
            # If username exists, add a number to it
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
            
            # Create user with random password
            import secrets
            random_password = secrets.token_urlsafe(12)
            
            User.objects.create_user(
                username=username,
                password=random_password,
                first_name=first_name,
                last_name=last_name,
                family_name=last_name,
                field=field,
                id_number=id_number,
                user_type='guest'
            )
            messages.success(request, 'Guest added successfully!')
        except Exception as e:
            messages.error(request, f'Error adding guest: {str(e)}')
        
        return redirect('moderator-dashboard')
    
    return render(request, 'tickets/add_guest.html')

@login_required
@user_passes_test(is_moderator)
def user_detail(request, user_id):
    user = get_object_or_404(User, id=user_id)
    tickets = user.tickets.all()
    ticket_types = TicketType.objects.filter(is_active=True)
    
    if request.method == 'POST':
        if 'add_ticket' in request.POST:
            ticket_type_id = request.POST.get('ticket_type')
            ticket_type = get_object_or_404(TicketType, id=ticket_type_id)
            ticket = Ticket.objects.create(ticket_type=ticket_type, user=user)
            viewset = TicketViewSet()
            viewset.context = {'request': request}
            viewset.generate_qr_code(ticket)
            messages.success(request, 'Ticket added successfully!')
        elif 'delete_ticket' in request.POST:
            ticket_id = request.POST.get('ticket_id')
            Ticket.objects.filter(id=ticket_id, user=user).delete()
            messages.success(request, 'Ticket deleted successfully!')
    
    return render(request, 'tickets/user_detail.html', {
        'user': user,
        'tickets': tickets,
        'ticket_types': ticket_types
    })

@login_required
@user_passes_test(is_moderator)
def delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if user.user_type != 'moderator':
        user.delete()
        messages.success(request, 'User deleted successfully!')
    else:
        messages.error(request, 'Cannot delete moderator users!')
    return redirect('moderator-dashboard')

@login_required
@user_passes_test(is_moderator)
def manage_ticket_types(request):
    if request.method == 'POST':
        if 'add_ticket_type' in request.POST:
            title = request.POST.get('title')
            TicketType.objects.create(title=title)
            messages.success(request, 'Ticket type added successfully!')
        elif 'delete_ticket_type' in request.POST:
            type_id = request.POST.get('type_id')
            TicketType.objects.filter(id=type_id).delete()
            messages.success(request, 'Ticket type deleted successfully!')
    
    ticket_types = TicketType.objects.all()
    return render(request, 'tickets/manage_ticket_types.html', {
        'ticket_types': ticket_types
    })

@login_required
@user_passes_test(is_moderator)
def ticket_status(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)
    
    if request.method == 'POST':
        if ticket.status == 'valid':
            ticket.status = 'used'
            ticket.save()
            messages.success(request, 'Ticket marked as used successfully!')
        else:
            messages.warning(request, 'Ticket has already been used!')
    
    return render(request, 'tickets/ticket_status.html', {
        'ticket': ticket
    })

@login_required
@user_passes_test(is_moderator)
def guest_list(request):
    search_query = request.GET.get('q', '')
    guests = User.objects.filter(user_type='guest')
    
    if search_query:
        guests = guests.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(id_number__icontains=search_query)
        )
    
    return render(request, 'tickets/guest_list.html', {
        'guests': guests,
        'search_query': search_query
    })
