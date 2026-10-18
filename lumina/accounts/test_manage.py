# accounts/test_manage.py   - member management by the administrator
# (run:  python manage.py test accounts)

from datetime import timedelta

from django.urls import reverse
from django.utils import timezone

from loans.models import BookIssue
from lumina.testutils import LuminaTestCase

from .models import User


class MemberManagementTests(LuminaTestCase):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.staff)

    def test_list_shows_members_but_never_administrators(self):
        r = self.client.get(reverse("accounts:manage_members"))
        self.assertContains(r, "ada@example.com")
        self.assertNotContains(r, "admin@example.com</td>")
        self.assertEqual(r.context["total"], 1)

    def test_search_and_filters(self):
        User.objects.create_user(email="bola@example.com", password="x", first_name="Bola", last_name="T",
                                 role="teacher", is_blocked=True)
        url = reverse("accounts:manage_members")
        self.assertEqual([m.email for m in self.client.get(url, {"q": "bola"}).context["members"]], ["bola@example.com"])
        self.assertEqual([m.email for m in self.client.get(url, {"status": "blocked"}).context["members"]], ["bola@example.com"])
        self.assertEqual([m.email for m in self.client.get(url, {"status": "active"}).context["members"]], ["ada@example.com"])
        self.assertEqual([m.email for m in self.client.get(url, {"role": "teacher"}).context["members"]], ["bola@example.com"])

    def test_block_then_unblock(self):
        self.client.post(reverse("accounts:manage_member_block", args=[self.member.pk]))
        self.member.refresh_from_db()
        self.assertTrue(self.member.is_blocked)
        # ...and the blocked member really cannot log in any more
        self.client.logout()
        r = self.client.post(reverse("accounts:login"), {"username": "ada@example.com", "password": "Sunrise-Library-42"})
        self.assertContains(r, "has been blocked")
        self.client.force_login(self.staff)
        self.client.post(reverse("accounts:manage_member_unblock", args=[self.member.pk]))
        self.member.refresh_from_db()
        self.assertFalse(self.member.is_blocked)

    def test_administrators_cannot_be_blocked_or_deleted(self):
        for name in ("block", "unblock", "delete"):
            r = self.client.post(reverse(f"accounts:manage_member_{name}", args=[self.staff.pk]))
            self.assertEqual(r.status_code, 404, name)
        self.assertTrue(User.objects.get(pk=self.staff.pk).is_staff)

    def test_delete_member_and_the_loan_history_guard(self):
        self.client.post(reverse("accounts:manage_member_delete", args=[self.member.pk]))
        self.assertFalse(User.objects.filter(pk=self.member.pk).exists())

        lender = User.objects.create_user(email="l@example.com", password="x")
        BookIssue(user=lender, copy=self.copy1, issued_by=self.staff, due_date=timezone.localdate() + timedelta(days=5)).save()
        r = self.client.post(reverse("accounts:manage_member_delete", args=[lender.pk]), follow=True)
        self.assertContains(r, "has loan records")
        self.assertTrue(User.objects.filter(pk=lender.pk).exists())

    def test_on_loan_column(self):
        BookIssue(user=self.member, copy=self.copy1, issued_by=self.staff, due_date=timezone.localdate() + timedelta(days=5)).save()
        self.assertEqual(self.client.get(reverse("accounts:manage_members")).context["members"][0].on_loan, 1)

    def test_members_cannot_manage_members(self):
        other = User.objects.create_user(email="o@example.com", password="x")
        self.client.force_login(self.member)
        self.assertEqual(self.client.post(reverse("accounts:manage_member_block", args=[other.pk])).status_code, 403)
        other.refresh_from_db()
        self.assertFalse(other.is_blocked)
