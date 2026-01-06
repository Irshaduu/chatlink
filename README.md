# 💬 ChatLink

**ChatLink** is a backend-focused communication platform designed to connect users based on language preferences.

This project is built as a **learning-driven, production-oriented backend system**, with strong emphasis on **security, correctness, and real-world Django architecture** — not as a rushed demo or tutorial app.

---

## 🎯 Project Goals

- Master Django from **core fundamentals to advanced backend patterns**
- Design a **secure, OTP-first authentication system**
- Apply **production-grade thinking** from day one
- Build a backend suitable for **real users, real data, and real scaling**
- Prepare confidently for **backend & full-stack developer interviews**

---

## 🔐 Authentication & Onboarding (Completed)

ChatLink uses a **security-first, OTP-based authentication architecture**.

### ✔ Implemented Features

- ✅ Custom `User` model (`AbstractUser`)
- ✅ OTP-based registration (Email or Mobile)
- ✅ OTP-based password reset
- ✅ Login via Username / Email / Phone
- ✅ OTP-first account creation (no ghost users)
- ✅ Secure session lifecycle management
- ✅ Attempt limits & resend throttling
- ✅ OTP expiry enforcement
- ✅ Identifier uniqueness (Email & Phone)
- ✅ Age validation (**13+ only**)
- ✅ Country selection (ISO standard)
- ✅ Native & learning language preferences
- ✅ POST-only logout with CSRF protection
- ✅ Cache-safe protected views

> User accounts are created **only after successful OTP verification**, ensuring database integrity and preventing partial or abandoned users.

---

## 🧠 OTP Security Model

ChatLink implements a **hardened OTP lifecycle**:

- Limited OTP attempts per session
- Limited free OTP resends
- Cooldown enforcement after free resends
- Automatic cleanup of expired or abused OTPs
- Separate OTP models for:
  - Registration
  - Password reset

This design prevents:
- OTP brute-forcing
- Abuse via repeated resend requests
- Infinite verification loops

---

## 👤 Profile System

### Current
- ✅ View profile

### In Progress
- 🔄 Edit profile details
- 🔄 Language update cooldown logic
- 🔄 Profile media support

---

## 🌍 Matching & Communication (Planned)

- 🔄 Language-based user matching
- 🔄 One-to-one chat system
- 🔄 Real-time messaging (WebSockets)
- 🔄 Voice & video calls (WebRTC)
- 🔄 Live message translation
- 🔄 User moments / media sharing

---

## 🛠 Tech Stack

### Backend
- **Python:** 3.11  
- **Django:** 4.2 (LTS)  
- **Auth System:** Custom OTP-based authentication  
- **Countries:** `django-countries`  
- **Languages:** `pycountry`

### Planned Extensions
- **API Layer:** Django REST Framework
- **Realtime:** Django Channels
- **Cache / Broker:** Redis
- **Background Tasks:** Celery
- **Deployment:** Docker + VPS / Cloud

---

## 🧱 Architecture Principles

- OTP-first onboarding
- No partial database writes
- No insecure credential handling
- Explicit session control
- Clear separation of concerns
- Feature-scoped Git commits
- Refactor-friendly code structure
- Production-safe patterns from day one

---

## 📦 Project Status

- **Current Phase:** Authentication & OTP Security ✅
- **Next Phase:** Profile Editing & Media
- **Upcoming Phases:** Matching, Chat, Realtime Communication

---

## 📌 Philosophy

This project is intentionally developed **slowly and correctly**, prioritizing:

- Security over shortcuts
- Clarity over cleverness
- Architecture over hacks

The goal is not just *“it works”*, but *“it works safely, predictably, and scalably.”*

---

## 👨‍💻 Author

Built as a **learning-driven backend project** to strengthen:

- Django internals
- Authentication system design
- Secure backend workflows
- Real-world engineering discipline
