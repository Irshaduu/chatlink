from django.contrib import admin
from .models import User, PendingOTP


admin.site.register(User)
admin.site.register(PendingOTP)
