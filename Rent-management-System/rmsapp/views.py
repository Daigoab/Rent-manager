from django.shortcuts import render
from rest_framework import status
from .models import *
from rest_framework.response import Response
from .serializer import *
from rest_framework.generics import ListCreateAPIView, CreateAPIView
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.views import APIView
import plotly.express as px

# Create your views here.
def index(request):
    context = {'message': 'Hello world!'}
    return render(request, 'index.html', context)

#Registration for the landlord and tenant
@api_view(['POST'])
@permission_classes([AllowAny])
def register_landlord(request):
    first_name = request.data.get('first_name')
    second_name = request.data.get('second_name')
    email = request.data.get('email')
    phone_number = request.data.get('phone_number')
    address = request.data.get('address')

    # Validate data
    if not email or not phone_number:
        return JsonResponse({'error': 'Email and phone number are required'}, status=400)

    # Create a new landlord object
    landlord = Landlord(
        first_name=first_name,
        second_name=second_name,
        email=email,
        phone_number=phone_number,
        address=address
    )

    # Save the landlord to the database
    landlord.save()

    # Send confirmation email
    subject = 'Welcome to Quebec Rent Managing System'
    message = f'Thank you for registering, {first_name}! Your account has been created successfully.'
    from_email = settings.DEFAULT_FROM_EMAIL  # Use the default sender email from Django settings

    send_mail(subject, message, from_email, [email])

    return JsonResponse({'message': 'Landlord registered successfully'})

User = get_user_model()

class TenantRegistrationView(CreateAPIView):
    serializer_class = TenantSerializer

    def create(self, request, *args, **kwargs):
        # Extract property_id from the request data
        property_id = request.data.get('property_id')

        # Check if the property with the given ID exists
        try:
            property_instance = Property.objects.get(pk=property_id)
        except Property.DoesNotExist:
            return Response({'error': 'Property not found'}, status=status.HTTP_404_NOT_FOUND)

        # Ensure the property is available (status=True)
        if not property_instance.status:
            return Response({'error': 'Property is not available for leasing'}, status=status.HTTP_400_BAD_REQUEST)

        # Create a new tenant with the leased property
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        # Update the leased_property field for the tenant
        tenant = User.objects.get(email=serializer.data['email'])
        tenant.leased_property = property_instance
        tenant.save()

        # Send confirmation email
        subject = 'Welcome to Quebec Homes LTD'
        message = f'Thank you for registering, {serializer.data["first_name"]}! Your account has been created successfully.'
        from_email = settings.DEFAULT_FROM_EMAIL

        send_mail(subject, message, from_email, [serializer.data['email']])

        # Success message
        success_message = 'Tenant registered successfully. Confirmation email sent.'

        headers = self.get_success_headers(serializer.data)
        return Response({'message': success_message, 'data': serializer.data}, status=status.HTTP_201_CREATED, headers=headers)

class ListView (ListCreateAPIView):
    queryset = Tenant.objects.all()
    serializer_class = TenantSerializer

#Dashboard for authenticated users
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard(request):
    user = request.user
    properties = Property.objects.filter(landlord=user.landlord)
    tenants = Tenant.objects.filter(property__landlord=user.landlord)

    # Serialize data using Django Rest Framework serializers
    property_serializer = PropertySerializer(properties, many=True)
    tenant_serializer = TenantSerializer(tenants, many=True)

    return Response({'properties': property_serializer.data, 'tenants': tenant_serializer.data})

#Check whether property is available
def is_property_available(property_id):
    try:
        property_instance = Property.objects.get(pk=property_id)
    except Property.DoesNotExist:
        return False, Response({'error': 'Property not found'}, status=status.HTTP_404_NOT_FOUND)

    today = datetime.today().date()

    if not property_instance.status:
        return False, Response({'error': 'Property is not available for leasing'}, status=status.HTTP_400_BAD_REQUEST)

    if today < property_instance.lease_start_date:
        return False, Response({'error': 'Lease start date has not started yet'}, status=status.HTTP_400_BAD_REQUEST)

    if not property_instance.is_occupied():
        return True, None
    else:
        return False, Response({'error': 'Property is currently occupied'}, status=status.HTTP_400_BAD_REQUEST)

