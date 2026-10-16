# catalogue/management/commands/seed_demo.py
# Fills an EMPTY database with sample data so every page has something to show:
#   categories, book types, 15 books (each with a small real PDF), physical copies,
#   6 videos, demo members, one administrator (if none exists) and 3 loans.
#
#   python manage.py seed_demo
#
# Safe to run twice: it skips anything that already exists.
# Demo logins (all use the password printed at the end).

from datetime import timedelta

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import User
from catalogue.models import Book, BookCopy, BookType, Category, DownloadStatus, Video
from loans.models import BookIssue

PASSWORD = "Demo-Pass-2026"

CATEGORIES = [
    ("literature", "Literature & Fiction", "Novels, short stories and poetry from Africa and beyond.", False),
    ("technology", "Technology & Programming", "Coding, databases, web design and IT fundamentals.", True),
    ("science", "Science & Nature", "Physics, biology, environment and everyday discovery.", False),
    ("history", "History & Politics", "Africa's past, world affairs and civic thinking.", False),
    ("self", "Self-Development", "Study skills, wellbeing, careers and personal growth.", True),
    ("children", "Children & Young Adults", "Gentle, imaginative reads for younger readers.", True),
]
# title, author, publisher, category slug, year, pages, download setting, copies, description
BOOKS = [
    ("Things Fall Apart", "Chinua Achebe", "Heinemann", "literature", 1958, 209, "inherit", 4, "A landmark novel of Igbo life and the arrival of colonial rule."),
    ("Half of a Yellow Sun", "Chimamanda Ngozi Adichie", "Fourth Estate", "literature", 2006, 433, "inherit", 3, "Three lives are swept up in the Nigerian civil war."),
    ("Purple Hibiscus", "Chimamanda Ngozi Adichie", "Algonquin Books", "literature", 2003, 307, "allow", 3, "A coming-of-age story set in post-colonial Enugu."),
    ("So Long a Letter", "Mariama Ba", "Heinemann", "literature", 1979, 90, "allow", 2, "A widow's letter to a friend about love, loss and tradition."),
    ("The Concubine", "Elechi Amadi", "African Writers Series", "literature", 1966, 216, "inherit", 2, "A haunting village tale of love, fate and the gods."),
    ("Python for Beginners", "A. Okafor", "Lumina Press", "technology", 2022, 320, "inherit", 5, "A gentle first course in Python, with practice tasks."),
    ("Database Design Essentials", "N. Eze", "Lumina Press", "technology", 2021, 280, "inherit", 3, "Tables, keys and relationships explained step by step."),
    ("Responsive Web Design", "D. Okonkwo", "Aptech Books", "technology", 2023, 240, "deny", 2, "Build layouts that work on every screen with HTML and CSS."),
    ("The Living Planet", "T. Balogun", "Savanna House", "science", 2019, 350, "inherit", 2, "An accessible tour of ecosystems across the continent."),
    ("A Short History of West Africa", "K. Mensah", "Baobab Press", "history", 2015, 410, "inherit", 2, "Empires, trade routes and independence movements."),
    ("Study Smarter", "F. Adeyemi", "Lumina Press", "self", 2020, 180, "inherit", 4, "Practical habits for focus, memory and exam success."),
    ("The Tortoise and the Drum", "N. Obi", "Savanna House", "children", 2018, 48, "inherit", 2, "An illustrated folktale about patience and rhythm."),
]
VIDEOS = [
    ("Intro to Flutter: Lesson 1", "technology", "BEGINNER", "12:40"),
    ("HTML & CSS: Page Structure", "technology", "BEGINNER", "18:05"),
    ("SQL Joins Made Simple", "technology", "INTERMEDIATE", "15:22"),
    ("Revision Planning in 20 Minutes", "self", "ALL", "20:00"),
    ("Reading African Poetry Aloud", "literature", "ALL", "09:48"),
    ("How Ecosystems Work", "science", "ALL", "14:10"),
]


