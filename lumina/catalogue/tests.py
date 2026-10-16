# catalogue/tests.py   (run:  python manage.py test catalogue)

import csv
import io

from django.core.management import call_command
from django.urls import reverse

from lumina.testutils import LuminaTestCase, pdf

from .models import Book, BookCopy, BookType, Category, DownloadStatus, Statuses, Video
from .permissions import can_download


def make_book(category, book_type, **kw):
    defaults = dict(title="Another", author="Z. Writer", publisher="Tech Press", file="books/x.pdf")
    defaults.update(kw)
    return Book.objects.create(category=category, book_type=book_type, **defaults)


# =================================================================== PUBLIC SITE
class PublicCatalogueTests(LuminaTestCase):
    def test_home_shows_real_numbers_and_books(self):
        r = self.client.get(reverse("catalogue:home"))
        self.assertContains(r, "Sample Novel")
        self.assertEqual(r.context["item_count"], 2)          # 1 book + 1 video
        self.assertEqual(r.context["category_count"], 1)
        self.assertEqual(r.context["member_count"], 1)        # staff are not counted

    def test_drafts_are_hidden_everywhere(self):
        draft = make_book(self.category, self.book_type, title="Secret Draft", status=Statuses.DRAFT)
        self.assertNotContains(self.client.get(reverse("catalogue:books")), "Secret Draft")
        self.assertNotContains(self.client.get(reverse("catalogue:home")), "Secret Draft")
        self.assertEqual(self.client.get(reverse("catalogue:book_detail", args=[draft.pk])).status_code, 404)

    def test_search_in_all_fields_or_one(self):
        make_book(self.category, self.book_type, title="Python Guide")
        url = reverse("catalogue:books")
        self.assertContains(self.client.get(url, {"q": "python"}), "Python Guide")
        self.assertNotContains(self.client.get(url, {"q": "python"}), "Sample Novel")
        self.assertContains(self.client.get(url, {"q": "A. Author", "by": "author"}), "Sample Novel")
        self.assertNotContains(self.client.get(url, {"q": "A. Author", "by": "title"}), "Sample Novel")
        self.assertContains(self.client.get(url, {"q": "pub house", "by": "publisher"}), "Sample Novel")
        self.assertContains(self.client.get(url, {"search": "sample"}), "Sample Novel")      # older ?search= link

    def test_filter_by_category_and_type(self):
        other_cat = Category.objects.create(name="Science", slug="science")
        other_type = BookType.objects.create(name="Magazine")
        make_book(other_cat, other_type, title="Cells")
        url = reverse("catalogue:books")
        self.assertContains(self.client.get(url, {"category": "science"}), "Cells")
        self.assertNotContains(self.client.get(url, {"category": "science"}), "Sample Novel")
        self.assertContains(self.client.get(url, {"type": "Magazine"}), "Cells")
        self.assertNotContains(self.client.get(url, {"type": "Magazine"}), "Sample Novel")

    def test_pagination_keeps_filters(self):
        Book.objects.bulk_create([Book(title=f"Filler {i:02d}", author="F", category=self.category,
                                       book_type=self.book_type, file="books/f.pdf") for i in range(13)])
        r = self.client.get(reverse("catalogue:books"), {"q": "filler"})
        self.assertEqual(len(r.context["books"]), 12)
        self.assertContains(r, "q=filler&amp;page=2")
        self.assertEqual(len(self.client.get(reverse("catalogue:books"), {"q": "filler", "page": 2}).context["books"]), 1)

    def test_detail_differs_for_guests_and_members(self):
        url = reverse("catalogue:book_detail", args=[self.book.pk])
        guest = self.client.get(url)
        self.assertTemplateUsed(guest, "catalogue/book_detail.html")
        self.assertContains(guest, "Log in to read")
        self.assertContains(guest, "Physical copies: 2 of 2 available")
        self.client.force_login(self.member)
        member = self.client.get(url)
        self.assertTemplateUsed(member, "catalogue/member_book_detail.html")
        self.assertContains(member, "Read online")
        self.assertContains(member, "Download not permitted")

    def test_availability_ignores_loaned_lost_and_retired_copies(self):
        self.copy1.status = BookCopy.Status.ON_LOAN; self.copy1.save()
        self.assertContains(self.client.get(reverse("catalogue:book_detail", args=[self.book.pk])), "1 of 2 available")
        self.copy2.status = BookCopy.Status.LOST; self.copy2.save()
        self.assertContains(self.client.get(reverse("catalogue:book_detail", args=[self.book.pk])), "0 of 1 available")

    def test_videos_are_members_only_and_filterable(self):
        url = reverse("catalogue:videos")
        self.assertEqual(self.client.get(url).status_code, 302)
        self.client.force_login(self.member)
        self.assertContains(self.client.get(url), "Intro Video")
        self.assertNotContains(self.client.get(url, {"category": "nothing"}), "Intro Video")
        Video.objects.filter(pk=self.video.pk).update(status=Statuses.DRAFT)
        self.assertNotContains(self.client.get(url), "Intro Video")


