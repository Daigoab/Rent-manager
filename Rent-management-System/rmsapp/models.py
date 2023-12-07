
from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.dispatch import receiver
from django.db.models.signals import post_save
import datetime
from django.contrib.auth.models import AbstractUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone

# Create your models here.

class CustomUserManager(BaseUserManager):
    def create_user(self, first_name, second_name, email, phone_number, password=None, **extra_fields):
        email = self.normalize_email(email)
        user = self.model(first_name=first_name, second_name=second_name, email=email, phone_number=phone_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, phone_number, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, phone_number, password, **extra_fields)

class Landlord(AbstractUser):
    address = models.TextField(blank=True)
    objects = CustomUserManager()

    #Calculate the total earnings per month 
    def total_earnings_for_month(self, year, month):
        """
        Calculate the total earnings for a specific month across all properties and tenants.
        """
        start_date = timezone.datetime(year, month, 1, tzinfo=timezone.utc)
        end_date = start_date.replace(month=start_date.month + 1) if start_date.month < 12 else start_date.replace(year=start_date.year + 1, month=1)
        
        total_earnings = Revenue.objects.filter(
            landlord=self,
            payment_date__gte=start_date,
            payment_date__lt=end_date
        ).aggregate(models.Sum('amount'))['amount__sum'] or 0

        return total_earnings
    
    #Total earnings per month
    def total_earnings_for_month(self, year, month):
        """
        Calculate the total earnings for a specific month across all properties and tenants.
        """
        start_date = timezone.datetime(year, month, 1, tzinfo=timezone.utc)
        end_date = start_date.replace(month=start_date.month + 1) if start_date.month < 12 else start_date.replace(year=start_date.year + 1, month=1)
        
        total_earnings = Revenue.objects.filter(
            landlord=self,
            payment_date__gte=start_date,
            payment_date__lt=end_date
        ).aggregate(models.Sum('amount'))['amount__sum'] or 0

        return total_earnings

    #Total earnings per year
    def total_earnings_for_year(self, year):
        """
        Calculate the total earnings for a specific year across all properties and tenants.
        """
        start_date = timezone.datetime(year, 1, 1, tzinfo=timezone.utc)
        end_date = start_date.replace(year=start_date.year + 1)

        total_earnings = Revenue.objects.filter(
            landlord=self,
            payment_date__gte=start_date,
            payment_date__lt=end_date
        ).aggregate(models.Sum('amount'))['amount__sum'] or 0

        return total_earnings

    #Permissions allowed to the landlord
    class Meta:
        permissions = [
            ("can_add_property", "Can add property"),
            ("can_remove_property", "Can remove property"),
            ("can_view_tenants", "Can view tenants"),
            ("can_add_tenant", "Can add tenant"),
            ("can_remove_tenant", "Can remove tenant"),
        ]

    groups = models.ManyToManyField(
        Group,
        verbose_name='landlord groups',
        blank=True,
        help_text='The groups this landlord belongs to.',
        related_name='landlord_groups',
        related_query_name='landlord',
    )

    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name='landlord user permissions',
        blank=True,
        help_text='Specific permissions for this landlord.',
        related_name='landlord_user_permissions',
        related_query_name='landlord',
    )

    def __str__(self):
        return self.email

class Property(models.Model):
    landlord = models.ForeignKey(Landlord, on_delete=models.CASCADE, default=True)
    property_name = models.CharField(max_length=100)
    address = models.TextField()
    bedrooms = models.PositiveIntegerField()
    rent_amount = models.DecimalField(max_digits=10, decimal_places=2)
    lease_start_date = models.DateTimeField(default='2023-01-01T00:00:00Z')
    lease_end_date = models.DateTimeField(default='2023-01-01T00:00:00Z')
    status = models.BooleanField(default=True)

    #Check whether the property is occupied
    def is_occupied(self):
        """
        Check if the property is currently occupied.
        """
        today = datetime.today().date()
        return (
            self.status and  # Property is marked as available
            today >= self.lease_start_date and  # Lease start date has started
            Tenant.objects.filter(property=self).exists()  # Property has a tenant
        )

    def __str__(self):
        return self.property_name
    
    
    
class Tenant(AbstractUser):
    # Additional fields for Tenant
    phone_number = models.CharField(max_length=15, blank=False)
    address = models.TextField(blank=True)
    leased_property = models.OneToOneField(Property, on_delete=models.SET_NULL, null=True, blank=True)
    city = models.CharField(max_length=50)
    objects = CustomUserManager()

    groups = models.ManyToManyField(
        Group,
        verbose_name='tenant groups',
        blank=True,
        help_text='The groups this tenant belongs to.',
        related_name='tenant_groups',
        related_query_name='tenant',
    )

    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name='tenant user permissions',
        blank=True,
        help_text='Specific permissions for this tenant.',
        related_name='tenant_user_permissions',
        related_query_name='tenant',
    )

    def __str__(self):
        return self.email
    
class Revenue(models.Model):
    landlord = models.ForeignKey(Landlord, on_delete=models.CASCADE)
    property = models.ForeignKey(Property, on_delete=models.CASCADE)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.property.property_name} - {self.payment_date.strftime('%B %Y')} - ${self.amount}"

    class Meta:
        verbose_name_plural = "Revenues"

class RentDue(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    property_name = models.CharField(max_length=100)
    due_date = models.DateField()
    rent_amount = models.DecimalField(max_digits=10, decimal_places=2)
    is_paid = models.BooleanField(default=False)

    def __str__(self):
        return f"Rent Due for {self.property_name} - {self.due_date}"

class Payment(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, default=True)
    property = models.ForeignKey(Property, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField()

    def __str__(self):
        return f"Payment from {self.tenant} for {self.property} - {self.payment_date}"