# Implementation Guide: New Features

## Overview
This document describes the new features added to the MakaziPAY Rental System:
1. **Automated Payment Reminders** - Landlords can set due dates for rent payments
2. **Tenant Complaints System** - Tenants can file complaints against landlords
3. **Always-Visible STK Push** - M-Pesa payment button is always visible without requiring phone number

---

## 1. Automated Payment Reminders

### Feature Description
- Landlords can set due dates for rent payments (already in place with Payment model)
- The system can automatically send email reminders to tenants based on payment due dates
- Reminders track: when they were sent, how many times, and last send date
- Supports both upcoming payment reminders and overdue payment notifications

### Database Fields Added
- `payment_date` (DateTimeField): When the payment was actually made
- `reminder_sent` (BooleanField): Whether a reminder has been sent
- `reminder_count` (IntegerField): Number of reminders sent
- `last_reminder_date` (DateTimeField): When the last reminder was sent

### Email Configuration
The system is configured to send emails using Django's email backend. For development, emails are printed to the console. For production, configure SMTP settings in `settings.py`:

```python
# Production email settings
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-app-password'
DEFAULT_FROM_EMAIL = 'noreply@makazipay.com'
```

### Management Command
Run reminders manually with:
```bash
python manage.py send_payment_reminders --days-before=3
```

This sends reminders 3 days before the due date, and again for overdue payments.

### Automated Scheduling

#### For Development/Windows:
1. Create a Windows Task Scheduler task to run `automated_reminders.py` daily
2. Or run the script manually when needed

#### For Production/Linux:
Set up a cron job to run the automated reminders script daily at 9 AM:
```bash
# Edit crontab
crontab -e

# Add this line (adjust path to your project)
0 9 * * * /usr/bin/python3 /path/to/makazipay_backend/automated_reminders.py
```

#### Using the Automated Script:
```bash
# Run manually
python automated_reminders.py

# Or with full path
/path/to/python /path/to/makazipay_backend/automated_reminders.py
```

### Dashboard
- Landlords can see overdue payments highlighted in red
- Display shows upcoming payment amounts and dates
- Tenants see payment status (Paid/Pending/Overdue)

---

## 2. Tenant Complaints System

### New Models

#### Complaint Model
```python
- tenant: ForeignKey to Tenant
- landlord: ForeignKey to User (landlord)
- title: CharField - Brief title
- description: TextField - Detailed complaint
- status: CharField (open, in_progress, resolved, closed)
- priority: CharField (low, medium, high, urgent)
- created_at: DateTimeField - Auto
- updated_at: DateTimeField - Auto
- resolved_at: DateTimeField - When marked as resolved
- landlord_response: TextField - Landlord's response
- responded_at: DateTimeField - When landlord responded
```

#### ComplaintAttachment Model
```python
- complaint: ForeignKey to Complaint
- file: FileField - Supporting documents/images
- uploaded_at: DateTimeField - Auto
```

### Views & URLs

#### Tenant URLs
- `/complaints/my-complaints/` - View all complaints filed
- `/complaints/file-complaint/` - File a new complaint
- `/complaints/complaint/<id>/` - View complaint details

#### Landlord URLs
- `/complaints/complaints/` - View all received complaints
- `/complaints/complaint/<id>/respond/` - Respond to complaint
- Filter by status: `?status=open|in_progress|resolved|closed`

### Templates
All templates follow the existing dashboard styling:
- `tenant_complaints.html` - List of filed complaints
- `file_complaint.html` - File complaint form
- `complaint_detail.html` - View/respond to complaint
- `landlord_complaints.html` - Manage received complaints

### Features
1. **Tenants can:**
   - File complaints with title, description, and priority
   - Attach supporting files (PDF, DOC, images)
   - View complaint status and landlord responses
   - See all their complaints history

2. **Landlords can:**
   - View all complaints from their tenants
   - Filter by status (open, in_progress, resolved, closed)
   - Respond with detailed explanations
   - Update complaint status
   - Track complaint timestamps

