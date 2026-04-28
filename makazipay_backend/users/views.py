import base64
import json
import calendar
from datetime import date, datetime
import urllib.request
from decimal import Decimal

from django.conf import settings
from django.utils import timezone
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.hashers import make_password
from django.http import JsonResponse, HttpResponse
from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count
from django.db import IntegrityError

# MODELS
from properties.models import Property, Tenant, Payment
from .models import TenantProfile, User


# =========================
# JSON RESPONSE (CORS FIX)
# =========================
def json_response(data, status=200):
    response = JsonResponse(data, status=status)
    response["Access-Control-Allow-Origin"] = "*"
    response["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    response["Access-Control-Allow-Headers"] = "Content-Type"
    return response


# =========================
# SIGNUP (BOTH TENANT & LANDLORD) 🔥
# =========================
def signup(request):
    """
    Handle signup for both tenants and landlords.
    - Tenants: Can create account and login
    - Landlords: Can create account and login
    """
    
    if request.method == "POST":
        full_name = request.POST.get("fullName", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        confirm_password = request.POST.get("confirmPassword", "")
        role = request.POST.get("role", "").strip().lower()
        phone = request.POST.get("phone", "").strip()

        # Validation
        if not all([full_name, email, password, confirm_password, role]):
            messages.error(request, "All fields are required.")
            return render(request, "signup.html")

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, "signup.html")

        if len(password) < 6:
            messages.error(request, "Password must be at least 6 characters.")
            return render(request, "signup.html")

        if role not in ['tenant', 'landlord']:
            messages.error(request, "Invalid role selected.")
            return render(request, "signup.html")

        if User.objects.filter(email__iexact=email).exists():
            messages.error(request, "Email already registered. Please login or use a different email.")
            return render(request, "signup.html")

        # Create user account
        try:
            name_parts = full_name.split(None, 1)
            first_name = name_parts[0]
            last_name = name_parts[1] if len(name_parts) > 1 else ""

            # Create username from email
            username = email.split('@')[0]
            base_username = username
            counter = 1

            # Ensure unique username
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1

            user = User.objects.create_user(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
                phone=phone,
                role=role,
                password=password
            )

            # Create tenant profile if role is tenant
            if role == 'tenant':
                TenantProfile.objects.create(user=user)

            messages.success(request, f"✅ Account created successfully! Please log in.")
            return redirect("login")

        except IntegrityError as e:
            messages.error(request, "Error creating account. Please try again.")
            return render(request, "signup.html")
        except Exception as e:
            messages.error(request, f"Error: {str(e)}")
            return render(request, "signup.html")

    return render(request, "signup.html")


# =========================
# LOGIN (BOTH TENANT & LANDLORD) 🔥
# =========================
def login_view(request):
    """
    Handle login for both tenants and landlords.
    Redirects to appropriate dashboard based on role.
    """

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        if not username or not password:
            return render(request, "login.html", {"error": "Email and password are required."})

        username_for_auth = username
        if "@" in username:
            try:
                user_obj = User.objects.get(email__iexact=username)
                username_for_auth = user_obj.username
            except User.DoesNotExist:
                username_for_auth = username

        user = authenticate(request, username=username_for_auth, password=password)

        if user is not None:
            login(request, user)
            
            # Redirect based on role
            if user.role == "landlord":
                return redirect("/dashboards/landlord/")
            elif user.role == "tenant":
                return redirect("/dashboards/tenant/")
            else:  # admin
                return redirect("/admin/")

        return render(request, "login.html", {"error": "Invalid email or password."})

    return render(request, "login.html")


# =========================
# DASHBOARD REDIRECT
# =========================
def _dashboard_redirect(user):
    if hasattr(user, "role") and user.role == "landlord":
        return redirect("/dashboards/landlord/")
    return redirect("/dashboards/tenant/")


# =========================
# LANDLORD DASHBOARD
# =========================
@login_required
@login_required
def landlord_dashboard(request):
    # Check if user is landlord
    if request.user.role != 'landlord':
        messages.error(request, "Access denied. Landlords only.")
        return redirect("login")

    # Import Complaint model
    from complaints.models import Complaint

    landlord = request.user

    properties = Property.objects.filter(landlord=landlord).annotate(occupied_tenants=Count("tenant"))
    tenants = Tenant.objects.filter(property__landlord=landlord)

    total_properties = properties.count()
    total_tenants = tenants.count()

    upcoming_payments = Payment.objects.filter(
        tenant__property__landlord=landlord,
        paid=False,
        due_date__gte=timezone.now().date()
    ).aggregate(Sum("amount"))["amount__sum"] or 0

    overdue_payments = Payment.objects.filter(
        tenant__property__landlord=landlord,
        paid=False,
        due_date__lt=timezone.now().date()
    ).aggregate(Sum("amount"))["amount__sum"] or 0

    total_collected = Payment.objects.filter(
        tenant__property__landlord=landlord,
        paid=True
    ).aggregate(Sum("amount"))["amount__sum"] or 0

    paid_periods = Payment.objects.filter(
        tenant__property__landlord=landlord,
        paid=True
    ).values_list("due_date__year", "due_date__month").distinct()
    months_paid = paid_periods.count()
    paid_months = [
        f"{calendar.month_name[year]} {month}"
        for year, month in sorted(paid_periods, reverse=True)
    ]

    recent_payments = Payment.objects.filter(
        tenant__property__landlord=landlord
    ).order_by("-due_date")[:5]

    # Get complaint statistics
    open_complaints = Complaint.objects.filter(landlord=landlord, status='open').count()
    total_complaints = Complaint.objects.filter(landlord=landlord).count()

    tenant_items = []
    for tenant in tenants:
        latest_payment = Payment.objects.filter(tenant=tenant).order_by("due_date").first()
        if latest_payment:
            due_date = latest_payment.due_date
            if latest_payment.paid:
                status = "paid"
            elif due_date < timezone.now().date():
                status = "overdue"
            else:
                status = "pending"
        else:
            due_date = None
            status = "no payments"

        tenant_items.append({
            "tenant": tenant,
            "due_date": due_date,
            "status": status,
        })

    context = {
        "properties": properties,
        "tenant_items": tenant_items,
        "total_properties": total_properties,
        "total_tenants": total_tenants,
        "upcoming_payments": upcoming_payments,
        "overdue_payments": overdue_payments,
        "total_collected": total_collected,
        "months_paid": months_paid,
        "paid_months": paid_months,
        "recent_payments": recent_payments,
        "open_complaints": open_complaints,
        "total_complaints": total_complaints,
    }

    return render(request, "dashboards/landlord.html", context)


# =========================
# ADD PROPERTY
# =========================
@login_required
def add_property(request):
    if request.user.role != 'landlord':
        messages.error(request, "Access denied. Landlords only.")
        return redirect("login")

    if request.method == "POST":
        name = request.POST.get("name")
        address = request.POST.get("address")
        total_units = request.POST.get("total_units")

        if not name or not address or not total_units:
            messages.error(request, "All fields are required.")
            return redirect("add_property")

        Property.objects.create(
            landlord=request.user,
            name=name,
            address=address,
            total_units=total_units
        )

        messages.success(request, f"✅ Property '{name}' added successfully!")
        return redirect("/dashboards/landlord/")

    return render(request, "dashboards/add_property.html")


# =========================
# EDIT PROPERTY
@login_required
def edit_property(request, property_id):
    if request.user.role != 'landlord':
        messages.error(request, "Access denied. Landlords only.")
        return redirect("login")

    try:
        property_obj = Property.objects.get(id=property_id, landlord=request.user)
    except Property.DoesNotExist:
        messages.error(request, "Property not found or you don't have permission.")
        return redirect("landlord_dashboard")

    if request.method == "POST":
        name = request.POST.get("name")
        address = request.POST.get("address")
        total_units = request.POST.get("total_units")

        if not name or not address or not total_units:
            messages.error(request, "All fields are required.")
            return redirect("edit_property", property_id=property_id)

        property_obj.name = name
        property_obj.address = address
        property_obj.total_units = total_units
        property_obj.save()

        messages.success(request, f"✅ Property '{name}' updated successfully!")
        return redirect("landlord_dashboard")

    return render(request, "dashboards/add_property.html", {"property": property_obj})


# =========================
# DELETE PROPERTY
@login_required
def delete_property(request, property_id):
    if request.user.role != 'landlord':
        messages.error(request, "Access denied. Landlords only.")
        return redirect("login")

    try:
        property_obj = Property.objects.get(id=property_id, landlord=request.user)
    except Property.DoesNotExist:
        messages.error(request, "Property not found or you don't have permission.")
        return redirect("landlord_dashboard")

    if request.method == "POST":
        property_obj.delete()
        messages.success(request, f"✅ Property '{property_obj.name}' deleted successfully.")
        return redirect("landlord_dashboard")

    return redirect("landlord_dashboard")


# =========================
# ADD TENANT (EMAIL-BASED LINKING 🔥 UPDATED)
# =========================
@login_required
def add_tenant(request):
    """
    Landlord links an existing tenant to an apartment.
    Tenant must have registered first using their email.
    """
    if request.user.role != 'landlord':
        messages.error(request, "Access denied. Landlords only.")
        return redirect("login")

    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        unit = request.POST.get("unit", "").strip()
        property_id = request.POST.get("property", "").strip()
        rent = request.POST.get("rent", "").strip()

        # Validation
        if not all([email, unit, property_id, rent]):
            messages.error(request, "All fields are required.")
            return redirect("add_tenant")

        # Verify property ownership
        try:
            property_obj = Property.objects.get(id=property_id, landlord=request.user)
        except Property.DoesNotExist:
            messages.error(request, "Property not found or you don't have permission.")
            return redirect("add_tenant")

        # Find user by email
        user_obj = User.objects.filter(email__iexact=email).first()
        if not user_obj:
            messages.error(request, 
                f"❌ No account found with email '{email}'. Please ask the tenant to sign up first at /signup/")
            return redirect("add_tenant")

        if user_obj.role != 'tenant':
            messages.error(request,
                f"❌ The account with email '{email}' is registered as '{user_obj.role}'. "
                f"Please ask them to register as a Tenant or update their account role.")
            return redirect("add_tenant")

        # Ensure tenant profile exists for this tenant account
        if not hasattr(user_obj, 'tenant_profile'):
            TenantProfile.objects.create(user=user_obj)

        # Check if already linked to this property
        if Tenant.objects.filter(user=user_obj, property=property_obj).exists():
            messages.warning(request, f"{email} is already linked to this property.")
            return redirect("add_tenant")

        # Create tenant record
        try:
            tenant = Tenant.objects.create(
                user=user_obj,
                name=f"{user_obj.first_name} {user_obj.last_name}".strip() or user_obj.email,
                property=property_obj,
                unit=unit,
                rent=rent,
            )

            messages.success(request, f"✅ Tenant '{user_obj.email}' linked to {property_obj.name} successfully!")
            return redirect("landlord_dashboard")

        except IntegrityError:
            messages.error(request, f"❌ Error: Tenant is already linked to this property.")
            return redirect("add_tenant")
        except Exception as e:
            messages.error(request, f"Error adding tenant: {str(e)}")
            return redirect("add_tenant")

    # GET request - display form
    properties = Property.objects.filter(landlord=request.user)

    context = {
        "properties": properties,
    }

    return render(request, "dashboards/add_tenant.html", context)


# =========================
# EDIT TENANT
@login_required
def edit_tenant(request, tenant_id):
    if request.user.role != 'landlord':
        messages.error(request, "Access denied. Landlords only.")
        return redirect("login")

    try:
        tenant = Tenant.objects.get(id=tenant_id, property__landlord=request.user)
    except Tenant.DoesNotExist:
        messages.error(request, "Tenant not found or you don't have permission.")
        return redirect("landlord_dashboard")

    if request.method == "POST":
        property_id = request.POST.get("property")
        unit = request.POST.get("unit", "").strip()
        rent = request.POST.get("rent", "").strip()

        if not property_id or not unit or not rent:
            messages.error(request, "All fields are required.")
            return redirect("edit_tenant", tenant_id=tenant_id)

        try:
            property_obj = Property.objects.get(id=property_id, landlord=request.user)
        except Property.DoesNotExist:
            messages.error(request, "Property not found or you don't have permission.")
            return redirect("edit_tenant", tenant_id=tenant_id)

        tenant.property = property_obj
        tenant.unit = unit
        tenant.rent = rent
        tenant.save()

        messages.success(request, f"✅ Tenant '{tenant.name}' updated successfully!")
        return redirect("landlord_dashboard")

    properties = Property.objects.filter(landlord=request.user)
    return render(request, "dashboards/add_tenant.html", {
        "tenant": tenant,
        "properties": properties,
    })


# =========================
# REMOVE TENANT 🔥 UPDATED
# =========================
@login_required
def remove_tenant(request, tenant_id):
    """
    Landlord removes a tenant from a specific property.
    This allows the tenant to be linked to another landlord's property.
    """
    if request.user.role != 'landlord':
        messages.error(request, "Access denied.")
        return redirect("login")

    try:
        tenant = Tenant.objects.get(id=tenant_id, property__landlord=request.user)
    except Tenant.DoesNotExist:
        messages.error(request, "Tenant not found or you don't have permission.")
        return redirect("landlord_dashboard")

    tenant_email = tenant.user.email if tenant.user else tenant.name
    tenant_name = tenant.name
    tenant.delete()

    messages.success(request, f"✅ Tenant '{tenant_name}' has been removed from this property.")
    return redirect("landlord_dashboard")


# =========================
# TENANT DASHBOARD (SHOWS ONLY LINKED APARTMENTS 🔥 UPDATED)
# =========================
@login_required
def tenant_dashboard(request):
    """
    Tenant can see all apartments/properties they are linked to.
    """
    
    if request.user.role != 'tenant':
        messages.error(request, "Access denied. Tenants only.")
        return redirect("login")

    # Get all apartments linked to this tenant
    tenant_apartments = Tenant.objects.filter(user=request.user)

    if not tenant_apartments.exists():
        context = {
            "apartments": [],
            "payments": [],
            "total_paid": 0,
            "total_due": 0,
            "overdue_amount": 0,
            "latest_payment": None,
            "today": date.today(),
            "message": "You haven't been linked to any apartment yet. Contact your landlord."
        }
        return render(request, "dashboards/tenant.html", context)

    # Ensure a current monthly invoice exists for each apartment
    today = date.today()
    for tenant_apartment in tenant_apartments:
        current_month_payment = Payment.objects.filter(
            tenant=tenant_apartment,
            due_date__year=today.year,
            due_date__month=today.month
        ).first()

        if not current_month_payment:
            due_date = date(today.year, today.month, 1)
            Payment.objects.create(
                tenant=tenant_apartment,
                amount=tenant_apartment.rent,
                due_date=due_date,
                paid=False
            )

    # Create any missing monthly invoices from the earliest recorded payment through this month.
    def add_month(year_value, month_value, increment=1):
        month_value += increment
        year_value += (month_value - 1) // 12
        month_value = ((month_value - 1) % 12) + 1
        return year_value, month_value

    for tenant_apartment in tenant_apartments:
        apartment_payments = Payment.objects.filter(tenant=tenant_apartment)
        existing_months = {(p.due_date.year, p.due_date.month) for p in apartment_payments}

        if apartment_payments.exists():
            earliest_due = min(p.due_date for p in apartment_payments)
            start_year, start_month = earliest_due.year, earliest_due.month
        else:
            start_year, start_month = today.year, today.month

        current_year, current_month = start_year, start_month
        while current_year < today.year or (current_year == today.year and current_month <= today.month):
            if (current_year, current_month) not in existing_months:
                Payment.objects.create(
                    tenant=tenant_apartment,
                    amount=tenant_apartment.rent,
                    due_date=date(current_year, current_month, 1),
                    paid=False,
                )
                existing_months.add((current_year, current_month))

            current_year, current_month = add_month(current_year, current_month, 1)

    payments = Payment.objects.filter(tenant__in=tenant_apartments).order_by("-due_date")

    total_paid = payments.filter(paid=True).aggregate(Sum("amount"))["amount__sum"] or 0
    total_due = payments.filter(paid=False).aggregate(Sum("amount"))["amount__sum"] or 0

    overdue_payments = payments.filter(
        paid=False,
        due_date__lt=today
    )

    overdue_amount = overdue_payments.aggregate(Sum("amount"))["amount__sum"] or 0
    next_due_payment = payments.filter(paid=False).order_by("due_date").first()

    apartment_rows = []
    current_month_payments = []
    for tenant_apartment in tenant_apartments:
        current_payment = Payment.objects.filter(
            tenant=tenant_apartment,
            due_date__year=today.year,
            due_date__month=today.month,
            paid=False
        ).first()

        apartment_rows.append({
            "apartment": tenant_apartment,
            "next_due_payment": payments.filter(tenant=tenant_apartment, paid=False).order_by("due_date").first(),
            "current_month_payment": current_payment,
        })

        if current_payment:
            current_month_payments.append({
                "apartment": tenant_apartment,
                "payment": current_payment,
            })

    rent_cycle = []
    months_to_show = 12
    for i in range(months_to_show - 1, -1, -1):
        year_value = today.year
        month_value = today.month - i
        while month_value <= 0:
            month_value += 12
            year_value -= 1

        due_date = date(year_value, month_value, 1)
        month_payments = payments.filter(due_date__year=year_value, due_date__month=month_value)
        month_total = month_payments.aggregate(Sum("amount"))["amount__sum"] or 0

        if month_payments.exists():
            if month_payments.filter(paid=False).exists():
                status = "Overdue" if due_date < today else "Pending"
            else:
                status = "Paid"
        else:
            status = "No Invoice"

        rent_cycle.append({
            "label": f"{calendar.month_abbr[month_value]} {year_value}",
            "status": status,
            "amount": month_total,
            "due_date": due_date,
        })

    context = {
        "apartments": tenant_apartments,
        "apartment_rows": apartment_rows,
        "current_month_payments": current_month_payments,
        "payments": payments,
        "total_paid": total_paid,
        "total_due": total_due,
        "overdue_amount": overdue_amount,
        "next_due_payment": next_due_payment,
        "rent_cycle": rent_cycle,
        "today": today,
    }

    return render(request, "dashboards/tenant.html", context)


# =========================
# LANDLORD PROFILE
@login_required
def landlord_profile(request):
    if request.user.role != 'landlord':
        messages.error(request, "Access denied. Landlords only.")
        return redirect("login")

    if request.method == "POST":
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        email = request.POST.get("email", "").strip()
        phone = request.POST.get("phone", "").strip()
        profile_picture = request.FILES.get("profile_picture")

        if not first_name or not email:
            messages.error(request, "First name and email are required.")
            return redirect("landlord_profile")

        if User.objects.filter(email__iexact=email).exclude(id=request.user.id).exists():
            messages.error(request, "Another account already uses that email.")
            return redirect("landlord_profile")

        request.user.first_name = first_name
        request.user.last_name = last_name
        request.user.email = email
        request.user.phone = phone
        
        # Handle profile picture upload
        if profile_picture:
            # Delete old profile picture if exists
            if request.user.profile_picture:
                try:
                    request.user.profile_picture.delete()
                except:
                    pass
            request.user.profile_picture = profile_picture
        
        request.user.save()

        messages.success(request, "✅ Profile updated successfully.")
        return redirect("landlord_profile")

    return render(request, "dashboards/landlord_profile.html")


# =========================
# TENANT PROFILE
@login_required
def tenant_profile(request):
    if request.user.role != 'tenant':
        messages.error(request, "Access denied. Tenants only.")
        return redirect("login")

    if request.method == "POST":
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        phone = request.POST.get("phone", "").strip()
        profile_picture = request.FILES.get("profile_picture")

        if not first_name:
            messages.error(request, "First name is required.")
            return redirect("tenant_profile")

        request.user.first_name = first_name
        request.user.last_name = last_name
        request.user.phone = phone
        
        # Handle profile picture upload
        if profile_picture:
            # Delete old profile picture if exists
            if request.user.profile_picture:
                try:
                    request.user.profile_picture.delete()
                except:
                    pass
            request.user.profile_picture = profile_picture
        
        request.user.save()

        messages.success(request, "✅ Profile updated successfully.")
        return redirect("tenant_profile")

    return render(request, "dashboards/tenant_profile.html")


# =========================
# MPESA HELPERS

def is_mpesa_configured():
    """Check if M-Pesa credentials are properly configured"""
    consumer_key = getattr(settings, "MPESA_CONSUMER_KEY", "")
    consumer_secret = getattr(settings, "MPESA_CONSUMER_SECRET", "")
    shortcode = getattr(settings, "MPESA_SHORTCODE", "")
    passkey = getattr(settings, "MPESA_PASSKEY", "")
    
    # Check if using placeholder values
    if (consumer_key == "your-consumer-key" or 
        consumer_secret == "your-consumer-secret" or
        passkey == "your-passkey" or
        not consumer_key or not consumer_secret or
        not shortcode or not passkey):
        return False
    return True


def get_mpesa_access_token():
    consumer_key = getattr(settings, "MPESA_CONSUMER_KEY", "")
    consumer_secret = getattr(settings, "MPESA_CONSUMER_SECRET", "")
    env = getattr(settings, "MPESA_ENV", "sandbox")

    if not consumer_key or not consumer_secret:
        raise ValueError("MPESA_CONSUMER_KEY and MPESA_CONSUMER_SECRET must be set in settings.")

    oauth_url = (
        "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
        if env == "sandbox"
        else "https://api.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
    )

    auth_str = f"{consumer_key}:{consumer_secret}"
    encoded_auth = base64.b64encode(auth_str.encode()).decode()

    req = urllib.request.Request(
        oauth_url,
        headers={
            "Authorization": f"Basic {encoded_auth}",
            "Content-Type": "application/json",
        },
    )

    with urllib.request.urlopen(req, timeout=30) as resp:
        body = resp.read().decode()
        data = json.loads(body)

    return data.get("access_token")


def send_mpesa_stk_push(phone, amount):
    shortcode = getattr(settings, "MPESA_SHORTCODE", "")
    passkey = getattr(settings, "MPESA_PASSKEY", "")
    callback_url = getattr(settings, "MPESA_CALLBACK_URL", "https://example.com/mpesa/callback/")
    env = getattr(settings, "MPESA_ENV", "sandbox")

    if not shortcode or not passkey:
        raise ValueError("MPESA_SHORTCODE and MPESA_PASSKEY must be set in settings.")

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    password = base64.b64encode(f"{shortcode}{passkey}{timestamp}".encode()).decode()

    stk_url = (
        "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
        if env == "sandbox"
        else "https://api.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
    )

    payload = {
        "BusinessShortCode": shortcode,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": str(amount),
        "PartyA": phone,
        "PartyB": shortcode,
        "PhoneNumber": phone,
        "CallBackURL": callback_url,
        "AccountReference": "MakaziPAY Rent",
        "TransactionDesc": "Rent payment via STK Push",
    }

    access_token = get_mpesa_access_token()
    if not access_token:
        raise ValueError("Failed to obtain M-Pesa access token.")

    req = urllib.request.Request(
        stk_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        },
    )

    with urllib.request.urlopen(req, timeout=30) as resp:
        body = resp.read().decode()
        return json.loads(body)


