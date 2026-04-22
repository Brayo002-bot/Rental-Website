from django.urls import path
from . import views

urlpatterns = [
    # Tenant complaints
    path('my-complaints/', views.tenant_complaints, name='tenant_complaints'),
    path('file-complaint/', views.file_complaint, name='file_complaint'),
    
    # Complaint details
    path('complaint/<int:complaint_id>/', views.complaint_detail, name='complaint_detail'),
    
    # Landlord complaints
    path('complaints/', views.landlord_complaints, name='landlord_complaints'),
    path('complaint/<int:complaint_id>/respond/', views.respond_complaint, name='respond_complaint'),
]
