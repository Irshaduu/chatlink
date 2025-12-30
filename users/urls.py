from django.urls import path
from . import views

urlpatterns = [
    path("", views.login_view, name="login"),
    path("register/", views.register_view, name="register"),
    path("otp/", views.otp_verify_view, name="otp_verify"),
    path("resend-otp/", views.resend_otp_view, name="resend_otp"),
    path("home/", views.home_view, name="home"),
    path("logout/", views.logout_view, name="logout"),
    path("forgot/", views.forgot_password_view, name="forgot_password"),
    path("reset-otp/", views.reset_otp_view, name="reset_otp"),
    path("reset-password/", views.reset_password_view, name="reset_password"),

]
