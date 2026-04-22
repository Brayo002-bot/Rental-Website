from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL


class Property(models.Model):
    landlord = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    address = models.CharField(max_length=255)
    total_units = models.IntegerField()

    def __str__(self):
        return self.name


class Tenant(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=200)
    property = models.ForeignKey(Property, on_delete=models.CASCADE)
    unit = models.CharField(max_length=20)
    rent = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.name

class Payment(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid = models.BooleanField(default=False)
    due_date = models.DateField()
    payment_date = models.DateTimeField(null=True, blank=True)
    reminder_sent = models.BooleanField(default=False)
    reminder_count = models.IntegerField(default=0)
    last_reminder_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['due_date']
        indexes = [
            models.Index(fields=['tenant', '-due_date']),
            models.Index(fields=['paid', 'due_date']),
        ]

    def __str__(self):
        return f"{self.tenant.name} - Ksh {self.amount} due {self.due_date}"