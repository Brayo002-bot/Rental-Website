from django.urls import path, include
from django.shortcuts import redirect, render
from django.conf import settings
from django.conf.urls.static import static
from users.views import (
    tenant_dashboard,
    tenant_profile,
    login_view,
    logout_view,
    signup,
    add_property,
    edit_property,
    delete_property,
    add_tenant,
    edit_tenant,
    remove_tenant,
    landlord_profile,
    mpesa_pay,
)
from properties.views import landlord_dashboard

def home_view(request):
    """
    Homepage - shows landing page for anonymous users,
    redirects to dashboard if logged in
    """
    if request.user.is_authenticated:
        if request.user.role == 'landlord':
            return redirect('landlord_dashboard')
        elif request.user.role == 'tenant':
            return redirect('tenant_dashboard')
        else:
            return redirect('/admin/')
    
    # Show homepage for anonymous users
    return render(request, 'index.html')

urlpatterns = [
    # HOME
    path("", home_view, name="home"),

    # AUTH
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path("signup/", signup, name="signup"),

    # DASHBOARDS
    path("dashboards/landlord/", landlord_dashboard, name="landlord_dashboard"),
    path("dashboards/tenant/", tenant_dashboard, name="tenant_dashboard"),

    # PROPERTY & TENANT
    path("add-property/", add_property, name="add_property"),
    path("edit-property/<int:property_id>/", edit_property, name="edit_property"),
    path("delete-property/<int:property_id>/", delete_property, name="delete_property"),
    path("add-tenant/", add_tenant, name="add_tenant"),
    path("edit-tenant/<int:tenant_id>/", edit_tenant, name="edit_tenant"),
    path("remove-tenant/<int:tenant_id>/", remove_tenant, name="remove_tenant"),
    path("landlord-profile/", landlord_profile, name="landlord_profile"),
    path("tenant-profile/", tenant_profile, name="tenant_profile"),

    # PAYMENTS
    path("mpesa-pay/", mpesa_pay, name="mpesa_pay"),
    
    # PROPERTIES APP
    path("properties/", include("properties.urls")),
    
    # COMPLAINTS
    path("complaints/", include("complaints.urls")),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)