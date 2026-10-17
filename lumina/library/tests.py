# library/tests.py   (run:  python manage.py test library)

import importlib
import os

from django.test import override_settings
from django.urls import clear_url_caches, reverse

from catalogue.models import Category, Statuses, Video
from lumina.testutils import TEST_MEDIA, LuminaTestCase, pdf

from .models import DownloadLog, ReadingProgress, VideoView


class ReaderTests(LuminaTestCase):
    def test_reader_needs_login(self):
        r = self.client.get(reverse("library:read", args=[self.book.pk]))
        self.assertEqual(r.status_code, 302)
        self.assertIn(reverse("accounts:login"), r["Location"])

    def test_opening_the_reader_creates_progress_and_shows_the_frame(self):
        self.client.force_login(self.member)
        r = self.client.get(reverse("library:read", args=[self.book.pk]))
        self.assertContains(r, f'src="{reverse("library:file", args=[self.book.pk])}#page=1"')
        self.assertEqual(ReadingProgress.objects.get(user=self.member, book=self.book).last_page, 1)

    def test_save_my_place(self):
        self.client.force_login(self.member)
        url = reverse("library:save_progress", args=[self.book.pk])
        self.assertEqual(self.client.get(url).status_code, 405)
        self.client.post(url, {"page": "42"})
        self.assertEqual(ReadingProgress.objects.get(user=self.member, book=self.book).last_page, 42)
        self.client.post(url, {"page": "abc"})                      # nonsense becomes page 1, not an error
        self.assertEqual(ReadingProgress.objects.get(user=self.member, book=self.book).last_page, 1)
        self.assertEqual(ReadingProgress.objects.count(), 1)
        r = self.client.get(reverse("library:read", args=[self.book.pk]))
        self.assertContains(r, "#page=1")

    def test_progress_is_private_to_each_member(self):
        self.client.force_login(self.member)
        self.client.post(reverse("library:save_progress", args=[self.book.pk]), {"page": "9"})
        self.client.force_login(self.staff)
        self.assertEqual(self.client.get(reverse("library:read", args=[self.book.pk])).context["progress"].last_page, 1)

    def test_draft_or_fileless_books_cannot_be_read(self):
        self.client.force_login(self.member)
        self.book.status = Statuses.DRAFT; self.book.save()
        self.assertEqual(self.client.get(reverse("library:read", args=[self.book.pk])).status_code, 404)
        self.book.status = Statuses.LIVE; self.book.file = ""; self.book.save()
        self.assertEqual(self.client.get(reverse("library:read", args=[self.book.pk])).status_code, 404)


class ProtectedFileTests(LuminaTestCase):
    def test_pdf_is_only_for_members_and_can_be_framed_by_our_own_pages(self):
        url = reverse("library:file", args=[self.book.pk])
        self.assertEqual(self.client.get(url).status_code, 302)           # guests: sent to login
        self.client.force_login(self.member)
        r = self.client.get(url)
        self.assertEqual(r["Content-Type"], "application/pdf")
        self.assertTrue(b"".join(r.streaming_content).startswith(b"%PDF"))
        self.assertEqual(r["X-Frame-Options"], "SAMEORIGIN")
        self.assertTrue(r["Content-Disposition"].startswith("inline"))

    def test_blocked_member_cannot_get_the_pdf(self):
        self.client.force_login(self.member)
        type(self.member).objects.filter(pk=self.member.pk).update(is_blocked=True)
        r = self.client.get(reverse("library:file", args=[self.book.pk]))
        self.assertRedirects(r, reverse("accounts:login"))

    def test_media_folder_never_serves_book_pdfs(self):
        """Only covers/ and thumbnails/ are public; books/ and videos/ are not."""
        os.makedirs(os.path.join(TEST_MEDIA, "covers"), exist_ok=True)
        with open(os.path.join(TEST_MEDIA, "covers", "c.txt"), "w") as f:
            f.write("cover")
        import lumina.urls
        with override_settings(DEBUG=True):
            importlib.reload(lumina.urls); clear_url_caches()
            try:
                self.assertEqual(self.client.get("/media/covers/c.txt").status_code, 200)
                self.assertEqual(self.client.get(f"/media/{self.book.file.name}").status_code, 404)
                self.assertEqual(self.client.get("/media/videos/anything.mp4").status_code, 404)
            finally:
                pass
        importlib.reload(lumina.urls); clear_url_caches()


