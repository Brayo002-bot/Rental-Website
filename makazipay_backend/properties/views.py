from django.shortcuts import render, redirect
from .models import Property, Tenant, Payment
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.utils import timezone
from django.contrib import messages  # for showing success/error messages

@login_required
def landlord_dashboard(request):
    landlord = request.user
    properties = Property.objects.filter(landlord=landlord)
    tenants = Tenant.objects.filter(property__landlord=landlord)

    total_properties = properties.count()
    total_tenants = tenants.count()

    today = timezone.now().date()

    upcoming_payments = Payment.objects.filter(
        tenant__property__landlord=landlord,
        paid=False,
        due_date__gte=today
    ).aggregate(Sum("amount"))["amount__sum"] or 0

    overdue_payments = Payment.objects.filter(
        tenant__property__landlord=landlord,
        paid=False,
        due_date__lt=today
    ).aggregate(Sum("amount"))["amount__sum"] or 0

    context = {
        "total_properties": total_properties,
        "total_tenants": total_tenants,
        "upcoming_payments": upcoming_payments,
        "overdue_payments": overdue_payments,
        "properties": properties,
        "tenants": tenants,
    }

    return render(request, "landlord/dashboard.html", context)


@login_required
def add_property(request):
    if request.method == "POST":
        name = request.POST.get("name")
        address = request.POST.get("address")
        total_units = request.POST.get("total_units")

        if not name or not address or not total_units:
            messages.error(request, "All fields are required.")
            return redirect("add_property")

        # Save property
        Property.objects.create(
            landlord=request.user,
            name=name,
            address=address,
            total_units=int(total_units)
        )

        messages.success(request, f"Property '{name}' added successfully!")
        return redirect("landlord_dashboard")

    return render(request, "dashboards/add_property.html")