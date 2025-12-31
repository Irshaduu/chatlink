# 💬 ChatLink

**ChatLink** is a backend-focused communication platform where users connect with others based on language preferences.

This project is built as a **learning + portfolio project** with a strong focus on **real-world backend architecture**, security, and clean Django practices — not as a rushed demo app.

---

## 🎯 Project Objectives

- Practice Django from **foundation to advanced backend concepts**
- Build a **production-oriented authentication and onboarding system**
- Gain hands-on experience with:
  - Custom user models
  - OTP-based authentication
  - Secure session handling
  - Scalable data modeling
- Prepare confidently for **backend developer interviews**

---

## 🔐 Authentication & Registration (Implemented)

ChatLink uses a **security-first, OTP-based authentication flow**.

### ✔ Implemented Features

- ✅ Custom User model (`AbstractUser`)
- ✅ OTP-based registration (Email or Mobile)
- ✅ OTP-based password reset
- ✅ Login via Username / Email / Mobile
- ✅ OTP-first architecture (no half-created users)
- ✅ Session-safe account creation & cleanup
- ✅ Age validation (**13+ only**)
- ✅ Country selection (ISO standard)
- ✅ Native & learning language preferences (ISO codes)
- ✅ Secure logout (POST + CSRF)
- ✅ Cache-safe protected pages

> User accounts are created **only after OTP verification**, preventing incomplete or ghost users.

---

## 👤 Profile System

### Current
- ✅ View profile

### In Progress
- 🔄 Edit profile details
- 🔄 Update language preferences
- 🔄 Profile picture upload

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
- **Python:** 3.11.9  
- **Django:** 4.2 (LTS)  
- **Authentication:** Custom OTP-based system  
- **Countries:** `django-countries`  
- **Languages:** `pycountry`

### Planned Extensions
- **API:** Django REST Framework
- **Realtime:** Django Channels
- **Cache / Broker:** Redis
- **Background Tasks:** Celery
- **Deployment:** Docker + Cloud/VPS

---

## 🧱 Architecture Principles

- OTP-first user creation
- No partial database writes
- No insecure password handling
- Clear separation of concerns
- Feature-based Git commits
- Production-safe patterns from day one

---

## 📦 Project Status

- **Current Phase:** Authentication & Registration (Completed)
- **Next Phase:** Profile Editing & Media
- **Future Phases:** Matching, Chat, Realtime Communication

---

## 📌 Notes

This project is intentionally developed **step by step** to emphasize **correctness, security, and scalability**, rather than fast completion.

---

## 👨‍💻 Author

Built as a **learning-driven backend project** to strengthen Django, system design, and real-world backend skills.