# =========================
# MPESA PAYMENT
# =========================
@login_required
def mpesa_pay(request):
    if request.method != "POST":
        return HttpResponse("Invalid request")

    phone = request.POST.get("phone", "").strip() or request.user.phone
    amount = request.POST.get("amount", "").strip()
    payment_id = request.POST.get("payment_id", "").strip()

    # Debug: Log the received data
    print(f"DEBUG mpesa_pay: phone={phone}, amount={amount}, payment_id={payment_id}")
    print(f"DEBUG mpesa_pay: user={request.user}, user.phone={request.user.phone}")

    if not phone:
        messages.error(request, "Phone number is required for M-Pesa payment.")
        return redirect("tenant_dashboard")

    if not amount:
        messages.error(request, "Payment amount is required.")
        return redirect("tenant_dashboard")

    try:
        amount_value = Decimal(amount)
        if amount_value <= 0:
            raise ValueError("Invalid amount")
    except Exception:
        messages.error(request, "Invalid payment amount.")
        return redirect("tenant_dashboard")

    if phone.startswith("0"):
        phone = "254" + phone[1:]

    # Check if M-Pesa is properly configured
    if not is_mpesa_configured():
        # Test mode: allow recording payment without actual M-Pesa call
        test_mode = getattr(settings, "MPESA_TEST_MODE", False)
        
        print(f"DEBUG: is_mpesa_configured={is_mpesa_configured()}, test_mode={test_mode}, payment_id={payment_id}")
        
        if test_mode and payment_id:
            try:
                # Try to find the payment
                payment = Payment.objects.get(id=payment_id, tenant__user=request.user)
                print(f"DEBUG: Found payment: {payment}")
                payment.paid = True
                payment.payment_date = timezone.now()
                payment.save()
                messages.success(request, f"✅ Test payment recorded: Ksh {amount} paid successfully!")
            except Payment.DoesNotExist:
                print(f"DEBUG: Payment not found for id={payment_id}")
                messages.error(request, "Payment record not found.")
            except Exception as e:
                print(f"DEBUG: Error: {e}")
                messages.error(request, f"Error processing payment: {e}")
        elif test_mode:
            # Just show success message in test mode
            messages.warning(request, f"⚠️ Test Mode: Payment of Ksh {amount} would be sent to {phone}. Configure real M-Pesa credentials for actual payments.")
        else:
            messages.error(request, "⚠️ M-Pesa payment is not configured. Please contact the administrator to set up M-Pesa STK Push credentials.")
        return redirect("tenant_dashboard")

    try:
        result = send_mpesa_stk_push(phone, amount_value)
        
        # Check the response from M-Pesa
        if result.get("ResponseCode") == "0":
            # Store the checkout request ID for callback tracking
            checkout_id = result.get("CheckoutRequestID", "")
            messages.success(request, f"✅ M-Pesa STK Push sent to {phone}. Please enter your PIN on your phone to complete payment.")
        else:
            error_message = result.get("errorMessage", "Unknown error from M-Pesa")
            messages.error(request, f"M-Pesa error: {error_message}")
    except Exception as e:
        # Provide more helpful error message
        error_str = str(e)
        if "authentication" in error_str.lower() or "unauthorized" in error_str.lower():
            messages.error(request, "❌ M-Pesa authentication failed. Please contact the administrator.")
        elif "connection" in error_str.lower() or "timeout" in error_str.lower():
            messages.error(request, "❌ Could not connect to M-Pesa. Please try again later.")
        else:
            messages.error(request, f"❌ Payment request failed: {e}")

    return redirect("tenant_dashboard")


# =========================
# LOGOUT
# =========================
def logout_view(request):
    logout(request)
    return redirect("/")