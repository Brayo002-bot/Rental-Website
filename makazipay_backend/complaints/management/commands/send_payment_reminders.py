from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from properties.models import Payment


class Command(BaseCommand):
    help = 'Send payment reminders to tenants for upcoming and overdue payments'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days-before',
            type=int,
            default=3,
            help='Send reminder N days before due date'
        )

    def handle(self, *args, **options):
        days_before = options['days_before']
        today = timezone.now().date()
        reminder_date = today + timedelta(days=days_before)

        # Find unpaid payments that are due in N days or are overdue
        payments = Payment.objects.filter(
            paid=False,
            due_date__lte=reminder_date
        ).exclude(
            due_date__isnull=True
        )

        reminder_count = 0
        for payment in payments:
            if payment.due_date <= today:
                # Overdue payment - always send reminder
                if not payment.reminder_sent or payment.due_date < today - timedelta(days=1):
                    self._send_reminder(payment, 'overdue')
                    reminder_count += 1
            else:
                # Upcoming payment - send reminder once
                if not payment.reminder_sent:
                    self._send_reminder(payment, 'upcoming')
                    reminder_count += 1

        self.stdout.write(
            self.style.SUCCESS(f'✅ Successfully sent {reminder_count} payment reminders')
        )

    def _send_reminder(self, payment, reminder_type):
        """Send reminder to tenant (placeholder for actual SMS/Email sending)"""
        payment.reminder_sent = True
        payment.reminder_count += 1
        payment.last_reminder_date = timezone.now()
        payment.save()

        tenant = payment.tenant
        landlord = tenant.property.landlord

        if reminder_type == 'overdue':
            message = f"OVERDUE: Your rent payment of Ksh {payment.amount} was due on {payment.due_date}. Please pay immediately."
        else:
            message = f"REMINDER: Your rent payment of Ksh {payment.amount} is due on {payment.due_date}. Pay now to avoid late fees."

        # TODO: Implement actual SMS/Email sending here
        # from django.core.mail import send_mail
        # send_mail(
        #     f'Payment Reminder - {tenant.name}',
        #     message,
        #     'noreply@makazipay.com',
        #     [tenant.user.email],
        #     fail_silently=False,
        # )

        print(f"Reminder sent to {tenant.name}: {message}")
