#!/usr/bin/env python
"""
Automated Payment Reminder Script
Run this script periodically to send payment reminders to tenants.

For production deployment:
- Set up a cron job to run this script daily
- Example cron job (runs at 9 AM daily):
  0 9 * * * /path/to/your/python /path/to/this/script.py

For development:
- Run manually: python automated_reminders.py
- Or schedule with Windows Task Scheduler
"""

import os
import sys
import django

# Add the project directory to the Python path
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_DIR)

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'makazipay_backend.settings')
django.setup()

# Now we can import Django modules
from django.core.management import execute_from_command_line

def main():
    """Run the payment reminder command"""
    print("Starting automated payment reminders...")

    # Run the send_payment_reminders command
    execute_from_command_line(['manage.py', 'send_payment_reminders'])

    print("Payment reminders completed.")

if __name__ == '__main__':
    main()