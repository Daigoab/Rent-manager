from django.urls import path
from . import views
urlpatterns = [
     path('', views.index, name='index'),
     path('', views.RentView, name='tenant'), 
     path('', views.register_landlord, name='register landlord'),
     path('', views.TenantRegistrationView, name='register tenant'),
     path('', views.is_property_available, name='check property'),
     path('', views.add_tenant, name='add tenant'),
     path('', views.AddPropertyView, NAME='add property'),
     path('', views.view_property_and_tenants, name='view properties and tenants'),
     path('', views.total_earnings_for_month, name='check total income for month'),
     path('', views.total_earnings_for_year, name='check total income for year'),
     path('', views.monthly_income_graph, name='create monthly income graph'),
     path('', views.yearly_income_graph, name='create yearly income graph')
]