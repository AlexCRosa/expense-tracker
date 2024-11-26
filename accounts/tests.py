from django.test import TestCase
from django.urls import reverse
from core.models import User
from django.core import mail


class UserSignupTests(TestCase):

    def test_user_signup(self):
        signup_url = reverse('accounts:signup')
        response = self.client.post(signup_url, {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'password1': 'ComplexPass123!',
            'password2': 'ComplexPass123!',
        })

        if response.status_code == 302:
            self.assertRedirects(response, reverse('accounts:login'))
        else:
            print("Response Content:", response.content.decode())
            if response.context and 'form' in response.context:
                print("Form Errors:", response.context['form'].errors)

        self.assertTrue(User.objects.filter(username='newuser').exists())


class UserLoginTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='password123'
        )

    def test_user_login_success(self):
        login_url = reverse('accounts:login')
        response = self.client.post(login_url, {
            'username': 'testuser',
            'password': 'password123',
        })

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('dashboard'))

    def test_user_login_failure(self):
        login_url = reverse('accounts:login')
        response = self.client.post(login_url, {
            'username': 'testuser',
            'password': 'wrongpassword',
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Please enter a correct username and password.")


class PasswordChangeTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='password123'
        )
        self.client.login(username='testuser', password='password123')

    def test_password_change(self):
        password_change_url = reverse('accounts:password_change')
        response = self.client.post(password_change_url, {
            'old_password': 'password123',
            'new_password1': 'NewComplexPass123!',
            'new_password2': 'NewComplexPass123!',
        })

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('accounts:password_change_done'))

        # Verify the user can log in with the new password
        self.client.logout()
        login_url = reverse('accounts:login')
        response = self.client.post(login_url, {
            'username': 'testuser',
            'password': 'NewComplexPass123!',
        })

        self.assertEqual(response.status_code, 302)

    def test_password_change_failure(self):
        password_change_url = reverse('accounts:password_change')
        response = self.client.post(password_change_url, {
            'old_password': 'wrongpassword',
            'new_password1': 'NewComplexPass123!',
            'new_password2': 'NewComplexPass123!',
        })

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/password_change.html')
        self.assertContains(response, "Your old password was entered incorrectly.")


class PasswordResetTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="testuser@example.com",
            password="password123"
        )
        self.password_reset_url = reverse('accounts:password_reset')

    def test_password_reset_email_sent(self):
        response = self.client.post(self.password_reset_url, {'email': self.user.email})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(self.user.email, mail.outbox[0].to)

    def test_password_reset_email_not_sent_for_invalid_user(self):
        response = self.client.post(self.password_reset_url, {'email': 'nonexistent@example.com'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 0)

    def test_password_reset_email_content(self):
        response = self.client.post(self.password_reset_url, {'email': self.user.email})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 1)

        # Check email content
        email = mail.outbox[0]
        self.assertIn('/accounts/reset/', email.body)
        self.assertIn(self.user.username, email.body)


    
