
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.text import slugify

from catalogue.models import Book, Category, BookType, Statuses


class Command(BaseCommand):
    help = "Import book metadata from the Open Library Search API"

    def add_arguments(self, parser):
        parser.add_argument(
            "--query",
            default="python programming",
            help="Search phrase, e.g. African literature",
        )
        parser.add_argument(
            "--max-results",
            type=int,
            default=20,
        )

    def handle(self, *args, **options):
        query = options["query"].strip()
        limit = max(1, min(options["max_results"], 100))

        if not query:
            raise CommandError("Please provide a search query.")

        params = urllib.parse.urlencode({
            "q": query,
            "limit": limit,
            "fields": (
                "key,title,author_name,publisher,"
                "first_publish_year,number_of_pages_median,"
                "isbn,cover_i,subject"
            ),
        })

        url = f"https://openlibrary.org/search.json?{params}"

        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": (
                    "LuminaELibrary/1.0 "
                    "(contact: despinannebs22@gmail.com)"
                )
            },
        )

        data = None

        # Retry briefly for temporary server errors or rate limits.
        for attempt in range(3):
            try:
                with urllib.request.urlopen(
                    request,
                    timeout=30,
                ) as response:
                    data = json.loads(
                        response.read().decode("utf-8")
                    )
                break

            except urllib.error.HTTPError as exc:
                if exc.code == 429 and attempt < 2:
                    wait_seconds = 2 ** (attempt + 1)
                    self.stdout.write(
                        f"Rate limited. Waiting {wait_seconds} seconds..."
                    )
                    time.sleep(wait_seconds)
                else:
                    raise CommandError(
                        f"Open Library returned HTTP {exc.code}. "
                        "Try again later and check its API usage guidelines."
                    ) from exc

            except Exception as exc:
                raise CommandError(
                    f"Could not fetch Open Library results: {exc}"
                ) from exc

        if data is None:
            raise CommandError(
                "Open Library did not return results after retries."
            )

        # Use an existing category, or create a suitable default.
        category, _ = Category.objects.get_or_create(
            name="General",
            defaults={
                "slug": self.unique_category_slug("General"),
                "description": "General reading",
            },
        )

        book_type, _ = BookType.objects.get_or_create(
            name="E-book",
            defaults={
                "description": "Digital book listing",
            },
        )

        created = 0
        skipped = 0
        errors = 0

        for item in data.get("docs", []):
            title = (item.get("title") or "").strip()[:200]

            if not title:
                skipped += 1
                continue

            authors = item.get("author_name") or ["Unknown"]
            author = ", ".join(authors)[:150]

            isbn_values = item.get("isbn") or []
            isbn = next(
                (
                    value.strip()
                    for value in isbn_values
                    if value and len(value.strip()) <= 20
                ),
                None,
            )

            # Avoid duplicate records.
            if isbn and Book.objects.filter(isbn=isbn).exists():
                skipped += 1
                self.stdout.write(f"Already exists: {title}")
                continue

            if Book.objects.filter(
                title__iexact=title,
                author__iexact=author,
            ).exists():
                skipped += 1
                self.stdout.write(f"Already exists: {title}")
                continue

            publishers = item.get("publisher") or []
            publisher = publishers[0][:150] if publishers else None

            year = item.get("first_publish_year")
            if not isinstance(year, int) or not (1 <= year <= 9999):
                year = None

            pages = item.get("number_of_pages_median")
            if not isinstance(pages, int) or pages < 1:
                pages = None

            description = (
                "Metadata imported from Open Library. "
                "A legally obtained book file must be added before publication."
            )

            try:
                with transaction.atomic():
                    book = Book.objects.create(
                        title=title,
                        author=author,
                        publisher=publisher,
                        category=category,
                        book_type=book_type,
                        year=year,
                        pages=pages,
                        isbn=isbn,
                        description=description,
                        status=Statuses.LIVE,
                    )

                    # Save a cover only when Open Library supplies a cover ID.
                    cover_id = item.get("cover_i")

                    if cover_id:
                        cover_url = (
                            "https://covers.openlibrary.org/b/id/"
                            f"{cover_id}-M.jpg"
                        )

                        cover_request = urllib.request.Request(
                            cover_url,
                            headers={
                                "User-Agent": (
                                    "LuminaELibrary/1.0 "
                                    "(contact: despinannebs22@gmail.com)"
                                )
                            },
                        )

                        try:
                            with urllib.request.urlopen(
                                cover_request,
                                timeout=15,
                            ) as cover_response:
                                image_data = cover_response.read(
                                    2_000_001
                                )

                            if (
                                image_data
                                and len(image_data) <= 2_000_000
                                and image_data.startswith(b"\xff\xd8")
                            ):
                                book.cover.save(
                                    f"openlibrary-{cover_id}.jpg",
                                    ContentFile(image_data),
                                    save=True,
                                )

                        except Exception as cover_error:
                            self.stdout.write(
                                self.style.WARNING(
                                    f"Cover unavailable for '{title}': "
                                    f"{cover_error}"
                                )
                            )

                created += 1
                self.stdout.write(
                    self.style.SUCCESS(f"Imported: {title}")
                )

            except Exception as exc:
                errors += 1
                self.stderr.write(
                    self.style.ERROR(f"Failed to import '{title}': {exc}")
                )

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                f"Finished. Imported: {created}; "
                f"skipped: {skipped}; errors: {errors}."
            )
        )

    @staticmethod
    def unique_category_slug(name):
        base_slug = slugify(name) or "general"
        slug = base_slug
        counter = 1

        from catalogue.models import Category

        while Category.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1

        return slug
