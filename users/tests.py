from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from users.models import PasswordResetOTP
from django.utils import timezone
from datetime import timedelta



User = get_user_model()


class AuthPageTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123"
        )

    def test_login_page_loads(self):
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)

    def test_register_page_loads(self):
        response = self.client.get(reverse("register"))
        self.assertEqual(response.status_code, 200)

    def test_home_requires_login(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 302)

    def test_home_accessible_when_logged_in(self):
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)


class LogoutTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123"
        )

    def test_logout_logs_user_out(self):
        self.client.login(username="testuser", password="testpass123")

        response = self.client.post(reverse("logout"))
        self.assertRedirects(response, reverse("login"))

        response = self.client.get(reverse("home"))

        self.assertRedirects(
            response,
            f"{reverse('login')}?next={reverse('home')}"
        )


class ForgotPasswordPageTest(TestCase):

    def test_forgot_password_page_loads(self):
        response = self.client.get(reverse("forgot_password"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "users/forgot_password.html")


class ForgotPasswordSendOTPTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="resetuser",
            email="reset@example.com",
            password="StrongPass123"
        )

    def test_forgot_password_creates_otp_and_redirects(self):
        response = self.client.post(
            reverse("forgot_password"),
            {"identifier": "reset@example.com"}
        )

        # Redirects to OTP verification page
        self.assertRedirects(
            response,
            reverse("verify_password_reset_otp")
        )

        # OTP created in DB
        self.assertTrue(
            PasswordResetOTP.objects.filter(
                identifier="reset@example.com"
            ).exists()
        )

        # Identifier stored in session
        self.assertEqual(
            self.client.session["reset_identifier"],
            "reset@example.com"
        )


class PasswordResetInvalidOTPTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="otpuser",
            email="otp@example.com",
            password="StrongPass123"
        )

        # Create OTP manually
        self.otp = PasswordResetOTP.objects.create(
            identifier="otp@example.com"
        )
        self.otp.generate_otp()

        # Simulate session state
        session = self.client.session
        session["reset_identifier"] = "otp@example.com"
        session.save()

    def test_invalid_reset_otp_does_not_verify(self):
        response = self.client.post(
            reverse("verify_password_reset_otp"),
            {"otp": "000000"}  # wrong OTP
        )

        # Should stay on OTP page
        self.assertRedirects(
            response,
            reverse("verify_password_reset_otp")
        )

        # reset_verified must NOT be set
        self.assertNotIn(
            "reset_verified",
            self.client.session
        )


class PasswordResetExpiredOTPTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="expireduser",
            email="expired@example.com",
            password="StrongPass123"
        )

        self.otp = PasswordResetOTP.objects.create(
            identifier="expired@example.com"
        )
        self.otp.generate_otp()

        self.otp.created_at = timezone.now() - timedelta(minutes=10)
        self.otp.save()

        session = self.client.session
        session["reset_identifier"] = "expired@example.com"
        session.save()

    def test_expired_reset_otp_is_rejected(self):
        response = self.client.post(
            reverse("verify_password_reset_otp"),
            {"otp": self.otp.otp}
        )

        # First redirect (back to reset-otp)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("verify_password_reset_otp"))

        # Second redirect (OTP missing → forgot password)
        final_response = self.client.get(reverse("verify_password_reset_otp"))
        self.assertRedirects(final_response, reverse("forgot_password"))

        # OTP must be deleted
        self.assertFalse(
            PasswordResetOTP.objects.filter(
                identifier="expired@example.com"
            ).exists()
        )

        # reset_verified must NOT be set
        self.assertNotIn("reset_verified", self.client.session)


class PasswordResetSuccessTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="successuser",
            email="success@example.com",
            password="OldPassword123"
        )

        # Create OTP
        self.otp = PasswordResetOTP.objects.create(
            identifier="success@example.com"
        )
        self.otp.generate_otp()

        # Session setup
        session = self.client.session
        session["reset_identifier"] = "success@example.com"
        session.save()

    def test_successful_password_reset_flow(self):
        # Step 1: Verify OTP
        response = self.client.post(
            reverse("verify_password_reset_otp"),
            {"otp": self.otp.otp}
        )

        self.assertRedirects(
            response,
            reverse("reset_password")
        )

        # Step 2: Submit new password
        response = self.client.post(
            reverse("reset_password"),
            {
                "password": "NewSecurePass123",
                "confirm_password": "NewSecurePass123",
            }
        )

        self.assertRedirects(response, reverse("login"))

        # Step 3: Old password should NOT work
        self.assertFalse(
            self.client.login(
                username="successuser",
                password="OldPassword123"
            )
        )

        # Step 4: New password should work
        self.assertTrue(
            self.client.login(
                username="successuser",
                password="NewSecurePass123"
            )
        )