class DownloadTests(LuminaTestCase):
    def url(self):
        return reverse("library:download", args=[self.book.pk])

    def test_guest_is_sent_to_login(self):
        self.assertEqual(self.client.get(self.url()).status_code, 302)

    def test_forbidden_when_the_admin_has_not_allowed_it(self):
        self.client.force_login(self.member)
        self.assertEqual(self.client.get(self.url()).status_code, 403)
        self.assertEqual(DownloadLog.objects.count(), 0)

    def test_allowed_download_is_an_attachment_and_is_logged(self):
        self.book.download_permission = "allow"; self.book.save()
        self.client.force_login(self.member)
        r = self.client.get(self.url())
        self.assertEqual(r.status_code, 200)
        self.assertIn("attachment", r["Content-Disposition"])
        self.assertEqual(DownloadLog.objects.filter(user=self.member, book=self.book).count(), 1)

    def test_category_switch_allows_downloads_for_inherited_books(self):
        Category.objects.filter(pk=self.category.pk).update(allow_download=True)
        self.client.force_login(self.member)
        self.assertEqual(self.client.get(self.url()).status_code, 200)
        self.book.download_permission = "deny"; self.book.save()          # the book's own setting wins
        self.assertEqual(self.client.get(self.url()).status_code, 403)

    def test_download_button_follows_the_rule(self):
        self.client.force_login(self.member)
        page = reverse("catalogue:book_detail", args=[self.book.pk])
        self.assertNotContains(self.client.get(page), "Download PDF")
        self.book.download_permission = "allow"; self.book.save()
        self.assertContains(self.client.get(page), "Download PDF")


class WatchTests(LuminaTestCase):
    def test_watching_redirects_to_the_link_and_is_counted_once(self):
        self.client.force_login(self.member)
        url = reverse("library:watch", args=[self.video.pk])
        r = self.client.get(url)
        self.assertRedirects(r, "https://example.com/watch", fetch_redirect_response=False)
        self.client.get(url)
        self.assertEqual(VideoView.objects.filter(user=self.member, video=self.video).count(), 1)

    def test_uploaded_video_files_are_served_to_members_only(self):
        video = Video.objects.create(title="Upload", category=self.category, level="ALL", video_file=pdf("clip.mp4"))
        url = reverse("library:watch", args=[video.pk])
        self.assertEqual(self.client.get(url).status_code, 302)
        self.client.force_login(self.member)
        self.assertEqual(self.client.get(url).status_code, 200)

    def test_drafts_and_empty_videos_are_not_found(self):
        self.client.force_login(self.member)
        Video.objects.filter(pk=self.video.pk).update(status=Statuses.DRAFT)
        self.assertEqual(self.client.get(reverse("library:watch", args=[self.video.pk])).status_code, 404)


class AccountPageTests(LuminaTestCase):
    def test_dashboard_numbers_and_lists(self):
        ReadingProgress.objects.create(user=self.member, book=self.book, last_page=7)
        DownloadLog.objects.create(user=self.member, book=self.book)
        VideoView.objects.create(user=self.member, video=self.video)
        self.client.force_login(self.member)
        r = self.client.get(reverse("library:account"))
        self.assertEqual((r.context["books_read"], r.context["downloads"], r.context["videos_watched"]), (1, 1, 1))
        self.assertContains(r, "Sample Novel")
        self.assertContains(r, "page 7")