# =================================================================== THE DOWNLOAD RULE
class DownloadRuleTests(LuminaTestCase):
    def check(self, permission, category_allows, expected):
        self.book.download_permission = permission
        self.book.save()
        Category.objects.filter(pk=self.category.pk).update(allow_download=category_allows)
        self.book.refresh_from_db()
        self.assertIs(can_download(self.member, self.book), expected, (permission, category_allows))

    def test_rule_table(self):
        self.check(DownloadStatus.INHERIT, False, False)    # follows the category: off
        self.check(DownloadStatus.INHERIT, True, True)      # follows the category: on
        self.check(DownloadStatus.ALLOW, False, True)       # the book beats the category
        self.check(DownloadStatus.DENY, True, False)        # the book beats the category

    def test_other_conditions(self):
        self.check(DownloadStatus.ALLOW, False, True)
        self.assertFalse(can_download(type("Anon", (), {"is_authenticated": False})(), self.book))
        self.member.is_blocked = True
        self.assertFalse(can_download(self.member, self.book))
        self.member.is_blocked = False
        Book.objects.filter(pk=self.book.pk).update(status=Statuses.DRAFT)
        self.book.refresh_from_db()
        self.assertFalse(can_download(self.member, self.book))


# =================================================================== ADMINISTRATION
class ManageCatalogueTests(LuminaTestCase):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.staff)

    # ---- categories
    def test_category_slug_is_created_and_kept_unique(self):
        url = reverse("catalogue:manage_categories")
        self.client.post(url, {"name": "Science", "description": "Facts"})
        self.client.post(url, {"name": "science!", "description": ""})
        self.assertEqual(sorted(Category.objects.exclude(pk=self.category.pk).values_list("slug", flat=True)), ["science", "science-2"])

    def test_category_edit_does_not_touch_download_switch(self):
        Category.objects.filter(pk=self.category.pk).update(allow_download=True)
        self.client.post(reverse("catalogue:manage_category_edit", args=[self.category.pk]),
                         {"name": "Fiction!", "slug": "fiction", "description": "New text"})
        self.category.refresh_from_db()
        self.assertEqual(self.category.name, "Fiction!")
        self.assertTrue(self.category.allow_download)

    def test_category_with_books_cannot_be_deleted(self):
        r = self.client.post(reverse("catalogue:manage_category_delete", args=[self.category.pk]), follow=True)
        self.assertContains(r, "still has books or videos")
        self.assertTrue(Category.objects.filter(pk=self.category.pk).exists())
        empty = Category.objects.create(name="Empty", slug="empty")
        self.client.post(reverse("catalogue:manage_category_delete", args=[empty.pk]))
        self.assertFalse(Category.objects.filter(pk=empty.pk).exists())

    def test_delete_needs_post(self):
        self.assertEqual(self.client.get(reverse("catalogue:manage_category_delete", args=[self.category.pk])).status_code, 405)

    # ---- book types
    def test_book_type_add_and_protected_delete(self):
        self.client.post(reverse("catalogue:manage_book_types"), {"name": "Audio", "description": ""})
        self.assertTrue(BookType.objects.filter(name="Audio").exists())
        r = self.client.post(reverse("catalogue:manage_book_type_delete", args=[self.book_type.pk]), follow=True)
        self.assertContains(r, "cannot be deleted")

    # ---- books
    def book_data(self, **extra):
        data = {"title": "Brand New", "author": "N. Writer", "publisher": "", "category": self.category.pk,
                "book_type": self.book_type.pk, "year": "", "pages": "", "isbn": "", "description": "",
                "download_permission": "inherit", "status": "live", "copies": "3", "file": pdf()}
        data.update(extra)
        return data

    def test_add_book_creates_copies_and_remembers_the_admin(self):
        r = self.client.post(reverse("catalogue:manage_book_add"), self.book_data(), follow=True)
        self.assertContains(r, "3 physical copies added")
        book = Book.objects.get(title="Brand New")
        self.assertEqual(book.created_by, self.staff)
        self.assertEqual(book.copies.count(), 3)
        self.assertTrue(all(c.inventory_code.startswith(f"LUM-{book.pk:04d}-") for c in book.copies.all()))

    def test_only_pdf_files_are_accepted(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        r = self.client.post(reverse("catalogue:manage_book_add"),
                             self.book_data(file=SimpleUploadedFile("x.exe", b"MZ")))
        self.assertEqual(r.status_code, 200)
        self.assertFalse(Book.objects.filter(title="Brand New").exists())

    def test_edit_book_can_add_copies_but_not_remove_them(self):
        url = reverse("catalogue:manage_book_edit", args=[self.book.pk])
        data = self.book_data(title="Sample Novel", copies="1")
        data.pop("file")                                   # keep the existing file
        self.assertContains(self.client.post(url, data), "already has 2 copies")
        data["copies"] = "4"
        self.client.post(url, data)
        self.assertEqual(self.book.copies.count(), 4)

    def test_delete_book_without_loans_removes_it_and_its_copies(self):
        self.client.post(reverse("catalogue:manage_book_delete", args=[self.book.pk]))
        self.assertFalse(Book.objects.filter(pk=self.book.pk).exists())
        self.assertEqual(BookCopy.objects.count(), 0)

    def test_delete_book_with_loan_history_is_refused(self):
        from loans.models import BookIssue
        from datetime import timedelta
        from django.utils import timezone
        BookIssue(user=self.member, copy=self.copy1, issued_by=self.staff,
                  due_date=timezone.localdate() + timedelta(days=7)).save()
        r = self.client.post(reverse("catalogue:manage_book_delete", args=[self.book.pk]), follow=True)
        self.assertContains(r, "loan history")
        self.assertTrue(Book.objects.filter(pk=self.book.pk).exists())

    def test_book_list_filters_and_paginates(self):
        make_book(self.category, self.book_type, title="Zebra Facts")
        url = reverse("catalogue:manage_books")
        self.assertContains(self.client.get(url, {"q": "zebra"}), "Zebra Facts")
        self.assertNotContains(self.client.get(url, {"q": "zebra"}), "Sample Novel")

    # ---- videos
    def test_video_needs_a_link_or_a_file(self):
        url = reverse("catalogue:manage_video_add")
        base = {"title": "T", "category": self.category.pk, "level": "ALL", "duration": "", "status": "live",
                "video_url": "", "description": ""}
        self.assertContains(self.client.post(url, base), "Give a video link or upload a video file")
        self.client.post(url, dict(base, video_url="https://example.com/v2"))
        self.assertTrue(Video.objects.filter(title="T").exists())

    def test_video_duration_format_is_checked(self):
        r = self.client.post(reverse("catalogue:manage_video_add"), {
            "title": "T", "category": self.category.pk, "level": "ALL", "duration": "abc", "status": "live",
            "video_url": "https://example.com/v"})
        self.assertContains(r, "MM:SS")

    # ---- download permissions
    def test_download_page_saves_category_switches_and_book_overrides(self):
        self.client.post(reverse("catalogue:manage_downloads"),
                         {"categories": [self.category.pk], f"book_{self.book.pk}": "deny"})
        self.category.refresh_from_db(); self.book.refresh_from_db()
        self.assertTrue(self.category.allow_download)
        self.assertEqual(self.book.download_permission, "deny")
        self.client.post(reverse("catalogue:manage_downloads"), {f"book_{self.book.pk}": "hacked"})
        self.category.refresh_from_db(); self.book.refresh_from_db()
        self.assertFalse(self.category.allow_download)             # unticked = off
        self.assertEqual(self.book.download_permission, "deny")    # invalid value ignored

    # ---- reports
    def test_report_rows_totals_and_csv(self):
        make_book(self.category, self.book_type, title="Second", download_permission="allow")
        r = self.client.get(reverse("catalogue:manage_reports"))
        self.assertEqual(r.context["rows"], [{"category": "Fiction", "books": 2, "videos": 1, "downloadable": 1, "total": 3}])
        self.assertEqual(r.context["totals"]["total"], 3)
        r = self.client.get(reverse("catalogue:manage_reports"), {"export": "csv"})
        self.assertEqual(r["Content-Type"], "text/csv")
        rows = list(csv.reader(io.StringIO(r.content.decode())))
        self.assertEqual(rows[0], ["Category", "Books", "Videos", "Downloadable", "Total"])
        self.assertEqual(rows[-1], ["Total", "2", "1", "1", "3"])

    def test_report_ignores_drafts_and_respects_dates(self):
        make_book(self.category, self.book_type, title="Hidden", status=Statuses.DRAFT)
        self.assertEqual(self.client.get(reverse("catalogue:manage_reports")).context["totals"]["books"], 1)
        self.assertEqual(self.client.get(reverse("catalogue:manage_reports"), {"to": "2000-01-01"}).context["totals"]["total"], 0)

    def test_dashboard_numbers(self):
        r = self.client.get(reverse("catalogue:manage_dashboard"))
        self.assertEqual((r.context["book_total"], r.context["video_total"], r.context["category_total"],
                          r.context["member_total"]), (1, 1, 1, 1))
        self.assertEqual(r.context["bars"][0]["peak"], True)

    def test_members_cannot_use_any_admin_action(self):
        self.client.force_login(self.member)
        for name, args in [("catalogue:manage_category_delete", [self.category.pk]),
                           ("catalogue:manage_book_delete", [self.book.pk]),
                           ("catalogue:manage_video_delete", [self.video.pk])]:
            self.assertEqual(self.client.post(reverse(name, args=args)).status_code, 403, name)
        self.assertTrue(Book.objects.filter(pk=self.book.pk).exists())


# =================================================================== SAMPLE DATA COMMAND
class SeedCommandTests(LuminaTestCase):
    def test_seed_demo_runs_twice_without_duplicates(self):
        from loans.models import BookIssue
        call_command("seed_demo", stdout=io.StringIO())
        books, copies, loans = Book.objects.count(), BookCopy.objects.count(), BookIssue.objects.count()
        call_command("seed_demo", stdout=io.StringIO())
        self.assertEqual((Book.objects.count(), BookCopy.objects.count(), BookIssue.objects.count()), (books, copies, loans))
        self.assertEqual(loans, 3)
        self.assertEqual(BookIssue.objects.filter(status="issued", due_date__lt=__import__("django").utils.timezone.localdate()).count(), 1)
