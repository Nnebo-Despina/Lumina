# catalogue/permissions.py
# THE DOWNLOAD RULE (specification: "Admin can set permission either at category
# or individual book to download").
#
#   book.download_permission == "allow"    -> allowed
#   book.download_permission == "deny"     -> never allowed
#   book.download_permission == "inherit"  -> follows category.allow_download
#
# On top of that the person must be logged in and not blocked, and the book must be
# published and actually have a file.

from .models import DownloadStatus, Statuses


def book_download_allowed(book):
    """Does the ADMIN's setting allow this book to be downloaded? (ignores who is asking)"""
    if book.download_permission == DownloadStatus.ALLOW:
        return True
    if book.download_permission == DownloadStatus.DENY:
        return False
    return book.category.allow_download          # "inherit"


def can_download(user, book):
    """May THIS user download THIS book right now?"""
    return (
        user.is_authenticated
        and not user.is_blocked
        and book.status == Statuses.LIVE
        and bool(book.file)
        and book_download_allowed(book)
    )
