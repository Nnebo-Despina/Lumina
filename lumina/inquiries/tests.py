# inquiries/tests.py   (run:  python manage.py test inquiries)

from django.urls import reverse

from lumina.testutils import LuminaTestCase

from .models import Inquiry


class ContactFormTests(LuminaTestCase):
    data = {"name": "Visitor", "email": "visitor@example.com", "subject": "membership",
            "message": "How long does approval take?"}

    def test_a_guest_can_send_an_inquiry(self):
        r = self.client.post(reverse("inquiries:contact"), self.data, follow=True)
        self.assertContains(r, "Your message was sent")
        inquiry = Inquiry.objects.get()
        self.assertEqual((inquiry.status, inquiry.user, inquiry.subject), ("pending", None, "membership"))

    def test_a_member_is_prefilled_and_remembered(self):
        self.client.force_login(self.member)
        page = self.client.get(reverse("inquiries:contact"))
        self.assertEqual(page.context["form"].initial, {"name": "Ada Obi", "email": "ada@example.com"})
        self.client.post(reverse("inquiries:contact"), self.data)
        self.assertEqual(Inquiry.objects.get().user, self.member)

    def test_subject_defaults_to_general_with_no_blank_choice(self):
        form = self.client.get(reverse("inquiries:contact")).context["form"]
        self.assertEqual(form.fields["subject"].initial, "general")
        self.assertNotIn("", [value for value, _ in form.fields["subject"].choices])

    def test_short_or_invalid_messages_are_rejected(self):
        r = self.client.post(reverse("inquiries:contact"), dict(self.data, message="Hi"))
        self.assertContains(r, "at least 10 characters")
        r = self.client.post(reverse("inquiries:contact"), dict(self.data, email="nope"))
        self.assertEqual(Inquiry.objects.count(), 0)


class InboxTests(LuminaTestCase):
    def setUp(self):
        super().setUp()
        self.new = Inquiry.objects.create(name="A", email="a@example.com", subject="general", message="Open question here")
        self.old = Inquiry.objects.create(name="B", email="b@example.com", subject="problem", message="Fixed already ok",
                                          status=Inquiry.Status.ANSWERED)
        self.client.force_login(self.staff)

    def test_inbox_lists_and_filters_by_status(self):
        url = reverse("inquiries:manage_inquiries")
        r = self.client.get(url)
        self.assertContains(r, "Open question here")
        self.assertEqual(r.context["pending_total"], 1)
        self.assertNotContains(self.client.get(url, {"status": "pending"}), "Fixed already ok")
        self.assertNotContains(self.client.get(url, {"status": "answered"}), "Open question here")

    def test_mark_answered_sets_the_time(self):
        url = reverse("inquiries:manage_inquiry_answered", args=[self.new.pk])
        self.assertEqual(self.client.get(url).status_code, 405)
        self.client.post(url)
        self.new.refresh_from_db()
        self.assertEqual(self.new.status, "answered")
        self.assertIsNotNone(self.new.answered_at)

    def test_status_choices_are_the_right_ones(self):
        """Regression: status used to point at the subject choices, so 'pending' was invalid."""
        self.new.full_clean()
        self.assertEqual([c[0] for c in Inquiry._meta.get_field("status").choices], ["pending", "answered"])

    def test_members_cannot_open_the_inbox(self):
        self.client.force_login(self.member)
        self.assertEqual(self.client.get(reverse("inquiries:manage_inquiries")).status_code, 403)
        self.assertEqual(self.client.post(reverse("inquiries:manage_inquiry_answered", args=[self.new.pk])).status_code, 403)