def make_pdf(title, pages=3):
    """A tiny but valid multi-page PDF (so the reader and downloads can be tested)."""
    esc = lambda t: t.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    font_id = 3 + 2 * pages
    objs = ["<< /Type /Catalog /Pages 2 0 R >>",
            "<< /Type /Pages /Kids [%s] /Count %d >>" % (" ".join("%d 0 R" % (3 + 2 * i) for i in range(pages)), pages)]
    for i in range(pages):
        stream = ("BT /F1 24 Tf 72 760 Td (%s) Tj ET BT /F1 14 Tf 72 720 Td (Page %d of %d - sample text for the Lumina demo.) Tj ET"
                  % (esc(title), i + 1, pages))
        objs.append("<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents %d 0 R /Resources << /Font << /F1 %d 0 R >> >> >>" % (4 + 2 * i, font_id))
        objs.append("<< /Length %d >>\nstream\n%s\nendstream" % (len(stream), stream))
    objs.append("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    out, offsets = b"%PDF-1.4\n", []
    for number, body in enumerate(objs, start=1):
        offsets.append(len(out))
        out += ("%d 0 obj\n%s\nendobj\n" % (number, body)).encode("latin-1")
    xref = len(out)
    out += ("xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1)).encode()
    out += "".join("%010d 00000 n \n" % off for off in offsets).encode()
    out += ("trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objs) + 1, xref)).encode()
    return out


class Command(BaseCommand):
    help = "Fill the database with sample data (books, PDFs, copies, videos, members, loans)."

    def handle(self, *args, **options):
        # ----- people
        admin = User.objects.filter(is_staff=True).first()
        if admin is None:
            admin = User.objects.create_superuser("admin@lumina.test", PASSWORD, first_name="Library", last_name="Admin")
            self.stdout.write("Created administrator admin@lumina.test")
        members = {}
        for email, first, last, role in [("chidera@example.com", "Chidera", "Nwosu", "student"),
                                         ("fatima@example.com", "Fatima", "Bello", "teacher"),
                                         ("emeka@example.com", "Emeka", "Obi", "student")]:
            members[email], _ = User.objects.get_or_create(email=email, defaults=dict(first_name=first, last_name=last, role=role))
            if _:
                members[email].set_password(PASSWORD)
                members[email].save()
        User.objects.get_or_create(email="tunde@example.com", defaults=dict(first_name="Tunde", last_name="Adeyemi", is_blocked=True))

        # ----- catalogue
        book_type, _ = BookType.objects.get_or_create(name="Book", defaults={"description": "Readable or downloadable text titles"})
        BookType.objects.get_or_create(name="Video", defaults={"description": "Video tutorials and recorded talks"})
        cats = {}
        for slug, name, desc, allow in CATEGORIES:
            cats[slug], _ = Category.objects.get_or_create(slug=slug, defaults=dict(name=name, description=desc, allow_download=allow))

        for title, author, publisher, slug, year, pages, perm, copies, desc in BOOKS:
            book, created = Book.objects.get_or_create(
                title=title, author=author,
                defaults=dict(publisher=publisher, category=cats[slug], book_type=book_type, year=year, pages=pages,
                              description=desc, download_permission=perm, created_by=admin))
            if created:
                book.file.save(f"{book.pk}.pdf", ContentFile(make_pdf(title)), save=True)
                for n in range(1, copies + 1):
                    BookCopy.objects.create(book=book, inventory_code=f"LUM-{book.pk:04d}-{n:02d}")

        for title, slug, level, duration in VIDEOS:
            Video.objects.get_or_create(title=title, defaults=dict(
                category=cats[slug], level=level, duration=duration, video_url="https://www.youtube.com/"))

        # ----- three loans (one of them overdue)
        if not BookIssue.objects.exists():
            today = timezone.localdate()
            plan = [("Things Fall Apart", "chidera@example.com", 5, 9), ("Purple Hibiscus", "chidera@example.com", -10, 24),
                    ("Half of a Yellow Sun", "fatima@example.com", 4, 10)]
            for title, email, due_in, ago in plan:
                copy = BookCopy.objects.filter(book__title=title, status=BookCopy.Status.AVAILABLE).first()
                if copy:
                    issue = BookIssue(user=members[email], copy=copy, issued_by=admin, due_date=today + timedelta(days=max(due_in, 1)))
                    issue.save()
                    BookIssue.objects.filter(pk=issue.pk).update(issued_at=timezone.now() - timedelta(days=ago), due_date=today + timedelta(days=due_in))

        self.stdout.write(self.style.SUCCESS(
            f"Done. {Book.objects.count()} books, {BookCopy.objects.count()} copies, {Video.objects.count()} videos.\n"
            f"Log in with chidera@example.com, fatima@example.com, emeka@example.com or admin@lumina.test\n"
            f"(password for all of them: {PASSWORD})   Blocked demo member: tunde@example.com"))
