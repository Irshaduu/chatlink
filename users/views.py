from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from .models import PendingOTP, PasswordResetOTP
from django.views.decorators.cache import never_cache

User = get_user_model()


# -------------------------------------------------
# LOGIN
# -------------------------------------------------
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


# -------------------------------------------------
# REGISTER 
# -------------------------------------------------
def register_view(request):
    if request.method == "POST":
        identifier = request.POST.get("identifier", "").strip()

        if User.objects.filter(username=identifier).exists():
            messages.error(request, "Account already exists. Please login.")
            return redirect("login")

        PendingOTP.objects.filter(identifier=identifier).delete()

        otp_obj = PendingOTP.objects.create(identifier=identifier)
        otp_obj.generate_otp()

        request.session["pending_identifier"] = identifier

        if "@" in identifier:
            send_mail(
                subject="ChatLink OTP Verification",
                message=f"Your OTP is {otp_obj.otp}",
                from_email=None,
                recipient_list=[identifier],
            )
        else:
            print(f"OTP for mobile {identifier}: {otp_obj.otp}")

        messages.success(request, "OTP sent successfully.")
        return redirect("otp_verify")

    return render(request, "users/register.html")




# -----------------------------------------------
# OTP VERIFY → CREATE USER + AUTO LOGIN
# -----------------------------------------------
def otp_verify_view(request):
    identifier = request.session.get("pending_identifier")

    if not identifier:
        messages.error(request, "Session expired. Please register again.")
        return redirect("register")

    try:
        otp_obj = PendingOTP.objects.get(identifier=identifier)
    except PendingOTP.DoesNotExist:
        messages.error(request, "OTP not found. Please register again.")
        return redirect("register")

    if request.method == "POST":
        otp_input = request.POST.get("otp", "").strip()
        password = request.POST.get("password", "").strip()
        confirm_password = request.POST.get("confirm_password", "").strip()

        if otp_obj.is_expired():
            otp_obj.delete()
            messages.error(request, "OTP expired. Please register again.")
            return redirect("register")

        if otp_input != otp_obj.otp:
            messages.error(request, "Invalid OTP.")
            return redirect("otp_verify")

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect("otp_verify")

        # ✅ CREATE USER
        user = User.objects.create_user(
            username=identifier,
            email=identifier if "@" in identifier else "",
            password=password
        )

        # ✅ AUTO LOGIN
        user.backend = "django.contrib.auth.backends.ModelBackend"
        login(request, user)

        # ✅ CLEANUP (SAFE)
        otp_obj.delete()
        request.session.pop("pending_identifier", None)

        messages.success(request, "Account created successfully.")
        return redirect("home")

    return render(request, "users/otp_verify.html")



# -------------------------------------------------
# RESEND OTP (REGISTER)
# -------------------------------------------------
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

    messages.success(request, "New OTP sent successfully.")
    return redirect("otp_verify")


# -------------------------------------------------
# FORGOT PASSWORD → SEND OTP
# -------------------------------------------------
def forgot_password_view(request):
    if request.method == "POST":
        identifier = request.POST.get("identifier")

        user = User.objects.filter(username=identifier).first()
        if not user:
            messages.error(request, "Account not found.")
            return redirect("forgot_password")

        otp_obj, _ = PasswordResetOTP.objects.get_or_create(identifier=identifier)
        otp_obj.generate_otp()

        if "@" in identifier:
            send_mail(
                subject="ChatLink Password Reset OTP",
                message=f"Your OTP is {otp_obj.otp}",
                from_email=None,
                recipient_list=[identifier],
            )
        else:
            print(f"Password reset OTP for {identifier}: {otp_obj.otp}")

        request.session["reset_identifier"] = identifier
        messages.success(request, "OTP sent successfully.")
        return redirect("reset_otp")

    return render(request, "users/forgot_password.html")


# -------------------------------------------------
# FORGOT PASSWORD → VERIFY OTP
# -------------------------------------------------
def reset_otp_view(request):
    identifier = request.session.get("reset_identifier")

    if not identifier:
        messages.error(request, "Session expired. Try again.")
        return redirect("forgot_password")

    if request.method == "POST":
        otp_input = request.POST.get("otp")

        try:
            otp_obj = PasswordResetOTP.objects.get(
                identifier=identifier, otp=otp_input
            )
        except PasswordResetOTP.DoesNotExist:
            messages.error(request, "Invalid OTP.")
            return redirect("reset_otp")

        if otp_obj.is_expired():
            otp_obj.delete()
            messages.error(request, "OTP expired.")
            return redirect("forgot_password")

        otp_obj.delete()
        request.session["reset_verified"] = True
        return redirect("reset_password")

    return render(request, "users/reset_otp.html")


# -------------------------------------------------
# RESET PASSWORD
# -------------------------------------------------
def reset_password_view(request):
    if not request.session.get("reset_verified"):
        return redirect("forgot_password")

    identifier = request.session.get("reset_identifier")

    if request.method == "POST":
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect("reset_password")

        user = User.objects.get(username=identifier)
        user.set_password(password)
        user.save()

        request.session.flush()
        messages.success(request, "Password reset successful. Please login.")
        return redirect("login")

    return render(request, "users/reset_password.html")


# -------------------------------------------------
# HOME
# -------------------------------------------------
@never_cache
@login_required
def home_view(request):
    return render(request, "users/home.html")


# -------------------------------------------------
# LOGOUT
# -------------------------------------------------
def logout_view(request):
    logout(request)
    messages.info(request, "Logged out.")
    return redirect("login")



