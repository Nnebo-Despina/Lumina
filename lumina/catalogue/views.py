# catalogue/views.py
# PUBLIC side of the catalogue: home, about, browse / search, book details, videos.
# (The administration side is in manage_views.py.)

from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, render
from django.views.generic import ListView, TemplateView

from accounts.decorators import MemberRequiredMixin
from library.models import ReadingProgress

from .models import Book, BookCopy, BookType, Category, Statuses, Video
from .permissions import can_download

User = get_user_model()
LIVE = Statuses.LIVE


def live_books():
    """Published books only (drafts are never shown to the public)."""
    return Book.objects.filter(status=LIVE).select_related("category", "book_type")


def categories_with_counts():
    """Every category with the number of published books it holds."""
    return Category.objects.annotate(
        live_books=Count("book", filter=Q(book__status=LIVE), distinct=True)
    ).order_by("name")[:6]


# ------------------------------------------------------------------ home
class HomeView(TemplateView):
    template_name = "catalogue/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # "Popular now": the 3 books readers open and download most (newest first on a tie)
        popular = list(
            live_books()
            .annotate(popularity=Count("reading_progress", distinct=True) + Count("download_logs", distinct=True))
            .order_by("-popularity", "-created_at")[:3]
        )
        context.update(
            popular_books=popular,
            spotlight=popular[0] if popular else None,
            categories=categories_with_counts(),
            item_count=live_books().count() + Video.objects.filter(status=LIVE).count(),
            category_count=Category.objects.count(),
            member_count=User.objects.filter(is_active=True, is_staff=False).count(),
        )
        return context


class AboutView(TemplateView):
    template_name = "catalogue/about.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = Category.objects.order_by("name")
        return context


# ------------------------------------------------------------------ browse + search
class BookListView(ListView):
    """Searchable, filterable catalogue.  GET: q (words), by (all/title/author/publisher),
    category (slug), type (book type name), page."""

    template_name = "catalogue/books.html"
    context_object_name = "books"
    paginate_by = 12

    SEARCH_FIELDS = {"title": ["title"], "author": ["author"], "publisher": ["publisher"]}

    def get_queryset(self):
        params = self.request.GET
        books = live_books().order_by("title")

        words = (params.get("q") or params.get("search") or "").strip()
        if words:
            fields = self.SEARCH_FIELDS.get(params.get("by"), ["title", "author", "publisher"])
            condition = Q()
            for field in fields:
                condition |= Q(**{f"{field}__icontains": words})
            books = books.filter(condition)

        if params.get("category"):
            books = books.filter(category__slug=params["category"])
        if params.get("type"):
            books = books.filter(book_type__name=params["type"])
        return books

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        params = self.request.GET
        keep = params.copy()
        keep.pop("page", None)                       # pagination links keep the other filters
        context.update(
            categories=Category.objects.order_by("name"),
            book_types=BookType.objects.order_by("name"),
            q=(params.get("q") or params.get("search") or "").strip(),
            by=params.get("by", "all"),
            current_category=params.get("category", ""),
            current_type=params.get("type", ""),
            querystring=keep.urlencode(),
        )
        return context


# ------------------------------------------------------------------ book details
def book_detail(request, pk):
    """Guests see the details and a login prompt; members also get Read / Download."""
    book = get_object_or_404(live_books(), pk=pk)

    # Physical stock (lost / retired copies do not count)
    holdings = book.copies.exclude(status__in=[BookCopy.Status.LOST, BookCopy.Status.RETIRED])
    context = {
        "book": book,
        "copies_total": holdings.count(),
        "copies_available": holdings.filter(status=BookCopy.Status.AVAILABLE).count(),
    }

    user = request.user
    if user.is_authenticated and not user.is_blocked:
        context["can_download"] = can_download(user, book)
        context["progress"] = ReadingProgress.objects.filter(user=user, book=book).first()
        return render(request, "catalogue/member_book_detail.html", context)
    return render(request, "catalogue/book_detail.html", context)


# ------------------------------------------------------------------ videos (members only)
class VideoListView(MemberRequiredMixin, ListView):
    template_name = "catalogue/videos.html"
    context_object_name = "videos"

    def get_queryset(self):
        videos = Video.objects.filter(status=LIVE).select_related("category").order_by("category__name", "title")
        if self.request.GET.get("category"):
            videos = videos.filter(category__slug=self.request.GET["category"])
        return videos

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = Category.objects.order_by("name")
        context["current_category"] = self.request.GET.get("category", "")
        return context
