from django.urls import path
from .views import (
    landlord_dashboard,
    tenant_dashboard,
    login_view,
    logout_view,
    add_property,
)

urlpatterns = [
    # AUTH
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),

    # DASHBOARDS
    path("dashboards/landlord/", landlord_dashboard, name="landlord_dashboard"),
    path("dashboards/tenant/", tenant_dashboard, name="tenant_dashboard"),

    # PROPERTY
    path("add-property/", add_property, name="add_property"),
]