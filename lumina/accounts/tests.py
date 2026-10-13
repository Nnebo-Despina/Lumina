# accounts/tests.py
# Automated checks for authentication, permissions and the page wiring.
# Run them with:   python manage.py test accounts

import re

from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import User

PASSWORD = "Sunrise-Library-42"

# --- every page of the site, grouped by who may open it -----------------------
PUBLIC = [
    ("catalogue:home", []), ("catalogue:about", []), ("catalogue:books", []),
    ("catalogue:book_detail", [1]), ("inquiries:contact", []),
    ("accounts:login", []), ("accounts:register", []), ("accounts:forgot_password", []),
    ("accounts:admin_login", []), ("accounts:admin_forgot_password", []),
]
MEMBER = [
    ("catalogue:videos", []), ("library:account", []), ("library:read", [1]),
    ("loans:my_loans", []), ("accounts:profile", []), ("accounts:change_password", []),
]
ADMIN = [
    ("catalogue:manage_dashboard", []), ("catalogue:manage_categories", []),
    ("catalogue:manage_book_types", []), ("catalogue:manage_books", []),
    ("catalogue:manage_book_add", []), ("catalogue:manage_book_edit", [1]),
    ("catalogue:manage_videos", []), ("catalogue:manage_video_add", []),
    ("catalogue:manage_video_edit", [1]), ("catalogue:manage_downloads", []),
    ("catalogue:manage_reports", []), ("loans:manage_issues", []),
    ("loans:manage_issue_new", []), ("accounts:manage_members", []),
    ("inquiries:manage_inquiries", []), ("accounts:admin_profile", []),
]


def url(name, args):
    return reverse(name, args=args)


# A fast password hasher keeps the test run short (production still uses Django's strong default)
@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class Base(TestCase):
    def setUp(self):
        self.member = User.objects.create_user(
            email="ada@example.com", password=PASSWORD, first_name="Ada", last_name="Obi")
        self.staff = User.objects.create_user(
            email="admin@example.com", password=PASSWORD, first_name="Lib", last_name="Admin",
            is_staff=True)


class PageWiringTests(Base):
    """Every route renders, and the right people can open it."""

    def test_public_pages_open_for_guests(self):
        for name, args in PUBLIC:
            with self.subTest(name):
                self.assertEqual(self.client.get(url(name, args)).status_code, 200)

    def test_member_pages_send_guests_to_login(self):
        for name, args in MEMBER:
            with self.subTest(name):
                r = self.client.get(url(name, args))
                self.assertRedirects(r, f"{reverse('accounts:login')}?next={url(name, args)}")

    def test_admin_pages_send_guests_to_admin_login(self):
        for name, args in ADMIN:
            with self.subTest(name):
                r = self.client.get(url(name, args))
                self.assertRedirects(r, f"{reverse('accounts:admin_login')}?next={url(name, args)}")

    def test_member_pages_open_for_members(self):
        self.client.force_login(self.member)
        for name, args in MEMBER:
            with self.subTest(name):
                self.assertEqual(self.client.get(url(name, args)).status_code, 200)

    def test_members_are_forbidden_from_admin_pages(self):
        self.client.force_login(self.member)
        for name, args in ADMIN:
            with self.subTest(name):
                self.assertEqual(self.client.get(url(name, args)).status_code, 403)

    def test_staff_open_admin_pages(self):
        self.client.force_login(self.staff)
        for name, args in ADMIN:
            with self.subTest(name):
                self.assertEqual(self.client.get(url(name, args)).status_code, 200)

    def test_unknown_page_uses_friendly_404(self):
        r = self.client.get("/no-such-page/")
        self.assertEqual(r.status_code, 404)
        self.assertContains(r, "Page not found", status_code=404)

    def test_navigation_changes_with_login_state(self):
        guest = self.client.get(reverse("catalogue:home"))
        self.assertContains(guest, "Register")
        self.assertNotContains(guest, "Logout")

        self.client.force_login(self.member)
        member = self.client.get(reverse("catalogue:home"))
        self.assertContains(member, "My Loans")
        self.assertContains(member, "Logout")
        self.assertNotContains(member, ">Admin</a>")

        self.client.force_login(self.staff)
        self.assertContains(self.client.get(reverse("catalogue:home")), ">Admin</a>")

    def test_active_link_is_highlighted(self):
        r = self.client.get(reverse("catalogue:about"))
        self.assertContains(r, f'<a href="{reverse("catalogue:about")}" class="active">About</a>', html=False)

    def test_django_builtin_admin_still_styled(self):
        """Our admin layout lives in templates/manage/, so Django's own admin is untouched."""
        r = self.client.get("/django-admin/login/")
        self.assertContains(r, "admin/css/base.css")

    def test_every_post_form_has_csrf_token(self):
        self.client.force_login(self.staff)
        for name, args in ADMIN + MEMBER:
            r = self.client.get(url(name, args))
            html = r.content.decode()
            for form in re.findall(r"<form\b[^>]*method=\"post\"[^>]*>.*?</form>", html, re.S | re.I):
                with self.subTest(name):
                    self.assertIn("csrfmiddlewaretoken", form)


