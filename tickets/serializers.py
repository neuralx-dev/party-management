from rest_framework import serializers
from .models import User, Ticket, TicketType

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name', 'field', 'id_number', 'user_type')

class TicketTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketType
        fields = ('id', 'title')

class TicketSerializer(serializers.ModelSerializer):
    ticket_type = TicketTypeSerializer(read_only=True)
    qr_code_url = serializers.SerializerMethodField()

    class Meta:
        model = Ticket
        fields = ('id', 'ticket_type', 'status', 'created_at', 'qr_code_url')

    def get_qr_code_url(self, obj):
        if obj.qr_code:
            return self.context['request'].build_absolute_uri(obj.qr_code.url)
        return None

class UserTicketsSerializer(serializers.ModelSerializer):
    tickets = TicketSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name', 'tickets')
