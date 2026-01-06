from django.urls import path
from . import views

urlpatterns = [
    # Authentication
    path("", views.login_view, name="login"),
    path("register/", views.register_view, name="register"),
    path("logout/", views.logout_view, name="logout"),

    # Registration OTP
    path("otp/", views.verify_registration_otp, name="verify_registration_otp"),
    path("resend-otp/", views.resend_registration_otp, name="resend_registration_otp"),

    # Password reset
    path("forgot/", views.forgot_password_view, name="forgot_password"),
    path("reset-otp/", views.verify_password_reset_otp, name="verify_password_reset_otp"),
    path("reset-otp/resend/", views.resend_password_reset_otp, name="resend_password_reset_otp"),
    path("reset-password/", views.reset_password_view, name="reset_password"),

    # App
    path("home/", views.home_view, name="home"),
    path("profile/", views.profile_view, name="profile"),
    path("profile/edit/", views.edit_profile_view, name="edit_profile"),
]

