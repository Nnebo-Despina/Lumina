# lumina/testutils.py
# Shared test fixture for every app's tests.
#   * a fast password hasher (production still uses Django's strong default)
#   * uploads go to a TEMPORARY folder, never into the real media/ folder
#   * ready-made people and records: self.member, self.staff, self.category,
#     self.book_type, self.book (a published book WITH a PDF and 2 copies), self.video

import atexit
import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

from accounts.models import User
from catalogue.models import Book, BookCopy, BookType, Category, Video

PASSWORD = "Sunrise-Library-42"
TEST_MEDIA = tempfile.mkdtemp(prefix="lumina-test-media-")
atexit.register(shutil.rmtree, TEST_MEDIA, ignore_errors=True)

# Pages are looked up with these tokens in route lists, e.g. ("library:read", ["BOOK"])
FIXTURE = {}


def pdf(name="sample.pdf"):
    return SimpleUploadedFile(name, b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF\n",
                              content_type="application/pdf")


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"], MEDIA_ROOT=TEST_MEDIA)
class LuminaTestCase(TestCase):
    def setUp(self):
        self.member = User.objects.create_user(email="ada@example.com", password=PASSWORD, first_name="Ada", last_name="Obi")
        self.staff = User.objects.create_user(email="admin@example.com", password=PASSWORD,
                                              first_name="Lib", last_name="Admin", is_staff=True)
        self.category = Category.objects.create(name="Fiction", slug="fiction", description="Novels")
        self.book_type = BookType.objects.create(name="Book")
        self.book = Book.objects.create(title="Sample Novel", author="A. Author", publisher="Pub House",
                                        category=self.category, book_type=self.book_type, file=pdf())
        self.copy1 = BookCopy.objects.create(book=self.book, inventory_code="LUM-0001-01")
        self.copy2 = BookCopy.objects.create(book=self.book, inventory_code="LUM-0001-02")
        self.video = Video.objects.create(title="Intro Video", category=self.category, level="ALL",
                                          video_url="https://example.com/watch")
        FIXTURE.update(BOOK=self.book.pk, VIDEO=self.video.pk)
