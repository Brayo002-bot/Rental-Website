from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from properties.models import Property, Tenant, Payment
from complaints.models import Complaint, ComplaintAttachment
from django.urls import reverse
from datetime import date, timedelta

User = get_user_model()


class ComplaintModelTest(TestCase):
    """Test Complaint model"""

    def setUp(self):
        self.landlord = User.objects.create_user(
            username='landlord1',
            email='landlord@test.com',
            password='testpass123',
            role='landlord',
            phone='254712345678'
        )
        
        self.tenant_user = User.objects.create_user(
            username='tenant1',
            email='tenant@test.com',
            password='testpass123',
            role='tenant',
            phone='254787654321'
        )
        
        self.property = Property.objects.create(
            landlord=self.landlord,
            name='Test Property',
            address='123 Main St',
            total_units=5
        )
        
        self.tenant = Tenant.objects.create(
            user=self.tenant_user,
            name='John Doe',
            property=self.property,
            unit='101',
            rent=5000
        )

    def test_complaint_creation(self):
        """Test creating a complaint"""
        complaint = Complaint.objects.create(
            tenant=self.tenant,
            landlord=self.landlord,
            title='Water leak in bathroom',
            description='There is a water leak in the bathroom ceiling',
            priority='high'
        )
        self.assertEqual(complaint.tenant, self.tenant)
        self.assertEqual(complaint.landlord, self.landlord)
        self.assertEqual(complaint.status, 'open')

    def test_complaint_string_representation(self):
        """Test complaint string representation"""
        complaint = Complaint.objects.create(
            tenant=self.tenant,
            landlord=self.landlord,
            title='Broken window',
            description='Window in the living room is broken',
            priority='medium'
        )
        self.assertIn('Complaint from', str(complaint))


class ComplaintViewTest(TestCase):
    """Test Complaint views"""

    def setUp(self):
        self.client = Client()
        
        self.landlord = User.objects.create_user(
            username='landlord1',
            email='landlord@test.com',
            password='testpass123',
            role='landlord',
            phone='254712345678'
        )
        
        self.tenant_user = User.objects.create_user(
            username='tenant1',
            email='tenant@test.com',
            password='testpass123',
            role='tenant',
            phone='254787654321'
        )
        
        self.property = Property.objects.create(
            landlord=self.landlord,
            name='Test Property',
            address='123 Main St',
            total_units=5
        )
        
        self.tenant = Tenant.objects.create(
            user=self.tenant_user,
            name='John Doe',
            property=self.property,
            unit='101',
            rent=5000
        )

    def test_tenant_complaints_view_requires_login(self):
        """Test that complaints view requires login"""
        response = self.client.get(reverse('tenant_complaints'))
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_file_complaint_view_requires_tenant(self):
        """Test that file complaint view requires tenant role"""
        self.client.login(username='landlord1', password='testpass123')
        response = self.client.get(reverse('file_complaint'))
        self.assertEqual(response.status_code, 302)  # Should redirect

    def test_tenant_can_file_complaint(self):
        """Test that tenant can file a complaint"""
        self.client.login(username='tenant1', password='testpass123')
        response = self.client.post(reverse('file_complaint'), {
            'tenant_id': self.tenant.id,
            'title': 'Complaint test',
            'description': 'This is a test complaint',
            'priority': 'high'
        })
        complaint = Complaint.objects.filter(
            tenant=self.tenant,
            title='Complaint test'
        ).first()
        self.assertIsNotNone(complaint)

    def test_landlord_can_view_complaints(self):
        """Test that landlord can view complaints"""
        Complaint.objects.create(
            tenant=self.tenant,
            landlord=self.landlord,
            title='Test complaint',
            description='This is a test',
            priority='medium'
        )
        
        self.client.login(username='landlord1', password='testpass123')
        response = self.client.get(reverse('landlord_complaints'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('Test complaint', str(response.content))

    def test_landlord_can_respond_to_complaint(self):
        """Test that landlord can respond to a complaint"""
        complaint = Complaint.objects.create(
            tenant=self.tenant,
            landlord=self.landlord,
            title='Test complaint',
            description='This is a test',
            priority='medium'
        )
        
        self.client.login(username='landlord1', password='testpass123')
        response = self.client.post(
            reverse('complaint_detail', args=[complaint.id]),
            {
                'landlord_response': 'We will fix this immediately',
                'status': 'in_progress'
            }
        )
        
        complaint.refresh_from_db()
        self.assertEqual(complaint.status, 'in_progress')
        self.assertEqual(complaint.landlord_response, 'We will fix this immediately')


class PaymentReminderTest(TestCase):
    """Test Payment reminder functionality"""

    def setUp(self):
        self.landlord = User.objects.create_user(
            username='landlord1',
            email='landlord@test.com',
            password='testpass123',
            role='landlord'
        )
        
        self.tenant_user = User.objects.create_user(
            username='tenant1',
            email='tenant@test.com',
            password='testpass123',
            role='tenant'
        )
        
        self.property = Property.objects.create(
            landlord=self.landlord,
            name='Test Property',
            address='123 Main St',
            total_units=5
        )
        
        self.tenant = Tenant.objects.create(
            user=self.tenant_user,
            name='John Doe',
            property=self.property,
            unit='101',
            rent=5000
        )

    def test_payment_reminder_fields(self):
        """Test that Payment model has reminder fields"""
        payment = Payment.objects.create(
            tenant=self.tenant,
            amount=5000,
            due_date=date.today() + timedelta(days=7),
            paid=False
        )
        self.assertEqual(payment.reminder_sent, False)
        self.assertEqual(payment.reminder_count, 0)
        self.assertIsNone(payment.payment_date)
