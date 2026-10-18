# catalogue/manage_views.py
# ADMINISTRATION side of the catalogue (/manage/...): dashboard, categories, book types,
# books, videos, download permissions and reports.
# Every view is protected with @admin_required (see accounts/decorators.py).

import csv

from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, ProtectedError, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.decorators import admin_required
from accounts.models import User
from loans.models import BookIssue

from .forms import BookAdminForm, BookTypeAdminForm, CategoryAdminForm, VideoAdminForm
from .models import Book, BookType, Category, DownloadStatus, Statuses, Video

LIVE = Statuses.LIVE


def _first_error(form):
    """One readable line from a form's errors (used for messages)."""
    for field, errors in form.errors.items():
        return f"{errors[0]}" if field == "__all__" else f"{field.replace('_', ' ').title()}: {errors[0]}"
    return "Please check the form."


# ======================================================================= dashboard
@admin_required
def manage_dashboard(request):
    today = timezone.localdate()
    now = timezone.now()
    this_month = {"created_at__year": now.year, "created_at__month": now.month}
    members = User.objects.filter(is_staff=False)

    # Titles per category (bars): the biggest category gets the gold bar
    cats = list(Category.objects.annotate(total=Count("book", distinct=True)).order_by("name"))
    biggest = max([c.total for c in cats], default=0) or 1
    bars = [{"name": c.name, "short": c.name.split(" ")[0], "total": c.total,
             "height": max(12, round(c.total / biggest * 100)), "peak": c.total == biggest and c.total > 0}
            for c in cats]

    context = {
        "book_total": Book.objects.count(),
        "video_total": Video.objects.count(),
        "category_total": len(cats),
        "member_total": members.count(),
        "books_month": Book.objects.filter(**this_month).count(),
        "videos_month": Video.objects.filter(**this_month).count(),
        "members_month": members.filter(date_joined__year=now.year, date_joined__month=now.month).count(),
        "on_loan": BookIssue.objects.filter(status=BookIssue.Status.ISSUED).count(),
        "overdue": BookIssue.objects.filter(status=BookIssue.Status.ISSUED, due_date__lt=today).count(),
        "returned_month": BookIssue.objects.filter(
            status=BookIssue.Status.RETURNED, returned_at__year=now.year, returned_at__month=now.month).count(),
        "bars": bars[:6],
        "newest_members": members.order_by("-date_joined")[:3],
        "recent_books": Book.objects.select_related("category", "book_type").order_by("-created_at")[:3],
    }
    return render(request, "manage/dashboard.html", context)


# ======================================================================= categories
@admin_required
def manage_categories(request):
    """List + 'add a category' form (the edit pop-ups post to manage_category_edit)."""
    form = CategoryAdminForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, f"Category '{form.instance.name}' was added.")
        return redirect("catalogue:manage_categories")

    categories = Category.objects.annotate(
        book_total=Count("book", distinct=True), video_total=Count("videos", distinct=True)
    ).order_by("name")
    return render(request, "manage/categories.html", {"form": form, "categories": categories})


@admin_required
@require_POST
def manage_category_edit(request, pk):
    category = get_object_or_404(Category, pk=pk)
    form = CategoryAdminForm(request.POST, instance=category)
    if form.is_valid():
        form.save()
        messages.success(request, f"Category '{category.name}' was updated.")
    else:
        messages.error(request, _first_error(form))
    return redirect("catalogue:manage_categories")


@admin_required
@require_POST
def manage_category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk)
    try:
        category.delete()
        messages.success(request, f"Category '{category.name}' was deleted.")
    except ProtectedError:
        messages.error(request, f"'{category.name}' still has books or videos. Move or delete them first.")
    return redirect("catalogue:manage_categories")


# ======================================================================= book types
@admin_required
def manage_book_types(request):
    form = BookTypeAdminForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, f"Book type '{form.instance.name}' was added.")
        return redirect("catalogue:manage_book_types")
    types = BookType.objects.annotate(book_total=Count("book", distinct=True)).order_by("name")
    return render(request, "manage/book_types.html", {"form": form, "book_types": types})


@admin_required
@require_POST
def manage_book_type_delete(request, pk):
    book_type = get_object_or_404(BookType, pk=pk)
    try:
        book_type.delete()
        messages.success(request, f"Book type '{book_type.name}' was deleted.")
    except ProtectedError:
        messages.error(request, f"'{book_type.name}' is used by books and cannot be deleted.")
    return redirect("catalogue:manage_book_types")


# ======================================================================= books
@admin_required
def manage_books(request):
    params = request.GET
    books = Book.objects.select_related("category", "book_type").order_by("-created_at")
    q = (params.get("q") or "").strip()
    if q:
        books = books.filter(Q(title__icontains=q) | Q(author__icontains=q) | Q(publisher__icontains=q) | Q(isbn__icontains=q))
    if params.get("category"):
        books = books.filter(category_id=params["category"])
    if params.get("type"):
        books = books.filter(book_type_id=params["type"])

    page = Paginator(books, 25).get_page(params.get("page"))
    keep = params.copy()
    keep.pop("page", None)
    return render(request, "manage/books.html", {
        "page_obj": page, "books": page.object_list, "q": q,
        "categories": Category.objects.order_by("name"), "book_types": BookType.objects.order_by("name"),
        "current_category": params.get("category", ""), "current_type": params.get("type", ""),
        "querystring": keep.urlencode(),
    })


