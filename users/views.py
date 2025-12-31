from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from .models import PendingOTP, PasswordResetOTP
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST
from django.db.models import Q
from .utils import get_all_languages
from datetime import date


User = get_user_model()


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

        # 🔍 Find user by username OR email OR phone
        user_obj = User.objects.filter(
            Q(username=identifier) |
            Q(email=identifier) |
            Q(phone=identifier)
        ).first()

        if not user_obj:
            messages.error(request, "Invalid credentials.")
            return redirect("login")

        # 🔐 Authenticate using username internally
        user = authenticate(
            request,
            username=user_obj.username,
            password=password
        )

        if not user:
            messages.error(request, "Invalid credentials.")
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
        # -----------------------------
        # Fetch form data
        # -----------------------------
        full_name = request.POST.get("full_name", "").strip()
        username = request.POST.get("username", "").strip()
        identifier = request.POST.get("identifier", "").strip()

        dob_str = request.POST.get("dob", "").strip()
        country = request.POST.get("country", "").strip()
        native_language = request.POST.get("native_language", "").strip()
        learning_language = request.POST.get("learning_language", "").strip()

        # -----------------------------
        # Basic validation
        # -----------------------------
        if not all([
            full_name,
            username,
            identifier,
            dob_str,
            country,
            native_language,
            learning_language
        ]):
            messages.error(request, "All fields are required.")
            return redirect("register")

        # -----------------------------
        # Username uniqueness
        # -----------------------------
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
            return redirect("register")

        # -----------------------------
        # Email / phone uniqueness
        # -----------------------------
        if (
            User.objects.filter(email=identifier).exists() or
            User.objects.filter(phone=identifier).exists()
        ):
            messages.error(request, "Account already exists. Please login.")
            return redirect("login")

        # -----------------------------
        # DOB validation (18+)
        # -----------------------------
        try:
            dob = date.fromisoformat(dob_str)
        except ValueError:
            messages.error(request, "Invalid date of birth.")
            return redirect("register")

        today = date.today()
        age = today.year - dob.year - (
            (today.month, today.day) < (dob.month, dob.day)
        )

        if age < 13:
            messages.error(
                request,
                "You must be at least 13 years old to use ChatLink."
            )
            return redirect("register")


        # -----------------------------
        # Clean old OTPs
        # -----------------------------
        PendingOTP.objects.filter(identifier=identifier).delete()

        # -----------------------------
        # Create & send OTP
        # -----------------------------
        otp_obj = PendingOTP.objects.create(identifier=identifier)
        otp_obj.generate_otp()

        if "@" in identifier:
            send_mail(
                subject="ChatLink OTP Verification",
                message=f"Your OTP is {otp_obj.otp}",
                from_email=None,
                recipient_list=[identifier],
            )
        else:
            # SMS integration later
            print(f"OTP for mobile {identifier}: {otp_obj.otp}")

        # -----------------------------
        # Store all pending data in session
        # -----------------------------
        request.session["pending_full_name"] = full_name
        request.session["pending_username"] = username
        request.session["pending_identifier"] = identifier
        request.session["pending_dob"] = dob_str
        request.session["pending_country"] = country
        request.session["pending_native_language"] = native_language
        request.session["pending_learning_language"] = learning_language

        messages.success(request, "OTP sent successfully.")
        return redirect("otp_verify")

    # -----------------------------
    # GET request → render form
    # -----------------------------
    return render(
        request,
        "users/register.html",
        {
            "languages": get_all_languages()
        }
    )




# -----------------------------------------------
# OTP VERIFY → CREATE USER + AUTO LOGIN
# -----------------------------------------------
@never_cache
def otp_verify_view(request):
    # Fetch pending session data
    username = request.session.get("pending_username")
    identifier = request.session.get("pending_identifier")

    full_name = request.session.get("pending_full_name")
    dob = request.session.get("pending_dob")
    country = request.session.get("pending_country")
    native_language = request.session.get("pending_native_language")
    learning_language = request.session.get("pending_learning_language")

    # Session safety check
    if not username or not identifier:
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

        # OTP expiry check
        if otp_obj.is_expired():
            otp_obj.delete()
            messages.error(request, "OTP expired. Please register again.")
            return redirect("register")

        # OTP validation
        if otp_input != otp_obj.otp:
            messages.error(request, "Invalid OTP.")
            return redirect("otp_verify")

        # Password validation
        if not password or not confirm_password:
            messages.error(request, "All fields are required.")
            return redirect("otp_verify")

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect("otp_verify")

        # 🔐 Critical race-condition protection
        if User.objects.filter(username=username).exists():
            messages.error(
                request,
                "Username already taken. Please register again."
            )
            return redirect("register")

        # ✅ Create user ONLY after OTP verification
        user = User.objects.create_user(
            username=username,
            password=password
        )

        # Assign identifier
        if "@" in identifier:
            user.email = identifier
        else:
            user.phone = identifier

        # Assign profile & registration data
        user.full_name = full_name
        user.date_of_birth = dob
        user.country = country
        user.native_language = native_language
        user.learning_language = learning_language

        user.save()

        # Auto login
        user.backend = "django.contrib.auth.backends.ModelBackend"
        login(request, user)

        # Cleanup OTP + session
        otp_obj.delete()

        for key in [
            "pending_username",
            "pending_identifier",
            "pending_full_name",
            "pending_dob",
            "pending_country",
            "pending_native_language",
            "pending_learning_language",
        ]:
            request.session.pop(key, None)

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
    return render(request, "users/home.html", {"user": request.user})


# -------------------------------------------------
# PROFILE
# -------------------------------------------------
@never_cache
@login_required
def profile_view(request):
    return render(request, "users/profile.html", {"user": request.user})



# -------------------------------------------------
# LOGOUT
# -------------------------------------------------
@require_POST
def logout_view(request):
    logout(request)
    messages.info(request, "Logged out.")
    return redirect("login")
