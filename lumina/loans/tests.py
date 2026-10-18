# loans/tests.py   (run:  python manage.py test loans)

from datetime import timedelta

from django.db import IntegrityError, transaction
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from catalogue.models import BookCopy
from lumina.testutils import LuminaTestCase

from .models import BookIssue


def issue(user, copy, staff, days=7):
    obj = BookIssue(user=user, copy=copy, issued_by=staff, due_date=timezone.localdate() + timedelta(days=days))
    obj.save()
    return obj


class IssueBookTests(LuminaTestCase):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.staff)
        self.url = reverse("loans:manage_issue_new")
        self.good = {"user": self.member.pk, "copy": self.copy1.pk, "notes": "",
                     "due_date": (timezone.localdate() + timedelta(days=14)).isoformat()}

    def test_issuing_creates_the_loan_and_puts_the_copy_on_loan(self):
        r = self.client.post(self.url, self.good, follow=True)
        self.assertContains(r, "was issued to Ada Obi")
        loan = BookIssue.objects.get()
        self.assertEqual((loan.user, loan.issued_by, loan.status), (self.member, self.staff, "issued"))
        self.copy1.refresh_from_db()
        self.assertEqual(self.copy1.status, BookCopy.Status.ON_LOAN)

    def test_form_offers_only_unblocked_members_and_available_copies(self):
        User.objects.create_user(email="blocked@example.com", password="x", first_name="B", last_name="L", is_blocked=True)
        BookCopy.objects.filter(pk=self.copy2.pk).update(status=BookCopy.Status.MAINTENANCE)
        form = self.client.get(self.url).context["form"]
        self.assertNotIn("blocked@example.com", [u.email for u in form.fields["user"].queryset])
        self.assertEqual(list(form.fields["copy"].queryset), [self.copy1])

    def test_blocked_member_and_unavailable_copy_are_rejected_even_if_forced(self):
        blocked = User.objects.create_user(email="b@example.com", password="x", is_blocked=True)
        self.assertEqual(self.client.post(self.url, dict(self.good, user=blocked.pk)).status_code, 200)
        BookCopy.objects.filter(pk=self.copy1.pk).update(status=BookCopy.Status.LOST)
        self.assertEqual(self.client.post(self.url, self.good).status_code, 200)
        self.assertEqual(BookIssue.objects.count(), 0)

    def test_due_date_must_be_after_today(self):
        r = self.client.post(self.url, dict(self.good, due_date=timezone.localdate().isoformat()))
        self.assertContains(r, "due date must be after today")
        self.assertEqual(BookIssue.objects.count(), 0)

    def test_a_copy_can_only_have_one_active_loan(self):
        issue(self.member, self.copy1, self.staff)
        with self.assertRaises(IntegrityError), transaction.atomic():
            BookIssue.objects.create(user=self.staff, copy=self.copy1, issued_by=self.staff,
                                     due_date=timezone.localdate() + timedelta(days=3))

    def test_members_cannot_issue_books_to_themselves(self):
        self.client.force_login(self.member)
        self.assertEqual(self.client.post(self.url, self.good).status_code, 403)
        self.assertEqual(BookIssue.objects.count(), 0)


class ReturnAndRegisterTests(LuminaTestCase):
    def setUp(self):
        super().setUp()
        self.loan = issue(self.member, self.copy1, self.staff)
        self.client.force_login(self.staff)

    def test_marking_returned_frees_the_copy(self):
        url = reverse("loans:manage_issue_return", args=[self.loan.pk])
        self.assertEqual(self.client.get(url).status_code, 405)
        self.client.post(url)
        self.loan.refresh_from_db(); self.copy1.refresh_from_db()
        self.assertEqual(self.loan.status, "returned")
        self.assertIsNotNone(self.loan.returned_at)
        self.assertEqual(self.copy1.status, BookCopy.Status.AVAILABLE)

    def test_register_shows_stats_and_flags_overdue_loans(self):
        BookIssue.objects.filter(pk=self.loan.pk).update(due_date=timezone.localdate() - timedelta(days=3))
        r = self.client.get(reverse("loans:manage_issues"))
        self.assertEqual((r.context["stats"]["on_loan"], r.context["stats"]["overdue"]), (1, 1))
        self.assertContains(r, 'data-status="overdue"')
        self.assertContains(r, "LUM-0001-01")

    def test_dashboard_shows_loan_numbers(self):
        r = self.client.get(reverse("catalogue:manage_dashboard"))
        self.assertEqual((r.context["on_loan"], r.context["overdue"]), (1, 0))

    def test_only_admins_can_see_the_register_or_return_books(self):
        self.client.force_login(self.member)
        self.assertEqual(self.client.get(reverse("loans:manage_issues")).status_code, 403)
        self.assertEqual(self.client.post(reverse("loans:manage_issue_return", args=[self.loan.pk])).status_code, 403)
        self.loan.refresh_from_db()
        self.assertEqual(self.loan.status, "issued")


class MyLoansTests(LuminaTestCase):
    def test_a_member_sees_only_their_own_loans(self):
        other = User.objects.create_user(email="other@example.com", password="x", first_name="Other", last_name="Reader")
        mine = issue(self.member, self.copy1, self.staff)
        theirs = issue(other, self.copy2, self.staff)
        self.client.force_login(self.member)
        r = self.client.get(reverse("loans:my_loans"))
        self.assertEqual(list(r.context["loans"]), [mine])
        self.assertNotContains(r, "LUM-0001-02")

    def test_counts_and_overdue_label(self):
        loan = issue(self.member, self.copy1, self.staff)
        BookIssue.objects.filter(pk=loan.pk).update(due_date=timezone.localdate() - timedelta(days=2))
        done = issue(self.member, self.copy2, self.staff)
        done.mark_returned()
        self.client.force_login(self.member)
        r = self.client.get(reverse("loans:my_loans"))
        self.assertEqual((r.context["current_count"], r.context["overdue_count"], r.context["returned_count"]), (1, 1, 1))
        self.assertContains(r, "Overdue")

    def test_guests_are_sent_to_login(self):
        self.assertEqual(self.client.get(reverse("loans:my_loans")).status_code, 302)
