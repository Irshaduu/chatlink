from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from datetime import timedelta
import random


class User(AbstractUser):
    """
    Final user is created ONLY after OTP verification.
    """
    pass


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
