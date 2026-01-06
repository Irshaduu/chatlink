from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST
from django.db.models import Q
from django.utils import timezone
from datetime import date, timedelta
import re
from .models import PendingOTP, PasswordResetOTP
from .utils import get_all_languages
from datetime import datetime


User = get_user_model()


EMAIL_REGEX = r"[^@]+@[^@]+\.[^@]+"
PHONE_REGEX = r"^\+?\d{7,15}$"


# -------------------------------------------------
# LOGIN
# -------------------------------------------------
def login_view(request):
    if request.method == "POST":
        identifier = request.POST.get("identifier", "").strip()
        password = request.POST.get("password", "").strip()

        if not identifier or not password:
            messages.error(request, "All fields are required.")
            return redirect("login")

        user_obj = User.objects.filter(
            Q(username=identifier) |
            Q(email=identifier) |
            Q(phone=identifier)
        ).first()

        if not user_obj:
            messages.error(request, "Invalid credentials.")
            return redirect("login")

        user = authenticate(
            request,
            username=user_obj.username,
            password=password
        )

        if not user:
            messages.error(request, "Invalid credentials.")
            return redirect("login")

        login(request, user)
        request.session.cycle_key()  # 🔐 session fixation protection
        messages.success(request, "Login successful.")
        return redirect("home")

    return render(request, "users/login.html")


# -------------------------------------------------
# REGISTER
# -------------------------------------------------
def register_view(request):
    if request.method == "POST":
        full_name = request.POST.get("full_name", "").strip()
        username = request.POST.get("username", "").strip()
        identifier = request.POST.get("identifier", "").strip()
        dob_str = request.POST.get("dob", "").strip()
        gender = request.POST.get("gender", "").strip()
        country = request.POST.get("country", "").strip()
        native_language = request.POST.get("native_language", "").strip()
        learning_language = request.POST.get("learning_language", "").strip()

        if not all([
            full_name, username, identifier, dob_str,
            gender, country, native_language, learning_language
        ]):
            messages.error(request, "All fields are required.")
            return redirect("register")

        if gender not in ["male", "female", "other"]:
            messages.error(request, "Please select a valid gender.")
            return redirect("register")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
            return redirect("register")

        # 🔐 IDENTIFIER VALIDATION
        if "@" in identifier:
            if not re.match(EMAIL_REGEX, identifier):
                messages.error(request, "Enter a valid email address.")
                return redirect("register")
            if User.objects.filter(email=identifier).exists():
                messages.error(request, "Account already exists. Please login.")
                return redirect("login")
        else:
            if not re.match(PHONE_REGEX, identifier):
                messages.error(request, "Enter a valid phone number.")
                return redirect("register")
            if User.objects.filter(phone=identifier).exists():
                messages.error(request, "Account already exists. Please login.")
                return redirect("login")

        try:
            dob = date.fromisoformat(dob_str)
        except ValueError:
            messages.error(request, "Invalid date of birth.")
            return redirect("register")

        age = date.today().year - dob.year - (
            (date.today().month, date.today().day) < (dob.month, dob.day)
        )

        if age < 13:
            messages.error(request, "You must be at least 13 years old.")
            return redirect("register")

        # Fresh OTP flow
        PendingOTP.objects.filter(identifier=identifier).delete()
        otp_obj = PendingOTP.objects.create(identifier=identifier)
        otp_obj.generate_otp()

        if "@" in identifier:
            send_mail(
                subject="ChatLink OTP Verification",
                message=f"Your OTP is {otp_obj.otp}",
                from_email=None,
                recipient_list=[identifier],
            )

        request.session.update({
            "pending_full_name": full_name,
            "pending_username": username,
            "pending_identifier": identifier,
            "pending_dob": dob_str,
            "pending_gender": gender,
            "pending_country": country,
            "pending_native_language": native_language,
            "pending_learning_language": learning_language,
        })

        messages.success(request, "OTP sent successfully.")
        return redirect("verify_registration_otp")

    return render(request, "users/register.html", {
        "languages": get_all_languages()
    })