class RegistrationTests(Base):
    def data(self, **extra):
        d = {"first_name": "New", "last_name": "Reader", "email": "new@example.com", "phone": "",
             "role": "student", "password1": PASSWORD, "password2": PASSWORD, "terms": "on"}
        d.update(extra)
        return d

    def test_register_creates_member_with_hashed_password(self):
        r = self.client.post(reverse("accounts:register"), self.data())
        self.assertRedirects(r, reverse("accounts:login"))
        user = User.objects.get(email="new@example.com")
        self.assertNotEqual(user.password, PASSWORD)
        self.assertTrue(user.check_password(PASSWORD))
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_blocked)

    def test_duplicate_email_rejected_ignoring_case(self):
        r = self.client.post(reverse("accounts:register"), self.data(email="ADA@example.com"))
        self.assertContains(r, "already exists")
        self.assertEqual(User.objects.filter(email__iexact="ada@example.com").count(), 1)

    def test_password_mismatch_and_weak_password_rejected(self):
        r = self.client.post(reverse("accounts:register"), self.data(password2="Different-Pass-1"))
        self.assertContains(r, "do not match")
        r = self.client.post(reverse("accounts:register"), self.data(password1="12345678", password2="12345678"))
        self.assertFalse(User.objects.filter(email="new@example.com").exists())

    def test_terms_required(self):
        d = self.data(); d.pop("terms")
        r = self.client.post(reverse("accounts:register"), d)
        self.assertContains(r, "You must accept the library rules")

    def test_logged_in_user_is_redirected_away(self):
        self.client.force_login(self.member)
        self.assertRedirects(self.client.get(reverse("accounts:register")), reverse("library:account"))


class LoginLogoutTests(Base):
    def test_member_login_redirects_to_account(self):
        r = self.client.post(reverse("accounts:login"), {"username": "ada@example.com", "password": PASSWORD})
        self.assertRedirects(r, reverse("library:account"))

    def test_login_is_case_insensitive(self):
        r = self.client.post(reverse("accounts:login"), {"username": "ADA@Example.com", "password": PASSWORD})
        self.assertRedirects(r, reverse("library:account"))

    def test_wrong_password_rejected(self):
        r = self.client.post(reverse("accounts:login"), {"username": "ada@example.com", "password": "nope"})
        self.assertContains(r, "Incorrect email or password")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_blocked_member_cannot_log_in(self):
        self.member.is_blocked = True; self.member.save()
        r = self.client.post(reverse("accounts:login"), {"username": "ada@example.com", "password": PASSWORD})
        self.assertContains(r, "has been blocked")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_next_parameter_is_honoured(self):
        r = self.client.post(reverse("accounts:login") + "?next=/videos/",
                             {"username": "ada@example.com", "password": PASSWORD, "next": "/videos/"})
        self.assertRedirects(r, "/videos/")

    def test_unsafe_next_is_ignored(self):
        r = self.client.post(reverse("accounts:login"),
                             {"username": "ada@example.com", "password": PASSWORD, "next": "https://evil.example/"})
        self.assertRedirects(r, reverse("library:account"))

    def test_without_remember_me_session_ends_with_browser(self):
        self.client.post(reverse("accounts:login"), {"username": "ada@example.com", "password": PASSWORD})
        self.assertTrue(self.client.session.get_expire_at_browser_close())
        self.client.logout()
        self.client.post(reverse("accounts:login"),
                         {"username": "ada@example.com", "password": PASSWORD, "remember": "on"})
        self.assertFalse(self.client.session.get_expire_at_browser_close())

    def test_logout_requires_post(self):
        self.client.force_login(self.member)
        self.assertEqual(self.client.get(reverse("accounts:logout")).status_code, 405)
        r = self.client.post(reverse("accounts:logout"))
        self.assertRedirects(r, reverse("catalogue:home"))
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_member_blocked_while_logged_in_is_signed_out(self):
        self.client.force_login(self.member)
        User.objects.filter(pk=self.member.pk).update(is_blocked=True)
        r = self.client.get(reverse("library:account"))
        self.assertRedirects(r, reverse("accounts:login"))
        self.assertNotIn("_auth_user_id", self.client.session)


class AdminLoginTests(Base):
    def test_staff_login_goes_to_dashboard(self):
        r = self.client.post(reverse("accounts:admin_login"), {"username": "admin@example.com", "password": PASSWORD})
        self.assertRedirects(r, reverse("catalogue:manage_dashboard"))

    def test_member_cannot_use_admin_login(self):
        r = self.client.post(reverse("accounts:admin_login"), {"username": "ada@example.com", "password": PASSWORD})
        self.assertContains(r, "does not have administrator access")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_admin_logout_returns_to_admin_login(self):
        self.client.force_login(self.staff)
        r = self.client.post(reverse("accounts:logout"), {"next": reverse("accounts:admin_login")})
        self.assertRedirects(r, reverse("accounts:admin_login"))