#Adding tenants
def add_tenant(request):
    # Check if the user has the necessary permission to add tenants
    if not request.user.has_perm('rmsapp.add_tenant'):
        return Response({'error': 'Permission denied'}, status=403)

    # Extract property_id and tenant details from request
    property_id = request.data.get('property_id')
    first_name = request.data.get('first_name')
    last_name = request.data.get('last_name')
    email = request.data.get('email')
    phone_number = request.data.get('phone_number')
    address = request.data.get('address')

    # Validate data
    if not email or not phone_number:
        return Response({'error': 'Email and phone number are required'}, status=400)

    # Check property availability
    is_available, availability_response = is_property_available(property_id)
    if not is_available:
        return availability_response

    # Create a new tenant object
    tenant = Tenant(
        first_name=first_name,
        last_name=last_name,
        email=email,
        phone_number=phone_number,
        address=address
    )

    # Save the tenant to the database
    tenant.save()

    return Response({'message': 'Tenant added successfully'})

#Add property
class AddPropertyView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        # Check if the user has the necessary permission to add properties
        if not request.user.has_perm('rmsapp.can_add_property'):
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

        # Extract property data from request
        property_data = request.data

        # Serialize the data using the PropertySerializer
        serializer = PropertySerializer(data=property_data)

        # Validate and save the property
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#View tenants and properties
def view_property_and_tenants(request, property_id):
    # Check if the user has the necessary permission to view tenants
    if not request.user.has_perm('rmsapp.view_tenants'):
        return Response({'error': 'Permission denied'}, status=403)

    # Retrieve property details
    try:
        property_instance = Property.objects.get(pk=property_id)
    except Property.DoesNotExist:
        return Response({'error': 'Property not found'}, status=404)

    # Serialize property details
    property_serializer = PropertySerializer(property_instance)

    # Retrieve tenants associated with the property
    tenants = Tenant.objects.filter(property=property_instance)

    # Serialize tenant details
    tenant_serializer = TenantSerializer(tenants, many=True)

    # Prepare response data
    response_data = {
        'property': property_serializer.data,
        'tenants': tenant_serializer.data
    }

    return Response(response_data)

#Calculate the total yearly income
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def total_earnings_for_year(request, year):
    """
    Calculate and return the total earnings for a specific year.
    """
    landlord = request.user  # Assuming the authenticated user is a landlord
    total_earnings = landlord.total_earnings_for_year(year)
    
    return JsonResponse({'total_earnings': total_earnings})

#Calculate the total monthly income
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def total_earnings_for_month(request, year, month):
    """
    Calculate and return the total earnings for a specific month.
    """
    landlord = request.user  # Assuming the authenticated user is a landlord
    total_earnings = landlord.total_earnings_for_month(year, month)
    
    return JsonResponse({'total_earnings': total_earnings})

#Graphical progress of monthly income
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def monthly_income_graph(request, year, month):
    """
    Generate and return a bar chart for monthly income.
    """
    landlord = request.user  # Assuming the authenticated user is a landlord
    start_date = f'{year}-{month:02d}-01'
    end_date = f'{year}-{month:02d}-31'
    
    monthly_revenue_data = Revenue.objects.filter(
        landlord=landlord,
        payment_date__range=[start_date, end_date]
    ).values('property__property_name').annotate(total_amount=models.Sum('amount'))

    fig = px.bar(monthly_revenue_data, x='property__property_name', y='total_amount', title=f'Monthly Income - {start_date} to {end_date}')
    
    return JsonResponse({'graph': fig.to_json()})

#Graph for yearly income progress 
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def yearly_income_graph(request, year):
    """
    Generate and return a bar chart for yearly income.
    """
    landlord = request.user  # Assuming the authenticated user is a landlord
    start_date = f'{year}-01-01'
    end_date = f'{year}-12-31'
    
    yearly_revenue_data = Revenue.objects.filter(
        landlord=landlord,
        payment_date__range=[start_date, end_date]
    ).values('property__property_name').annotate(total_amount=models.Sum('amount'))

    fig = px.bar(yearly_revenue_data, x='property__property_name', y='total_amount', title=f'Yearly Income - {start_date} to {end_date}')
    
    return JsonResponse({'graph': fig.to_json()})

# class RentView(APIView):
#     def get(self, request):
#         output = [{
#             "first_name": output.first_name,
#             "last_name": output.last_name,
#             "email": output.email,
#             "phone_number": output.phone_number,
#             "address": output.address,
#             "lease_start_date": output.lease_start_date,
#             "lease_end_date": output.lease_end_date,
#             "city": output.city
                   
#         }for output in Tenant.objects.all()]
#         return Response(output)
        
#     def post(self, request):
#         serializer = RentSerializer(data=request.data)
#         if serializer.is_valid(raise_exception=True):
#             serializer.save()
#             return Response(serializer.data)    