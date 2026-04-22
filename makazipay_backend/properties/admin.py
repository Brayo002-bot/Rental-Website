from django.contrib import admin
from .models import Property, Tenant, Payment

admin.site.register(Property)
admin.site.register(Tenant)
admin.site.register(Payment)