# -------------------------------------------------
# OTP VERIFY → CREATE USER
# -------------------------------------------------
@never_cache
def verify_registration_otp(request):
    username = request.session.get("pending_username")
    identifier = request.session.get("pending_identifier")

    if not username or not identifier:
        messages.error(request, "Session expired. Please register again.")
        return redirect("register")

    try:
        otp_obj = PendingOTP.objects.get(identifier=identifier)
    except PendingOTP.DoesNotExist:
        messages.error(request, "OTP not found.")
        return redirect("register")

    if request.method == "POST":
        otp_input = request.POST.get("otp", "").strip()
        password = request.POST.get("password", "").strip()
        confirm_password = request.POST.get("confirm_password", "").strip()

        if otp_obj.is_expired():
            otp_obj.delete()
            messages.error(request, "OTP expired.")
            return redirect("register")

        valid, message = otp_obj.verify_otp(otp_input)
        if not valid:
            messages.error(request, message)
            return redirect("verify_registration_otp")

        if not password or password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect("verify_registration_otp")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
            return redirect("register")

        user = User.objects.create_user(
            username=username,
            password=password
        )

        if "@" in identifier:
            user.email = identifier
        else:
            user.phone = identifier

        user.full_name = request.session.get("pending_full_name")
        user.date_of_birth = date.fromisoformat(
            request.session.get("pending_dob")
        )
        user.gender = request.session.get("pending_gender")
        user.country = request.session.get("pending_country")
        user.native_language = request.session.get("pending_native_language")
        user.learning_language = request.session.get("pending_learning_language")
        user.save()

        login(request, user)
        request.session.cycle_key()

        otp_obj.delete()
        for k in list(request.session.keys()):
            if k.startswith("pending_"):
                del request.session[k]

        messages.success(request, "Account created successfully.")
        return redirect("home")

    return render(request, "users/verify_registration_otp.html")


# -------------------------------------------------
# RESEND OTP (REGISTER)
# -------------------------------------------------
def resend_registration_otp(request):
    identifier = request.session.get("pending_identifier")

    if not identifier:
        messages.error(request, "Session expired.")
        return redirect("register")

    otp_obj = PendingOTP.objects.filter(identifier=identifier).first()
    if not otp_obj:
        messages.error(request, "OTP not found.")
        return redirect("register")

    if not otp_obj.can_resend():
        messages.error(
            request,
            "Please wait before requesting another OTP."
        )
        return redirect("verify_registration_otp")

    otp_obj.generate_otp(is_resend=True)

    if "@" in identifier:
        send_mail(
            subject="ChatLink OTP Verification",
            message=f"Your OTP is {otp_obj.otp}",
            from_email=None,
            recipient_list=[identifier],
        )

    messages.success(request, "New OTP sent.")
    return redirect("verify_registration_otp")

# -------------------------------------------------
# FORGOT PASSWORD → SEND OTP
# -------------------------------------------------
def forgot_password_view(request):
    if request.method == "POST":
        identifier = request.POST.get("identifier", "").strip()

        user = User.objects.filter(
            Q(username=identifier) |
            Q(email=identifier) |
            Q(phone=identifier)
        ).first()

        if not user:
            messages.error(request, "Account not found.")
            return redirect("forgot_password")

        otp_obj = PasswordResetOTP.objects.filter(identifier=identifier).first()

        if otp_obj and not otp_obj.can_resend():
            messages.error(
                request,
                "Please wait before requesting another OTP."
            )
            return redirect("forgot_password")


        if not otp_obj or otp_obj.is_expired():
            PasswordResetOTP.objects.filter(identifier=identifier).delete()
            otp_obj = PasswordResetOTP.objects.create(identifier=identifier)
            otp_obj.generate_otp(is_resend=False)  # ✅ IMPORTANT

        if "@" in identifier:
            send_mail(
                subject="ChatLink Password Reset OTP",
                message=f"Your OTP is {otp_obj.otp}",
                from_email=None,
                recipient_list=[identifier],
            )

        request.session["reset_identifier"] = identifier
        messages.success(request, "OTP sent successfully.")
        return redirect("verify_password_reset_otp")

    return render(request, "users/forgot_password.html")


