from rest_framework import serializers
from .models import *

class RentSerializer(serializers.ModelSerializer):
    class Meta: 
        model = Tenant
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'address', 'lease_start_date', 'lease_end_date', 'city']

class LandlordSerializer(serializers.ModelSerializer):
    class Meta:
        model = Landlord
        fields = [
            'id',
            'first_name',
            'last_name',
            'email',
            'phone_number',
            'address',
            'is_staff',
            'is_superuser',
            'groups',
            'user_permissions',
        ]

class TenantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenant
        fields = [
            'id',
            'first_name',
            'last_name',
            'email',
            'phone_number',
            'address',
            'leased_property',
            'city',
            'is_staff',
            'is_superuser',
            'groups',
            'user_permissions',
        ]

class PropertySerializer(serializers.ModelSerializer):
    class Meta:
        model = Property
        fields = [
            'id',
            'landlord',
            'property_name',
            'address',
            'bedrooms',
            'rent_amount',
            'lease_start_date',
            'lease_end_date',
            'status',
        ]
