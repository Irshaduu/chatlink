from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from .models import PendingOTP

User = get_user_model()


# ----------------------------
# LOGIN
# ----------------------------
def login_view(request):
    if request.method == "POST":
        identifier = request.POST.get("identifier")
        password = request.POST.get("password")

        user = User.objects.filter(username=identifier).first()

        if not user:
            messages.error(request, "Account not found. Please register.")
            return redirect("login")

        user = authenticate(request, username=identifier, password=password)

        if not user:
            messages.error(request, "Invalid password.")
            return redirect("login")

        login(request, user)
        messages.success(request, "Login successful.")
        return redirect("home")

    return render(request, "users/login.html")


# ----------------------------
# REGISTER (SEND OTP ONLY)
# ----------------------------
def register_view(request):
    if request.method == "POST":
        identifier = request.POST.get("identifier")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        if password != confirm_password:
            messages.error(request, "Passwords do not match")
            return redirect("register")

        # Remove old OTP if exists
        PendingOTP.objects.filter(identifier=identifier).delete()

        otp_obj = PendingOTP.objects.create(
            identifier=identifier,
            otp=""
        )
        otp_obj.generate_otp()

        # Store data temporarily in session
        request.session["pending_identifier"] = identifier
        request.session["pending_password"] = password

        if "@" in identifier:
            send_mail(
                subject="ChatLink OTP Verification",
                message=f"Your OTP is {otp_obj.otp}",
                from_email=None,
                recipient_list=[identifier],
            )
        else:
            print(f"OTP for mobile {identifier}: {otp_obj.otp}")

        messages.success(request, "OTP sent successfully")
        return redirect("otp_verify")

    return render(request, "users/register.html")


# ----------------------------
# OTP VERIFY (CREATE USER HERE)
# ----------------------------
def otp_verify_view(request):
    identifier = request.session.get("pending_identifier")
    password = request.session.get("pending_password")

    if not identifier or not password:
        messages.error(request, "Session expired. Please register again.")
        return redirect("register")

    try:
        otp_obj = PendingOTP.objects.get(identifier=identifier)
    except PendingOTP.DoesNotExist:
        messages.error(request, "OTP not found. Please register again.")
        return redirect("register")

    if request.method == "POST":
        otp_input = request.POST.get("otp")

        if otp_obj.is_expired():
            otp_obj.delete()
            messages.error(request, "OTP expired. Please resend OTP.")
            return redirect("register")

        if otp_obj.otp != otp_input:
            messages.error(request, "Invalid OTP")
            return redirect("otp_verify")

        # ✅ CREATE USER ONLY NOW
        user = User.objects.create_user(
            username=identifier,
            email=identifier if "@" in identifier else "",
            password=password
        )

        # Cleanup
        otp_obj.delete()
        request.session.flush()

        messages.success(request, "Account verified. Please login.")
        return redirect("login")

    return render(request, "users/otp_verify.html")


# ----------------------------
# RESEND OTP (NO JS, SAFE)
# ----------------------------
def resend_otp_view(request):
    identifier = request.session.get("pending_identifier")

    if not identifier:
        messages.error(request, "Session expired. Please register again.")
        return redirect("register")

    otp_obj, _ = PendingOTP.objects.get_or_create(identifier=identifier)
    otp_obj.generate_otp()

    if "@" in identifier:
        send_mail(
            subject="ChatLink OTP Verification",
            message=f"Your OTP is {otp_obj.otp}",
            from_email=None,
            recipient_list=[identifier],
        )
    else:
        print(f"OTP for mobile {identifier}: {otp_obj.otp}")

    messages.success(request, "New OTP sent successfully")
    return redirect("otp_verify")


# ----------------------------
# HOME
# ----------------------------
@login_required
def home_view(request):
    return render(request, "users/home.html")


# ----------------------------
# LOGOUT
# ----------------------------
def logout_view(request):
    logout(request)
    return redirect("login")