# -------------------------------------------------
# RESEND OTP (PASSWORD RESET)
# -------------------------------------------------
def resend_password_reset_otp(request):
    identifier = request.session.get("reset_identifier")

    if not identifier:
        messages.error(request, "Session expired.")
        return redirect("forgot_password")

    otp_obj = PasswordResetOTP.objects.filter(identifier=identifier).first()
    if not otp_obj:
        messages.error(request, "OTP not found.")
        return redirect("forgot_password")

    if not otp_obj.can_resend():
        messages.error(
            request,
            "Please wait before requesting another OTP."
        )
        return redirect("verify_password_reset_otp")

    otp_obj.generate_otp(is_resend=True)

    if "@" in identifier:
        send_mail(
            subject="ChatLink Password Reset OTP",
            message=f"Your OTP is {otp_obj.otp}",
            from_email=None,
            recipient_list=[identifier],
        )

    messages.success(request, "New OTP sent.")
    return redirect("verify_password_reset_otp")



# -------------------------------------------------
# VERIFY PASSWORD RESET OTP
# -------------------------------------------------
def verify_password_reset_otp(request):
    identifier = request.session.get("reset_identifier")

    if not identifier:
        messages.error(request, "Session expired.")
        return redirect("forgot_password")

    otp_obj = PasswordResetOTP.objects.filter(identifier=identifier).first()
    if not otp_obj:
        messages.error(request, "OTP not found.")
        return redirect("forgot_password")

    if request.method == "POST":
        otp_input = request.POST.get("otp", "").strip()
        valid, message = otp_obj.verify_otp(otp_input)

        if not valid:
            messages.error(request, message)
            return redirect("verify_password_reset_otp")

        otp_obj.delete()
        request.session["reset_verified"] = True
        request.session["reset_verified_at"] = timezone.now().isoformat()

        return redirect("reset_password")

    return render(request, "users/verify_password_reset_otp.html")


# -------------------------------------------------
# RESET PASSWORD
# -------------------------------------------------
def reset_password_view(request):
    verified = request.session.get("reset_verified")
    verified_at = request.session.get("reset_verified_at")

    if not verified or not verified_at:
        messages.error(request, "Session expired.")
        return redirect("forgot_password")

    verified_time = datetime.fromisoformat(verified_at)

    if timezone.now() - verified_time > timedelta(minutes=10):
        request.session.flush()
        messages.error(request, "Reset session expired.")
        return redirect("forgot_password")

    identifier = request.session.get("reset_identifier")

    user = User.objects.filter(
        Q(username=identifier) |
        Q(email=identifier) |
        Q(phone=identifier)
    ).first()

    if not user:
        messages.error(request, "Account not found.")
        return redirect("forgot_password")

    if request.method == "POST":
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect("reset_password")

        user.set_password(password)
        user.save()
        request.session.flush()

        messages.success(request, "Password reset successful.")
        return redirect("login")

    return render(request, "users/reset_password.html")


# -------------------------------------------------
# HOME / PROFILE / EDIT / LOGOUT
# -------------------------------------------------
@never_cache
@login_required
def home_view(request):
    return render(request, "users/home.html", {"user": request.user})


@never_cache
@login_required
def profile_view(request):
    return render(request, "users/profile.html", {"user": request.user})


@never_cache
@login_required
def edit_profile_view(request):
    user = request.user

    if request.method == "POST":
        full_name = request.POST.get("full_name", "").strip()
        bio = request.POST.get("bio", "").strip()
        new_learning_language = request.POST.get("learning_language", "").strip()

        if not full_name:
            messages.error(request, "Full name is required.")
            return redirect("edit_profile")

        user.full_name = full_name
        user.bio = bio

        if new_learning_language and new_learning_language != user.learning_language:
            now = timezone.now()
            if user.learning_language_updated_at:
                next_allowed = user.learning_language_updated_at + timedelta(days=15)
                if now < next_allowed:
                    messages.error(
                        request,
                        f"You can change learning language after {(next_allowed - now).days + 1} day(s)."
                    )
                    return redirect("edit_profile")

            user.learning_language = new_learning_language
            user.learning_language_updated_at = now

        user.save()
        messages.success(request, "Profile updated successfully.")
        return redirect("profile")

    return render(request, "users/edit_profile.html", {
        "user": user,
        "languages": get_all_languages(),
    })


@require_POST
def logout_view(request):
    logout(request)
    messages.info(request, "Logged out.")
    return redirect("login")