def _book_form(request, book=None):
    """Shared by 'add a book' and 'edit a book'."""
    form = BookAdminForm(request.POST or None, request.FILES or None, instance=book)
    if request.method == "POST" and form.is_valid():
        obj = form.save(commit=False)
        if book is None:
            obj.created_by = request.user                 # remember which admin added it
        obj.save()
        added = form.save_copies(obj)
        note = f" {added} physical cop{'y' if added == 1 else 'ies'} added." if added else ""
        messages.success(request, f"'{obj.title}' was saved.{note}")
        return redirect("catalogue:manage_books")
    return render(request, "manage/book_form.html", {"form": form, "book": book})


@admin_required
def manage_book_add(request):
    return _book_form(request)


@admin_required
def manage_book_edit(request, pk):
    return _book_form(request, get_object_or_404(Book, pk=pk))


@admin_required
@require_POST
def manage_book_delete(request, pk):
    book = get_object_or_404(Book, pk=pk)
    try:
        with transaction.atomic():
            book.copies.filter(issues__isnull=True).delete()   # copies that were never lent
            book.delete()
        messages.success(request, f"'{book.title}' was deleted.")
    except ProtectedError:
        messages.error(request, f"'{book.title}' has copies with a loan history and cannot be deleted. Set it to Draft instead.")
    return redirect("catalogue:manage_books")


# ======================================================================= videos
@admin_required
def manage_videos(request):
    q = (request.GET.get("q") or "").strip()
    videos = Video.objects.select_related("category").order_by("-created_at")
    if q:
        videos = videos.filter(Q(title__icontains=q) | Q(category__name__icontains=q))
    return render(request, "manage/videos.html", {"videos": videos, "q": q})


def _video_form(request, video=None):
    form = VideoAdminForm(request.POST or None, request.FILES or None, instance=video)
    if request.method == "POST" and form.is_valid():
        obj = form.save()
        messages.success(request, f"'{obj.title}' was saved.")
        return redirect("catalogue:manage_videos")
    return render(request, "manage/video_form.html", {"form": form, "video": video})


@admin_required
def manage_video_add(request):
    return _video_form(request)


@admin_required
def manage_video_edit(request, pk):
    return _video_form(request, get_object_or_404(Video, pk=pk))


@admin_required
@require_POST
def manage_video_delete(request, pk):
    video = get_object_or_404(Video, pk=pk)
    video.delete()
    messages.success(request, f"'{video.title}' was deleted.")
    return redirect("catalogue:manage_videos")


# ======================================================================= download permissions
@admin_required
def manage_downloads(request):
    """Category switches + per-book overrides. A book's own setting beats its category."""
    categories = Category.objects.annotate(book_total=Count("book", distinct=True)).order_by("name")
    books = Book.objects.select_related("category").order_by("title")

    if request.method == "POST":
        ticked = {int(v) for v in request.POST.getlist("categories") if v.isdigit()}
        for category in categories:
            allowed = category.pk in ticked
            if category.allow_download != allowed:
                Category.objects.filter(pk=category.pk).update(allow_download=allowed)

        valid = {choice for choice, _ in DownloadStatus.choices}
        for book in books:
            value = request.POST.get(f"book_{book.pk}")
            if value in valid and value != book.download_permission:
                Book.objects.filter(pk=book.pk).update(download_permission=value)

        messages.success(request, "Download permissions were saved.")
        return redirect("catalogue:manage_downloads")

    return render(request, "manage/downloads.html", {
        "categories": categories, "books": books, "choices": DownloadStatus.choices,
    })


# ======================================================================= reports
def _report(params):
    """Rows 'books available under each category' (+ totals) for the given filters."""
    books = Book.objects.filter(status=LIVE)
    videos = Video.objects.filter(status=LIVE)
    if params.get("from"):
        books, videos = books.filter(created_at__date__gte=params["from"]), videos.filter(created_at__date__gte=params["from"])
    if params.get("to"):
        books, videos = books.filter(created_at__date__lte=params["to"]), videos.filter(created_at__date__lte=params["to"])

    categories = Category.objects.order_by("name")
    if params.get("category"):
        categories = categories.filter(pk=params["category"])

    downloadable = Q(download_permission=DownloadStatus.ALLOW) | Q(
        download_permission=DownloadStatus.INHERIT, category__allow_download=True)
    rows = []
    for category in categories:
        in_cat = books.filter(category=category)
        n_books, n_videos, n_dl = in_cat.count(), videos.filter(category=category).count(), in_cat.filter(downloadable).count()
        rows.append({"category": category.name, "books": n_books, "videos": n_videos,
                     "downloadable": n_dl, "total": n_books + n_videos})
    totals = {k: sum(r[k] for r in rows) for k in ("books", "videos", "downloadable", "total")}
    return rows, totals


@admin_required
def manage_reports(request):
    rows, totals = _report(request.GET)

    if request.GET.get("export") == "csv":                  # the "Export CSV" button
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="lumina-report.csv"'
        writer = csv.writer(response)
        writer.writerow(["Category", "Books", "Videos", "Downloadable", "Total"])
        for r in rows:
            writer.writerow([r["category"], r["books"], r["videos"], r["downloadable"], r["total"]])
        writer.writerow(["Total", totals["books"], totals["videos"], totals["downloadable"], totals["total"]])
        return response

    keep = request.GET.copy()
    keep.pop("export", None)
    return render(request, "manage/reports.html", {
        "rows": rows, "totals": totals, "categories": Category.objects.order_by("name"),
        "current_category": request.GET.get("category", ""), "date_from": request.GET.get("from", ""),
        "date_to": request.GET.get("to", ""), "today": timezone.localdate(),
        "csv_query": keep.urlencode(),
    })
