from django.shortcuts import render, redirect
from .models import Property, Tenant, Payment
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count
from django.utils import timezone
from django.contrib import messages  # for showing success/error messages
from django.http import JsonResponse
from django.core.management import call_command
from django.template.loader import render_to_string
from django.http import HttpResponse
import json
from datetime import datetime, timedelta

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

    # Count of upcoming and overdue payments for reminders
    upcoming_count = Payment.objects.filter(
        tenant__property__landlord=landlord,
        paid=False,
        due_date__gte=today,
        reminder_sent=False
    ).count()

    overdue_count = Payment.objects.filter(
        tenant__property__landlord=landlord,
        paid=False,
        due_date__lt=today
    ).exclude(reminder_sent=True, due_date__lt=today - timedelta(days=1)).count()

    total_collected = Payment.objects.filter(
        tenant__property__landlord=landlord,
        paid=True
    ).aggregate(Sum("amount"))["amount__sum"] or 0

    # Recent payments for activity feed
    recent_payments = Payment.objects.filter(
        tenant__property__landlord=landlord
    ).order_by('-payment_date')[:5]

    # Tenant items with payment status
    tenant_items = []
    for tenant in tenants:
        latest_payment = Payment.objects.filter(tenant=tenant).order_by('-due_date').first()
        if latest_payment:
            if latest_payment.paid:
                status = "paid"
            elif latest_payment.due_date < today:
                status = "overdue"
            else:
                status = "pending"
            due_date = latest_payment.due_date
        else:
            status = "no_payments"
            due_date = None

        tenant_items.append({
            'tenant': tenant,
            'status': status,
            'due_date': due_date
        })

    # Complaints summary
    from complaints.models import Complaint
    total_complaints = Complaint.objects.filter(landlord=landlord).count()
    open_complaints = Complaint.objects.filter(landlord=landlord, status__in=['open', 'in_progress']).count()

    # Payment statistics for charts
    months_paid = Payment.objects.filter(
        tenant__property__landlord=landlord,
        paid=True,
        due_date__year=today.year
    ).count()

    # Monthly payment data for charts
    monthly_data = []
    for i in range(12):
        month_date = today.replace(day=1) - timedelta(days=30*i)
        month_payments = Payment.objects.filter(
            tenant__property__landlord=landlord,
            paid=True,
            payment_date__year=month_date.year,
            payment_date__month=month_date.month
        ).aggregate(Sum("amount"))["amount__sum"] or 0
        monthly_data.append({
            'month': month_date.strftime('%b %Y'),
            'amount': float(month_payments)
        })

    # Property analytics data
    property_analytics = []
    for prop in properties:
        tenant_count = tenants.filter(property=prop).count()
        collected = Payment.objects.filter(
            tenant__property=prop,
            paid=True
        ).aggregate(Sum("amount"))["amount__sum"] or 0
        outstanding = Payment.objects.filter(
            tenant__property=prop,
            paid=False
        ).aggregate(Sum("amount"))["amount__sum"] or 0

        property_analytics.append({
            'property': prop,
            'tenant_count': tenant_count,
            'occupancy_rate': int((tenant_count / prop.total_units) * 100) if prop.total_units > 0 else 0,
            'collected': collected,
            'outstanding': outstanding,
            'performance': 'good' if tenant_count > prop.total_units / 2 else 'poor'
        })

    context = {
        "total_properties": total_properties,
        "total_tenants": total_tenants,
        "upcoming_payments": upcoming_payments,
        "overdue_payments": overdue_payments,
        "upcoming_count": upcoming_count,
        "overdue_count": overdue_count,
        "total_collected": total_collected,
        "properties": properties,
        "tenants": tenants,
        "tenant_items": tenant_items,
        "recent_payments": recent_payments,
        "total_complaints": total_complaints,
        "open_complaints": open_complaints,
        "months_paid": months_paid,
        "monthly_data": json.dumps(monthly_data),
        "property_analytics": property_analytics,
    }

    return render(request, "dashboards/landlord.html", context)


