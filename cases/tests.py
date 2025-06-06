from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from accounts.models import NGOProfile, LawyerProfile
from cases.models import Case, CaseCategory,UserWallet,TokenTransaction
from cases.utils import award_tokens

User = get_user_model()

class CaseCreationAndVisibilityTest(TestCase):
    def setUp(self):
        # Create NGO User
        self.ngo_user = User.objects.create_user(
            email='ngo@example.com',
            password='password123',
            role='NGO'
        )
        self.ngo_profile = NGOProfile.objects.create(user=self.ngo_user)

        # Create Lawyer User
        self.lawyer_user = User.objects.create_user(
            email='lawyer@example.com',
            password='password123',
            role='LAWYER'
        )
        self.lawyer_profile = LawyerProfile.objects.create(user=self.lawyer_user)

        # Create category
        self.category = CaseCategory.objects.create(name="Civil", description="Civil Law")

    def test_ngo_can_create_case_with_open_status(self):
        """Ensure NGO can create a case and its status is 'open'"""
        self.client.login(email='ngo@example.com', password='password123')

        response = self.client.post(reverse('cases:case_create'), {
            'title': 'Test Case',
            'description': 'Test Description',
            'urgency': 'medium',
            'category': self.category.id,
            'location': 'New York'
        })

        self.assertEqual(response.status_code, 302)

        case = Case.objects.filter(title='Test Case').first()
        self.assertIsNotNone(case)
        self.assertEqual(case.status, 'open')
        self.assertEqual(case.ngo, self.ngo_user)

    def test_created_case_is_visible_to_lawyers(self):
        """Ensure that a created 'open' case is visible to lawyers on browse page"""
        case = Case.objects.create(
            title='Visible Case',
            description='This should be visible',
            urgency='medium',
            category=self.category,
            location='Los Angeles',
            ngo=self.ngo_user,
            status='open'
        )

        self.client.login(email='lawyer@example.com', password='password123')
        response = self.client.get(reverse('cases:lawyer_browse_cases'))
        self.assertEqual(response.status_code, 200)

        self.assertIn(case, response.context['cases'])

    def test_non_open_case_not_visible_to_lawyers(self):
        """Ensure that a non-open case (e.g., assigned) is not visible to lawyers"""
        case = Case.objects.create(
            title='Invisible Case',
            description='This should NOT be visible',
            urgency='high',
            category=self.category,
            location='Chicago',
            ngo=self.ngo_user,
            status='assigned'
        )

        self.client.login(email='lawyer@example.com', password='password123')
        response = self.client.get(reverse('cases:lawyer_browse_cases'))
        self.assertEqual(response.status_code, 200)

        self.assertNotIn(case, response.context['cases'])



class TokenSystemTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.case = Case.objects.create(title='Test Case', ngo=self.user)

    def test_award_tokens(self):
        award_tokens(self.user, 50, 'Test action', self.case)
        wallet = UserWallet.objects.get(user=self.user)
        self.assertEqual(wallet.balance, 50)
        transaction = TokenTransaction.objects.get(user=self.user)
        self.assertEqual(transaction.amount, 50)
        self.assertEqual(transaction.description, 'Test action')