---

## 3. Always-Visible STK Push Payment Button

### Changes Made
- M-Pesa payment button is now visible in multiple places:
  1. **Current Month Payments section** - Show button even without phone
  2. **Your Apartments cards** - Quick pay button on each apartment
  3. **Current Rent Invoice section** - Main payment section
  
### Behavior
- **Without phone number:** Button is disabled with helpful message
- **With phone number:** Button is enabled and ready to use
- **Clear messaging:** Users see exactly what they need to do
- **Easy access:** 💳 icon makes payment buttons easy to spot

### Templates Updated
- `tenant.html` - Added new complaints section, improved payment buttons

### User Experience Flow
1. Tenant logs in
2. See clear payment options
3. If no phone: Message says "Add phone in profile to pay"
4. If has phone: Click button to initiate M-Pesa STK push
5. Enter PIN on phone to complete payment

---

## Installation & Setup

### 1. Run Migrations
```bash
python manage.py makemigrations properties complaints
python manage.py migrate
```

### 2. Update Settings
The following are already added to settings.py:
```python
INSTALLED_APPS = [
    ...
    'payments',
    'complaints',
]
```

### 3. Register Admin
Models are automatically registered in Django admin:
```bash
python manage.py createsuperuser
# Then visit /admin/ to manage complaints
```

### 4. Testing
Run the test suite:
```bash
python manage.py test complaints
```

---

## File Structure

### New Complaints App
```
complaints/
├── __init__.py
├── admin.py                    # Admin interface
├── apps.py                     # App config
├── forms.py                    # Complaint forms
├── models.py                   # Complaint & ComplaintAttachment models
├── tests.py                    # Unit tests
├── urls.py                     # URL routing
├── views.py                    # View logic
├── management/
│   └── commands/
│       └── send_payment_reminders.py  # Reminder CLI command
└── migrations/
    └── 0001_initial.py        # Initial migration
```

### Updated Files
- `properties/models.py` - Added reminder fields to Payment
- `users/views.py` - Added complaint context to dashboards
- `makazipay_backend/settings.py` - Added complaints and payments apps
- `makazipay_backend/urls.py` - Added complaints URLs
- `templates/dashboards/tenant.html` - Added complaints section
- `templates/dashboards/landlord.html` - Added complaints section

### New Templates
```
templates/dashboards/complaints/
├── tenant_complaints.html       # List tenant's complaints
├── file_complaint.html          # File new complaint form
├── complaint_detail.html        # View/respond to complaint
└── landlord_complaints.html     # Manage received complaints
```

---

## Future Enhancements

### Payment Reminders
- [ ] Integrate SMS notifications (Twilio, AfricasTalking)
- [ ] Email notifications
- [ ] WhatsApp reminders
- [ ] Push notifications
- [ ] Scheduled tasks (Celery)

### Complaints
- [ ] Complaint escalation levels
- [ ] Automated escalation if not resolved in X days
- [ ] Complaint category system
- [ ] Internal notes (landlord only)
- [ ] Photo evidence support
- [ ] Video evidence support
- [ ] Complaint resolution timeline

### Payments
- [ ] Payment installments
- [ ] Late fee calculation
- [ ] Payment receipt generation
- [ ] Payment analytics
- [ ] Payment export (CSV/PDF)

---

## Troubleshooting

### Issue: Complaints app not found
**Solution:** Make sure `'complaints'` is in INSTALLED_APPS in settings.py

### Issue: Migrations failed
**Solution:** Check for conflicts with `python manage.py showmigrations`

### Issue: STK Push button not showing
**Solution:** Verify the tenant.html was updated correctly, check browser cache

### Issue: Reminders not sending
**Solution:** Run `python manage.py send_payment_reminders` manually to test

---

## Support

For issues or questions, please refer to:
- Django documentation: https://docs.djangoproject.com
- M-Pesa API: https://developer.safaricom.co.ke