@login_required
def send_reminders(request):
    """AJAX view to send payment reminders manually"""
    if request.method == 'POST':
        try:
            # Run the send_payment_reminders management command
            call_command('send_payment_reminders', days_before=3, verbosity=0)

            # Get reminder statistics
            landlord = request.user
            today = timezone.now().date()

            upcoming_count = Payment.objects.filter(
                tenant__property__landlord=landlord,
                paid=False,
                due_date__gte=today,
                reminder_sent=False
            ).count()

            overdue_count = Payment.objects.filter(
                tenant__property__landlord=landlord,
                paid=False,
                due_date__lt=today
            ).exclude(reminder_sent=True, due_date__lt=today - timedelta(days=1)).count()

            return JsonResponse({
                'success': True,
                'message': f'Successfully sent {upcoming_count + overdue_count} payment reminders',
                'upcoming_sent': upcoming_count,
                'overdue_sent': overdue_count
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error sending reminders: {str(e)}'
            })

    return JsonResponse({'success': False, 'message': 'Invalid request method'})


@login_required
def generate_report_pdf(request):
    """Generate and download PDF report"""
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from io import BytesIO

        landlord = request.user
        today = timezone.now().date()

        # Create PDF buffer
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []

        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=20,
            spaceAfter=30,
            alignment=1  # Center alignment
        )
        story.append(Paragraph(f"MakaziPAY Report - {landlord.get_full_name() or landlord.username}", title_style))
        story.append(Paragraph(f"Generated on: {today.strftime('%B %d, %Y')}", styles['Normal']))
        story.append(Spacer(1, 20))

        # Summary Statistics
        story.append(Paragraph("Summary Statistics", styles['Heading2']))

        properties = Property.objects.filter(landlord=landlord)
        tenants = Tenant.objects.filter(property__landlord=landlord)

        total_collected = Payment.objects.filter(
            tenant__property__landlord=landlord,
            paid=True
        ).aggregate(Sum("amount"))["amount__sum"] or 0

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

        summary_data = [
            ['Metric', 'Value'],
            ['Total Properties', str(properties.count())],
            ['Total Tenants', str(tenants.count())],
            ['Total Collected', f"Ksh {total_collected:,.0f}"],
            ['Upcoming Payments', f"Ksh {upcoming_payments:,.0f}"],
            ['Overdue Payments', f"Ksh {overdue_payments:,.0f}"],
        ]

        summary_table = Table(summary_data)
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 30))

        # Properties Table
        story.append(Paragraph("Properties Overview", styles['Heading2']))

        property_data = [['Property Name', 'Address', 'Total Units', 'Tenants']]
        for prop in properties:
            tenant_count = tenants.filter(property=prop).count()
            property_data.append([
                prop.name,
                prop.address,
                str(prop.total_units),
                str(tenant_count)
            ])

        property_table = Table(property_data)
        property_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(property_table)
        story.append(Spacer(1, 30))

        # Recent Payments
        story.append(Paragraph("Recent Payment Activity", styles['Heading2']))

        recent_payments = Payment.objects.filter(
            tenant__property__landlord=landlord
        ).order_by('-payment_date')[:10]

        payment_data = [['Tenant', 'Property', 'Amount', 'Due Date', 'Status']]
        for payment in recent_payments:
            status = 'Paid' if payment.paid else ('Overdue' if payment.due_date < today else 'Pending')
            payment_data.append([
                payment.tenant.name,
                payment.tenant.property.name,
                f"Ksh {payment.amount:,.0f}",
                payment.due_date.strftime('%Y-%m-%d'),
                status
            ])

        payment_table = Table(payment_data)
        payment_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(payment_table)

        # Build PDF
        doc.build(story)
        buffer.seek(0)

        # Create response
        response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="makazipay_report_{today.strftime("%Y%m%d")}.pdf"'

        return response

    except ImportError:
        messages.error(request, "PDF generation requires reportlab. Please install it: pip install reportlab")
        return redirect('landlord_dashboard')
    except Exception as e:
        messages.error(request, f"Error generating PDF: {str(e)}")
        return redirect('landlord_dashboard')


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