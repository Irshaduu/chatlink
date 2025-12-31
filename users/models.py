from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from datetime import timedelta
import random

from django_countries.fields import CountryField


# -------------------------------------------------
# CUSTOM USER MODEL
# -------------------------------------------------
class User(AbstractUser):
    # Contact (OTP-based)
    email = models.EmailField(null=True, blank=True)
    phone = models.CharField(max_length=15, unique=True, null=True, blank=True)

    # Profile basics
    full_name = models.CharField(max_length=150, blank=True)
    bio = models.TextField(blank=True)

    # 🌍 Location & Personal info
    country = CountryField(blank=True, null=True)
    date_of_birth = models.DateField(null=True, blank=True)

    # 🗣 Language system (ISO 639 codes)
    native_language = models.CharField(max_length=10, blank=True)
    learning_language = models.CharField(max_length=10, blank=True)

    # Meta
    joined_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.username


# -------------------------------------------------
# OTP MODEL – REGISTRATION
# -------------------------------------------------
class PendingOTP(models.Model):
    """
    Temporary OTP holder BEFORE user creation.
    """
    identifier = models.CharField(max_length=255)  # email or phone
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def generate_otp(self):
        self.otp = str(random.randint(100000, 999999))
        self.created_at = timezone.now()
        self.save()

    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(minutes=5)

    def __str__(self):
        return f"OTP for {self.identifier}"


# -------------------------------------------------
# OTP MODEL – PASSWORD RESET
# -------------------------------------------------
class PasswordResetOTP(models.Model):
    identifier = models.CharField(max_length=255)  # username
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def generate_otp(self):
        self.otp = str(random.randint(100000, 999999))
        self.created_at = timezone.now()
        self.save()

    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(minutes=5)

    def __str__(self):
        return f"Password reset OTP for {self.identifier}"
