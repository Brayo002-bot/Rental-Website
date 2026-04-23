from django.urls import path
from .views import (
    landlord_dashboard,
    add_property,
    send_reminders,
    generate_report_pdf,
)

urlpatterns = [
    # DASHBOARDS
    path("dashboards/landlord/", landlord_dashboard, name="landlord_dashboard"),

    # PROPERTY
    path("add-property/", add_property, name="add_property"),

    # REMINDERS & REPORTS
    path("send-reminders/", send_reminders, name="send_reminders"),
    path("generate-report-pdf/", generate_report_pdf, name="generate_report_pdf"),
]