class PasswordRecoveryTests(Base):
    def test_member_reset_flow(self):
        r = self.client.post(reverse("accounts:forgot_password"), {"email": "ada@example.com"}, follow=True)
        self.assertContains(r, "a reset link is on its way")
        self.assertEqual(len(mail.outbox), 1)
        link = re.search(r"https?://\S+/accounts/reset/\S+/", mail.outbox[0].body).group(0)
        path = link.split("testserver")[1]

        page = self.client.get(path, follow=True)                 # Django swaps the token for "set-password"
        self.assertContains(page, "Choose a new password")
        final = page.redirect_chain[-1][0]
        r = self.client.post(final, {"new_password1": "Brand-New-Pass-77", "new_password2": "Brand-New-Pass-77"})
        self.assertRedirects(r, reverse("accounts:login"))
        self.assertTrue(User.objects.get(pk=self.member.pk).check_password("Brand-New-Pass-77"))

    def test_unknown_email_gets_same_message_and_no_mail(self):
        r = self.client.post(reverse("accounts:forgot_password"), {"email": "ghost@example.com"}, follow=True)
        self.assertContains(r, "a reset link is on its way")
        self.assertEqual(len(mail.outbox), 0)

    def test_admin_recovery_only_emails_staff(self):
        self.client.post(reverse("accounts:admin_forgot_password"), {"email": "ada@example.com"})
        self.assertEqual(len(mail.outbox), 0)                      # a normal member: nothing sent
        self.client.post(reverse("accounts:admin_forgot_password"), {"email": "admin@example.com"})
        self.assertEqual(len(mail.outbox), 1)

    def test_invalid_reset_link_explained(self):
        r = self.client.get(reverse("accounts:reset_password", args=["bad", "bad-token"]), follow=True)
        self.assertContains(r, "This link is not valid")


class ChangePasswordAndProfileTests(Base):
    def test_change_password_keeps_user_logged_in(self):
        self.client.force_login(self.member)
        r = self.client.post(reverse("accounts:change_password"), {
            "old_password": PASSWORD, "new_password1": "Another-Pass-88", "new_password2": "Another-Pass-88"})
        self.assertRedirects(r, reverse("accounts:profile"))
        self.assertTrue(User.objects.get(pk=self.member.pk).check_password("Another-Pass-88"))
        self.assertEqual(self.client.get(reverse("accounts:profile")).status_code, 200)   # still logged in

    def test_wrong_current_password_rejected(self):
        self.client.force_login(self.member)
        r = self.client.post(reverse("accounts:change_password"), {
            "old_password": "wrong", "new_password1": "Another-Pass-88", "new_password2": "Another-Pass-88"})
        self.assertContains(r, "old password was entered incorrectly")

    def test_profile_update(self):
        self.client.force_login(self.member)
        r = self.client.post(reverse("accounts:profile"), {
            "first_name": "Adaeze", "last_name": "Obi", "email": "ADA@example.com",
            "phone": "+234 800 000 0000", "role": "teacher"})
        self.assertRedirects(r, reverse("accounts:profile"))
        self.member.refresh_from_db()
        self.assertEqual((self.member.first_name, self.member.role, self.member.email),
                         ("Adaeze", "teacher", "ada@example.com"))

    def test_profile_cannot_take_another_members_email(self):
        self.client.force_login(self.member)
        r = self.client.post(reverse("accounts:profile"), {
            "first_name": "Ada", "last_name": "Obi", "email": "admin@example.com", "phone": "", "role": "student"})
        self.assertContains(r, "Another account already uses this email")

    def test_profile_page_shows_real_counts(self):
        self.client.force_login(self.member)
        r = self.client.get(reverse("accounts:profile"))
        self.assertEqual((r.context["books_read"], r.context["downloads"], r.context["on_loan"]), (0, 0, 0))

    def test_admin_profile_and_password(self):
        self.client.force_login(self.staff)
        r = self.client.post(reverse("accounts:admin_profile"), {
            "save_profile": "1", "first_name": "Head", "last_name": "Librarian",
            "email": "admin@example.com", "phone": ""})
        self.assertRedirects(r, reverse("accounts:admin_profile"))
        self.staff.refresh_from_db(); self.assertEqual(self.staff.first_name, "Head")
        r = self.client.post(reverse("accounts:admin_profile"), {
            "change_password": "1", "old_password": PASSWORD,
            "new_password1": "Admin-Pass-2026-x", "new_password2": "Admin-Pass-2026-x"})
        self.assertRedirects(r, reverse("accounts:admin_profile"))
        self.assertTrue(User.objects.get(pk=self.staff.pk).check_password("Admin-Pass-2026-x"))
