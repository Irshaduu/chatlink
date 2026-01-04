from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from datetime import timedelta
import secrets
from django_countries.fields import CountryField


# -------------------------------------------------
# CONSTANTS
# -------------------------------------------------
GENDER_CHOICES = [
    ("male", "Male"),
    ("female", "Female"),
    ("other", "Other"),
]


# -------------------------------------------------
# CUSTOM USER MODEL
# -------------------------------------------------
class User(AbstractUser):
    # Contact (OTP-based)
    email = models.EmailField(unique=True, null=True, blank=True)
    phone = models.CharField(max_length=15, unique=True, null=True, blank=True)

    # Profile basics
    full_name = models.CharField(max_length=150, blank=True)
    bio = models.TextField(blank=True)

    # 🌍 Location & Personal info
    country = CountryField(blank=True, null=True)
    date_of_birth = models.DateField(null=True, blank=True)

    # 🗣 Language system
    native_language = models.CharField(max_length=10, blank=True)
    learning_language = models.CharField(max_length=10, blank=True)
    learning_language_updated_at = models.DateTimeField(null=True, blank=True)

    # 🔒 Immutable identity
    gender = models.CharField(
        max_length=10,
        choices=GENDER_CHOICES,
        default="other",
    )

    # Meta
    joined_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.username


# -------------------------------------------------
# OTP MODEL – REGISTRATION
# -------------------------------------------------
class PendingOTP(models.Model):
    identifier = models.CharField(max_length=255, unique=True)

    otp = models.CharField(max_length=6)
    attempts = models.PositiveSmallIntegerField(default=0)
    resend_count = models.PositiveSmallIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    last_sent_at = models.DateTimeField(null=True, blank=True)

    OTP_EXPIRY_MINUTES = 5
    MAX_ATTEMPTS = 5
    MAX_FREE_RESENDS = 5
    RESEND_COOLDOWN_SECONDS = 60

    def generate_otp(self, is_resend=False):
        self.otp = f"{secrets.randbelow(1_000_000):06d}"
        self.attempts = 0

        if is_resend:
            self.resend_count += 1

        self.last_sent_at = timezone.now()
        self.save()

    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(
            minutes=self.OTP_EXPIRY_MINUTES
        )

    def can_resend(self):
        # ✅ First 5 resends are free
        if self.resend_count < self.MAX_FREE_RESENDS:
            return True

        # ⏳ After free resends → enforce cooldown
        if not self.last_sent_at:
            return True

        return timezone.now() > self.last_sent_at + timedelta(
            seconds=self.RESEND_COOLDOWN_SECONDS
        )

    def verify_otp(self, input_otp):
        if self.is_expired():
            self.delete()
            return False, "OTP expired."

        self.attempts += 1

        if self.attempts > self.MAX_ATTEMPTS:
            self.delete()
            return False, "Too many invalid attempts."

        if self.otp == input_otp:
            return True, "OTP verified."

        self.save(update_fields=["attempts"])
        return False, "Invalid OTP."


# -------------------------------------------------
# OTP MODEL – PASSWORD RESET
# -------------------------------------------------
class PasswordResetOTP(models.Model):
    identifier = models.CharField(max_length=255, unique=True)

    otp = models.CharField(max_length=6)
    attempts = models.PositiveSmallIntegerField(default=0)
    resend_count = models.PositiveSmallIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    last_sent_at = models.DateTimeField(null=True, blank=True)

    OTP_EXPIRY_MINUTES = 5
    MAX_ATTEMPTS = 5
    MAX_FREE_RESENDS = 5
    RESEND_COOLDOWN_SECONDS = 60

    def generate_otp(self, is_resend=False):
        self.otp = f"{secrets.randbelow(1_000_000):06d}"
        self.attempts = 0

        if is_resend:
            self.resend_count += 1

        self.last_sent_at = timezone.now()
        self.save()

    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(
            minutes=self.OTP_EXPIRY_MINUTES
        )

    def can_resend(self):
        # ✅ First 5 resends are FREE
        if self.resend_count < self.MAX_FREE_RESENDS:
            return True

        # ⏳ After free resends → cooldown
        return timezone.now() > self.last_sent_at + timedelta(
            seconds=self.RESEND_COOLDOWN_SECONDS
        )

    def verify_otp(self, input_otp):
        if self.is_expired():
            self.delete()
            return False, "OTP expired."

        self.attempts += 1

        if self.attempts > self.MAX_ATTEMPTS:
            self.delete()
            return False, "Too many invalid attempts."

        if self.otp == input_otp:
            return True, "OTP verified."

        self.save(update_fields=["attempts"])
        return False, "Invalid OTP."
