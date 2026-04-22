from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):

    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('landlord', 'Landlord'),
        ('tenant', 'Tenant'),
    )

    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='tenant')
    phone = models.CharField(max_length=15, blank=True, null=True)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


class TenantProfile(models.Model):
    """
    Tenant profile - created when tenant registers.
    Allows landlord to link tenant to apartments using email.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='tenant_profile')
    id_number = models.CharField(max_length=50, blank=True, null=True, unique=True)
    verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Tenant Profile"
        verbose_name_plural = "Tenant Profiles"

    def __str__(self):
        return f"Tenant: {self.user.email}"