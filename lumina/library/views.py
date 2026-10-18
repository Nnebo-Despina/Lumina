# library/views.py
# The MEMBER experience: dashboard, online reader, secure PDF / download, watching videos.
# Every view needs a logged-in, unblocked member (@member_required).

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.text import slugify
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.views.decorators.http import require_POST

from accounts.decorators import member_required
from catalogue.models import Book, Statuses, Video
from catalogue.permissions import can_download
from loans.models import BookIssue

from .models import DownloadLog, ReadingProgress, VideoView

LIVE = Statuses.LIVE


def _readable_book(pk):
    """A published book that actually has a file."""
    book = get_object_or_404(Book.objects.select_related("category", "book_type"), pk=pk, status=LIVE)
    if not book.file:
        raise Http404("This book has no file.")
    return book


# ------------------------------------------------------------------ dashboard
@member_required
def account(request):
    user = request.user
    loans = BookIssue.objects.filter(user=user, status=BookIssue.Status.ISSUED).select_related("copy__book")
    return render(request, "library/account.html", {
        "books_read": user.reading_progress.count(),
        "videos_watched": user.video_views.count(),
        "downloads": user.download_logs.count(),
        "borrowed_now": loans.count(),
        "continue_reading": user.reading_progress.select_related("book").order_by("-updated_at")[:5],
        "current_loans": loans.order_by("due_date"),
    })


# ------------------------------------------------------------------ online reader
@member_required
def read(request, pk):
    """The reader page: the PDF is shown in a frame and the last page is remembered."""
    book = _readable_book(pk)
    progress, _ = ReadingProgress.objects.get_or_create(user=request.user, book=book)
    return render(request, "library/read.html", {
        "book": book, "progress": progress, "can_download": can_download(request.user, book),
    })


@member_required
@require_POST
def save_progress(request, pk):
    """'Save my place' button: remembers the page number."""
    book = _readable_book(pk)
    try:
        page = max(1, int(request.POST.get("page", 1)))
    except ValueError:
        page = 1
    ReadingProgress.objects.update_or_create(user=request.user, book=book, defaults={"last_page": page})
    messages.success(request, f"Your place was saved at page {page}.")
    return redirect("library:read", pk=book.pk)


@member_required
@xframe_options_sameorigin          # lets OUR reader page show this PDF in a frame (default is DENY)
def book_file(request, pk):
    """The PDF itself, only for logged-in members. (Book files are NOT in the public /media/ folder.)"""
    book = _readable_book(pk)
    return FileResponse(book.file.open("rb"), content_type="application/pdf", as_attachment=False,
                        filename=f"{slugify(book.title) or 'book'}.pdf")


@member_required
def download(request, pk):
    """Download a book. Allowed only by the download rule (see catalogue/permissions.py)."""
    book = _readable_book(pk)
    if not can_download(request.user, book):
        raise PermissionDenied                                    # 403: the admin has not allowed it
    DownloadLog.objects.create(user=request.user, book=book)
    return FileResponse(book.file.open("rb"), content_type="application/pdf", as_attachment=True,
                        filename=f"{slugify(book.title) or 'book'}.pdf")


# ------------------------------------------------------------------ videos
@member_required
def watch(request, pk):
    """Opens a video (and records that this member watched it)."""
    video = get_object_or_404(Video, pk=pk, status=LIVE)
    if not (video.video_file or video.video_url):
        raise Http404("This video has no source.")
    VideoView.objects.get_or_create(user=request.user, video=video)
    if video.video_file:
        return FileResponse(video.video_file.open("rb"))          # content type guessed from the file name
    return redirect(video.video_url)                              # external link (for example YouTube)
