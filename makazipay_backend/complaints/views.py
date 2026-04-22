from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from datetime import datetime

from properties.models import Tenant
from .models import Complaint, ComplaintAttachment
from .forms import ComplaintForm, LandlordResponseForm


# ================================
# TENANT COMPLAINTS
# ================================

@login_required
def tenant_complaints(request):
    """Display all complaints filed by the tenant"""
    if request.user.role != 'tenant':
        messages.error(request, "Access denied. Tenants only.")
        return redirect('tenant_dashboard')

    # Get all tenants linked to this user
    tenants = Tenant.objects.filter(user=request.user)
    complaints = Complaint.objects.filter(tenant__in=tenants).order_by('-created_at')

    context = {
        'complaints': complaints,
        'total_complaints': complaints.count(),
        'open_complaints': complaints.filter(status='open').count(),
        'resolved_complaints': complaints.filter(status='resolved').count(),
    }

    return render(request, 'dashboards/complaints/tenant_complaints.html', context)


@login_required
def file_complaint(request):
    """File a new complaint"""
    if request.user.role != 'tenant':
        messages.error(request, "Access denied. Tenants only.")
        return redirect('tenant_dashboard')

    # Get tenant's apartments
    tenants = Tenant.objects.filter(user=request.user)
    if not tenants.exists():
        messages.error(request, "No apartments linked to your account.")
        return redirect('tenant_complaints')

    if request.method == 'POST':
        form = ComplaintForm(request.POST)
        tenant_id = request.POST.get('tenant_id')

        try:
            tenant = Tenant.objects.get(id=tenant_id, user=request.user)
        except Tenant.DoesNotExist:
            messages.error(request, "Invalid apartment selected.")
            return redirect('file_complaint')

        if form.is_valid():
            complaint = form.save(commit=False)
            complaint.tenant = tenant
            complaint.landlord = tenant.property.landlord
            complaint.save()

            # Handle attachments
            files = request.FILES.getlist('attachments')
            for file in files:
                ComplaintAttachment.objects.create(complaint=complaint, file=file)

            messages.success(request, "✅ Complaint filed successfully. Your landlord will respond soon.")
            return redirect('complaint_detail', complaint_id=complaint.id)
    else:
        form = ComplaintForm()

    context = {
        'form': form,
        'tenants': tenants,
    }

    return render(request, 'dashboards/complaints/file_complaint.html', context)


@login_required
def complaint_detail(request, complaint_id):
    """View complaint details"""
    complaint = get_object_or_404(Complaint, id=complaint_id)

    # Check permission
    if request.user.role == 'tenant':
        if complaint.tenant.user != request.user:
            messages.error(request, "Access denied.")
            return redirect('tenant_complaints')
    elif request.user.role == 'landlord':
        if complaint.landlord != request.user:
            messages.error(request, "Access denied.")
            return redirect('landlord_complaints')
    else:
        messages.error(request, "Access denied.")
        return redirect('login')

    # Handle landlord response
    if request.method == 'POST' and request.user.role == 'landlord':
        form = LandlordResponseForm(request.POST, instance=complaint)
        if form.is_valid():
            complaint = form.save(commit=False)
            complaint.responded_at = timezone.now()
            if complaint.status == 'resolved':
                complaint.resolved_at = timezone.now()
            complaint.save()
            messages.success(request, "✅ Response sent to tenant.")
            return redirect('complaint_detail', complaint_id=complaint.id)
    else:
        if request.user.role == 'landlord':
            form = LandlordResponseForm(instance=complaint)
        else:
            form = None

    context = {
        'complaint': complaint,
        'form': form,
        'attachments': complaint.attachments.all(),
    }

    return render(request, 'dashboards/complaints/complaint_detail.html', context)


# ================================
# LANDLORD COMPLAINTS
# ================================

@login_required
def landlord_complaints(request):
    """Display all complaints received by the landlord"""
    if request.user.role != 'landlord':
        messages.error(request, "Access denied. Landlords only.")
        return redirect('landlord_dashboard')

    complaints = Complaint.objects.filter(landlord=request.user).order_by('-created_at')
    
    # Filter by status if provided
    status = request.GET.get('status')
    if status and status in ['open', 'in_progress', 'resolved', 'closed']:
        complaints = complaints.filter(status=status)

    context = {
        'complaints': complaints,
        'total_complaints': Complaint.objects.filter(landlord=request.user).count(),
        'open_complaints': Complaint.objects.filter(landlord=request.user, status='open').count(),
        'in_progress_complaints': Complaint.objects.filter(landlord=request.user, status='in_progress').count(),
        'resolved_complaints': Complaint.objects.filter(landlord=request.user, status='resolved').count(),
        'current_status': status,
    }

    return render(request, 'dashboards/complaints/landlord_complaints.html', context)


@login_required
def respond_complaint(request, complaint_id):
    """Respond to a complaint (same as complaint_detail for landlord)"""
    return complaint_detail(request, complaint_id)
